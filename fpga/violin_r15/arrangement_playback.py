"""Compile a score to existing UART commands; never synthesize audio on the PC."""
from dataclasses import dataclass
import math
import time

from arrangement_model import DISCRETE, INSTRUMENTS, PARAMETERS, PPQ
from melody_player import command_frame, note_frame
from drum_patterns import hit_frame
from guitar_effects import effect_frames
from master_space_effects import space_effect_frames
from ensemble_protocol import targeted_note


TIMBRES = {'guitar': 0, 'piano': 1, 'bass': 2, 'violin': 3}
BUS_IDS = {'guitar': 0, 'piano': 1, 'drums': 2, 'violin': 3, 'bass': 4}


@dataclass(frozen=True)
class ScoreNote:
    start: int
    end: int
    instrument: str
    pitch: int
    velocity: int
    id: str


@dataclass(frozen=True)
class Event:
    at: float
    priority: int
    kind: str
    data: bytes = b''
    note: ScoreNote | None = None
    label: str = ''


@dataclass(frozen=True)
class Plan:
    events: tuple
    duration: float
    start_tick: int
    end_tick: int
    bpm: int
    hardware: bool
    warnings: tuple
    ensemble: bool = False


def score_notes(project):
    return sorted((ScoreNote(clip.start + note.start, clip.start + note.start + note.duration,
                             track.instrument, note.pitch,
                             max(1, min(127, round(note.velocity * track.level / 100))), note.id)
                   for track in project.active_tracks() for clip in track.clips for note in clip.notes),
                  key=lambda note: (note.start, note.id))


def check_hardware(notes, ensemble=False):
    active = {}
    boundaries = sorted([(note.start, 1, note.id, note) for note in notes] +
                        [(note.end, 0, note.id, note) for note in notes])
    limits = {'piano': 16, 'guitar': 32, 'bass': 8, 'violin': 1}
    for _, on, identifier, note in boundaries:
        if note.instrument == 'drums':
            continue
        if not on:
            active.pop(identifier, None)
            continue
        note_frame(TIMBRES[note.instrument], note.pitch, note.velocity, True)
        if not ensemble and any(previous.instrument != note.instrument for previous in active.values()):
            raise ValueError('当前v7主音色互斥：不同主乐器音符重叠。请分段、Mute或Solo；鼓组可叠加。')
        same_instrument = [previous for previous in active.values() if previous.instrument == note.instrument]
        if note.instrument in ('piano', 'violin') and any(previous.pitch == note.pitch for previous in same_instrument):
            raise ValueError('相同音高重叠：当前协议没有音符ID，松音会影响另一轨同音，请错开。')
        active[identifier] = note
        if len(same_instrument) + 1 > limits[note.instrument]:
            raise ValueError(f'{INSTRUMENTS[note.instrument]}超过当前声部上限 {limits[note.instrument]}')


def parameter_frames(previous, current, ensemble=False):
    frames = []
    for name, bus in BUS_IDS.items():
        if bus == 4 and not ensemble:
            continue
        key = 'bus.' + name
        if previous is None or previous[key] != current[key]:
            frames.append(command_frame(0x70, bus, current[key], 0))
    if previous is None or any(current[key] != previous[key] for key in current if key.startswith('space.')):
        frames.extend(space_effect_frames(**{key.split('.')[1]: value for key, value in current.items()
                                              if key.startswith('space.')}))
    if previous is None or any(current[key] != previous[key] for key in current if key.startswith('guitar.')):
        frames.extend(effect_frames(**{key.split('.')[1]: value for key, value in current.items()
                                       if key.startswith('guitar.')}))
    return b''.join(frames)


def compile_plan(project, hardware=False, start_tick=0, end_tick=None, ensemble=False):
    project.validate()
    end_tick = project.length if end_tick is None else end_tick
    if type(start_tick) is not int or type(end_tick) is not int or not 0 <= start_tick < end_tick <= project.length:
        raise ValueError('播放区间无效')
    seconds_per_tick = 60 / project.bpm / PPQ
    notes = [note for note in score_notes(project) if note.start < end_tick and note.end > start_tick]
    if hardware:
        check_hardware(notes, ensemble)
    events = []
    melodic = None
    if hardware:
        events.append(Event(0, -3, 'setup', command_frame(0x52, 0, 0, 0), label='停止板端鼓步进器'))
        events.append(Event(0, -2, 'setup', command_frame(0x03, 1, 0, 0), label='复音模式'))
        events.append(Event(0, -2, 'setup', command_frame(0x23, 0, 0, 0) + command_frame(0x06, 0, 0, 0),
                            label='恢复SMS钢琴并关闭踏板'))
        if ensemble:
            events.append(Event(0, -1, 'ensemble', command_frame(0x0e, 1, 0, 0), label='v8独立多乐器'))
    for note in notes:
        if note.start < start_tick and note.instrument not in ('piano', 'violin'):
            continue
        at = max(0, note.start - start_tick) * seconds_per_tick
        ending = (min(note.end, end_tick) - start_tick) * seconds_per_tick
        data = b''
        release = b''
        if hardware:
            if note.instrument == 'drums':
                data = hit_frame(note.pitch, note.velocity)
            else:
                if not ensemble and melodic != note.instrument:
                    melodic = note.instrument
                    events.append(Event(at, 1, 'timbre', command_frame(4, TIMBRES[melodic], 0, 0), label=melodic))
                if ensemble:
                    data = targeted_note(note.instrument, note.pitch, note.velocity, True)
                    release = targeted_note(note.instrument, note.pitch, 1, False)
                else:
                    data = note_frame(TIMBRES[melodic], note.pitch, note.velocity, True)
                    release = note_frame(TIMBRES[melodic], note.pitch, 1, False) or b''
        events.append(Event(at, 3, 'on', data, note))
        events.append(Event(ending, 0, 'off', release, note))
    sample_ticks = {start_tick}
    for lane in project.automation:
        sample_ticks.update(point.tick for point in lane.points if start_tick <= point.tick < end_tick)
        if lane.interpolation == 'linear' and lane.target not in DISCRETE:
            step = max(1, round(0.05 / seconds_per_tick))
            sample_ticks.update(range(start_tick, end_tick, step))
    previous = None
    for tick in sorted(sample_ticks):
        current = dict(project.parameters)
        for lane in project.automation:
            current[lane.target] = lane.value_at(tick, current[lane.target])
        if current != previous:
            data = parameter_frames(previous, current, ensemble) if hardware else b''
            events.append(Event((tick - start_tick) * seconds_per_tick, 2, 'effects', data,
                                label='效果自动化 / 总线设置'))
        previous = current
    events.sort(key=lambda event: (event.at, event.priority))
    if len(events) > 100000:
        raise ValueError('播放事件超过100000个，请缩短工程或简化自动化')
    if hardware:
        wire = []
        pending = 0
        first = 0
        for event in events:
            while first < len(wire) and wire[first][0] <= event.at - 0.1:
                pending -= wire[first][1]
                first += 1
            pending += len(event.data)
            wire.append((event.at, len(event.data)))
            if pending > 864:
                raise ValueError('100ms内串口命令过密，请降低自动化密度或同时触发的音符数')
    warnings = ('PC定时发送，115200串口单向无ACK；不是FPGA采样级定时。',
                '吉他/Bass/鼓的矩形长度用于编排，不是精确截音；按自然尾音结束，切主音色会清旧声。',
                '轨道音量按力度缩放，效果和总线音量是共享的，不是独立插件插槽。')
    return Plan(tuple(events), (end_tick - start_tick) * seconds_per_tick,
                start_tick, end_tick, project.bpm, hardware, warnings, ensemble)


