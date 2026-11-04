import math
import time
from dataclasses import dataclass

from mario_score import MEASURES, TICKS_PER_BEAT, bar_order


GUITAR_OPEN_MIDI = (64, 59, 55, 50, 45, 40)


def command_frame(opcode, first, second, third):
    values = (0xa5, opcode, first, second, third)
    if any(type(value) is not int or not 0 <= value <= 255 for value in values):
        raise ValueError('控制帧字节必须为0～255的整数')
    checksum = 0
    for value in values:
        checksum ^= value
    return bytes((*values, checksum))


def note_frame(timbre, pitch, velocity, on):
    if type(pitch) is not int or type(velocity) is not int or not 1 <= velocity <= 127:
        raise ValueError('音高必须为整数，力度必须为1～127')
    if type(timbre) is not int or timbre not in (0, 1, 2, 3) or type(on) is not bool:
        raise ValueError('不支持的音符命令格式')
    if timbre == 1:
        if not 21 <= pitch <= 108:
            raise ValueError('钢琴音域为A0～C8，请调整移调')
        return command_frame(0x05, pitch, velocity, int(on))
    if timbre == 3:
        if not 55 <= pitch <= 100:
            raise ValueError('小提琴音域为G3～E7，请调整移调')
        return command_frame(0x08, pitch, velocity, int(on))
    candidates = []
    for string_number, open_pitch in enumerate(GUITAR_OPEN_MIDI, 1):
        if timbre == 2 and string_number < 3:
            continue
        fret = pitch - (open_pitch - (12 if timbre == 2 else 0))
        if 0 <= fret <= 20:
            candidates.append((fret, string_number))
    if not candidates:
        name = '吉他' if timbre == 0 else 'Bass（本曲建议移调−24半音）'
        raise ValueError(f'MIDI {pitch}超出{name}弦品音域，请调整移调')
    fret, string_number = min(candidates)
    return command_frame(0x02, string_number, fret, velocity) if on else None


@dataclass(frozen=True)
class TimedEvent:
    at: float
    bar: int
    token: str
    pitch: int | None
    on: bool | None
    frame: bytes | None
    release: bytes | None = None


@dataclass(frozen=True)
class PlaybackPlan:
    events: tuple
    duration: float
    bars: tuple
    timbre: int


def make_plan(timbre, bpm=100, velocity=100, transpose=0, gate=0.82, start_bar=1, score_repeat=True):
    if type(bpm) is not int or not 40 <= bpm <= 240:
        raise ValueError('速度必须为40～240 BPM')
    if type(transpose) is not int or not -36 <= transpose <= 24:
        raise ValueError('移调必须为−36～24半音')
    if not isinstance(gate, (int, float)) or isinstance(gate, bool) or not 0.1 <= gate <= 1:
        raise ValueError('音符门限必须为10%～100%')
    order = bar_order(start_bar, score_repeat)
    seconds_per_tick = 60 / (bpm * TICKS_PER_BEAT)
    position = 0
    events = []
    for bar in order:
        for note in MEASURES[bar - 1]:
            pitch = note.pitch + transpose if note.pitch is not None else None
            if pitch is None:
                events.append(TimedEvent(position * seconds_per_tick, bar, '休止', None, None, None))
            else:
                attack = note_frame(timbre, pitch, velocity, True)
                release = note_frame(timbre, pitch, 1, False)
                events.append(TimedEvent(position * seconds_per_tick, bar, note.token, pitch, True, attack, release))
                events.append(TimedEvent((position + note.ticks * gate) * seconds_per_tick,
                                         bar, note.token, pitch, False, release))
            position += note.ticks
    events.sort(key=lambda event: (event.at, 0 if event.on is False else 1))
    return PlaybackPlan(tuple(events), position * seconds_per_tick, order, timbre)


class CommandPlayer:
    def __init__(self, send, schedule, cancel, changed=None, clock=time.monotonic):
        self.send = send
        self.schedule = schedule
        self.cancel = cancel
        self.changed = changed or (lambda player: None)
        self.clock = clock
        self.state = 'stopped'
        self.message = '未播放'
        self.position = 0.0
        self.plan = None
        self.event = None
        self._job = None
        self._index = 0
        self._origin = 0.0
        self._held = None
        self._resume_note = None

    def _cancel(self):
        if self._job is not None:
            self.cancel(self._job)
            self._job = None

    def _send(self, data):
        if data is None:
            return True
        try:
            return bool(self.send(data))
        except Exception:
            return False

    def _release(self):
        held, self._held = self._held, None
        return held is None or self._send(held.release)

    def play(self, plan):
        if not isinstance(plan, PlaybackPlan):
            raise ValueError('无效的播放计划')
        if self.state != 'stopped' and not self.stop():
            return False
        self.plan = plan
        self.position = 0.0
        self._index = 0
        self.event = None
        self._held = self._resume_note = None
        self._origin = self.clock()
        self.state = 'playing'
        self.message = '播放中'
        self._tick()
        return self.state == 'playing'

    def stop(self, message='已停止'):
        self._cancel()
        self.state = 'stopped'
        self._resume_note = None
        released = self._release()
        self.message = message if released else '停止，松音发送失败；板端可能仍有尾音'
        self.changed(self)
        return released

    def pause(self):
        if self.state != 'playing':
            return
        self.position = min(self.plan.duration, self.clock() - self._origin)
        self._cancel()
        self.state = 'paused'
        release_time = next((event.at for event in self.plan.events[self._index:]
                             if event.on is False and self._held and event.pitch == self._held.pitch), None)
        self._resume_note = self._held if self._held and self._held.release is not None and release_time is not None and self.position < release_time else None
        if not self._release():
            self.stop('松音失败，停止播放')
            return
        self.message = '已暂停'
        self.changed(self)

    def resume(self):
        if self.state != 'paused':
            return False
        if self._resume_note is not None:
            if not self._send(self._resume_note.frame):
                self.stop('恢复音符发送失败')
                return False
            self._held = self._resume_note
            self._resume_note = None
        self._origin = self.clock() - self.position
        self.state = 'playing'
        self.message = '播放中'
        self._tick()
        return self.state == 'playing'

    def _tick(self):
        self._job = None
        if self.state != 'playing':
            return
        self.position = min(self.plan.duration, self.clock() - self._origin)
        while self._index < len(self.plan.events):
            event = self.plan.events[self._index]
            if event.at > self.position + 0.000001:
                break
            if self.position - event.at > 0.2:
                self.stop('调度延迟过大，已停止，避免集中补发音符')
                return
            self._index += 1
            if not self._send(event.frame):
                self.stop('音符发送失败，已停止')
                return
            self.event = event
            if event.on is True:
                self._held = event
            elif event.on is False and self._held and self._held.pitch == event.pitch:
                self._held = None
        if self.position >= self.plan.duration and self._index == len(self.plan.events):
            self.stop('播放完成')
            return
        self.changed(self)
        next_time = self.plan.events[self._index].at if self._index < len(self.plan.events) else self.plan.duration
        delay = max(1, min(50, math.ceil((next_time - self.position) * 1000)))
        self._job = self.schedule(delay, self._tick)
