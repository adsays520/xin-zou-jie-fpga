"""Existing arrangement scheduler plus bounded live guitar/drum hit writes."""
from collections import deque
from copy import deepcopy
from dataclasses import replace
import threading
import time

from arrangement_playback import compile_plan
from ensemble_protocol import targeted_note
from drum_patterns import hit_frame
from guitar_envelope import envelope_preparation


LEAD_IN = 3.0


def game_plan(project, instrument, hardware=False, performance=False):
    if performance and instrument not in ('guitar', 'drums'):
        raise ValueError('命中发声首版支持吉他和鼓；钢琴、小提琴请用跟拍练习')
    accompaniment = deepcopy(project)
    if performance:
        for track in accompaniment.tracks:
            if track.instrument == instrument:
                track.muted = True
    plan = compile_plan(accompaniment, hardware=hardware, ensemble=True)
    events = tuple(replace(event, at=event.at+LEAD_IN) if event.kind in ('on', 'off') or event.at > 0 else event
                   for event in plan.events)
    preparation = plan.preparation
    if hardware and performance and instrument == 'guitar' and project.guitar_sustain < 127:
        preparation = envelope_preparation(project.guitar_sustain, True)
    return replace(plan, events=events, duration=plan.duration+LEAD_IN, preparation=preparation)


def strike_frames(target, instrument):
    if instrument not in ('guitar', 'drums'):
        raise ValueError('不支持此乐器的实时命中发声')
    if instrument == 'drums':
        return b''.join(hit_frame(note.pitch, note.velocity) for note in target.notes)
    return b''.join(targeted_note('guitar', note.pitch, note.velocity, True) for note in target.notes)


class LiveStriker:
    """A small independent producer sharing SerializedPort with accompaniment.

    Only naturally decaying pluck/drum commands are accepted: no independent
    piano/violin Off can accidentally kill the accompaniment's same-pitch gate.
    """
    def __init__(self, sender, clock=time.monotonic):
        self.sender, self.clock = sender, clock
        self.condition = threading.Condition()
        self.queue = deque()
        self.closed, self.error = False, ''
        self.sent = 0
        self.thread = threading.Thread(target=self._run, name='RhythmLiveHits', daemon=True)
        self.thread.start()

    def submit(self, data):
        if not data or len(data) % 6 or any(data[i+1] not in (0x0a, 0x50) for i in range(0, len(data), 6)):
            raise ValueError('只接收完整吉他或鼓命中帧')
        with self.condition:
            if self.closed or self.error:
                return False
            if len(self.queue) >= 32:
                self.error = '命中音符队列已满，停止以避免集中补发'
                self.queue.clear()
                return False
            self.queue.append((self.clock(), bytes(data)))
            self.condition.notify_all()
            return True

    def _run(self):
        while True:
            with self.condition:
                while not self.queue and not self.closed:
                    self.condition.wait()
                if self.closed:
                    return
                when, data = self.queue.popleft()
            try:
                if self.clock()-when > .150:
                    raise TimeoutError('命中发声发送迟到超过150ms')
                if not self.sender(data):
                    raise IOError('命中发声发送失败')
                self.sent += 1
            except Exception as error:
                with self.condition:
                    self.error = str(error)
                    self.queue.clear()
                    self.closed = True
                return

    def shutdown(self, timeout=.3):
        with self.condition:
            self.closed = True
            self.queue.clear()
            self.condition.notify_all()
        self.thread.join(timeout)
        return not self.thread.is_alive()