class ArrangementPlayer:
    def __init__(self, send, schedule, cancel, changed=None, clock=time.monotonic):
        self.send, self.schedule, self.cancel = send, schedule, cancel
        self.changed = changed or (lambda player: None)
        self.clock = clock
        self.state = 'stopped'
        self.message = '就绪：离线编排不发送串口'
        self.plan = None
        self.position = 0.0
        self.active = {}
        self.last_event = None
        self._job = None
        self._index = 0
        self._generation = 0
        self._origin = 0.0
        self._timbre = None
        self.loop = False

    @property
    def tick(self):
        if self.plan is None:
            return 0
        return self.plan.start_tick + round(self.position * self.plan.bpm * PPQ / 60)

    def _send(self, data):
        if not data or not self.plan.hardware:
            return True
        try:
            return bool(self.send(data))
        except Exception:
            return False

    def play(self, plan, loop=False):
        if not isinstance(plan, Plan):
            raise ValueError('无效播放计划')
        if self.state != 'stopped' and not self.stop():
            return False
        self.plan, self.loop = plan, bool(loop)
        self.position = 0.0
        self.active.clear()
        self._index = 0
        self._timbre = None
        self._origin = self.clock()
        self._generation += 1
        self.state = 'playing'
        self.message = '实机发送中（无ACK）' if plan.hardware else '离线走带（静音、不发送）'
        self._tick(self._generation)
        return self.state == 'playing'

    def stop(self, message='已停止；鼓与空间效果可能保留自然尾音'):
        self._generation += 1
        if self._job is not None:
            self.cancel(self._job)
            self._job = None
        self.state = 'stopped'
        successful = True
        if self.plan and self.plan.hardware:
            for event in tuple(self.active.values()):
                if event.note.instrument in ('piano', 'violin'):
                    release = targeted_note(event.note.instrument, event.note.pitch, 1, False) if self.plan.ensemble else note_frame(TIMBRES[event.note.instrument], event.note.pitch, 1, False)
                    successful = self._send(release) and successful
            if self.plan.ensemble:
                successful = self._send(command_frame(0x0e, 0, 0, 0)) and successful
            elif self._timbre is not None:
                successful = self._send(command_frame(4, TIMBRES[self._timbre], 0, 0)) and successful
        self._timbre = None
        self.active.clear()
        self.message = message if successful else '已取消未来事件，但松音发送失败；板端状态未知'
        self.changed(self)
        return successful

    def _tick(self, generation):
        if generation != self._generation or self.state != 'playing':
            return
        self._job = None
        self.position = min(self.plan.duration, max(0, self.clock() - self._origin))
        while self._index < len(self.plan.events):
            event = self.plan.events[self._index]
            if event.at > self.position + 1e-7:
                break
            if self.position - event.at > 0.15:
                self.stop('调度迟到超过150ms，已停止，避免集中补发音符')
                return
            self._index += 1
            if not self._send(event.data):
                self.stop('串口发送失败，已取消未来事件')
                return
            self.last_event = event
            if event.kind == 'timbre':
                self._timbre = event.label
            if event.kind == 'on':
                self.active[event.note.id] = event
            elif event.kind == 'off':
                self.active.pop(event.note.id, None)
            self.position = min(self.plan.duration, max(0, self.clock() - self._origin))
        if self.position >= self.plan.duration:
            if self.loop:
                plan = self.plan
                if self.stop('循环边界清声'):
                    self.play(plan, loop=True)
                return
            self.stop('播放完成；自然尾音可能继续')
            return
        self.changed(self)
        next_at = self.plan.events[self._index].at if self._index < len(self.plan.events) else self.plan.duration
        delay = max(1, min(25, math.ceil((next_at - self.position) * 1000)))
        self._job = self.schedule(delay, lambda: self._tick(generation))
