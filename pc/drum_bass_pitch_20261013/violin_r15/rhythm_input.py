"""Read-only S3 Hall log adapter; never infer a tap from 1Hz ADC snapshots."""
from collections import deque
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class HallHit:
    at: float
    string: int
    velocity: int
    channel: int
    timestamped: bool


class HallInput:
    def __init__(self):
        self.offset = None
        self.last_device = None
        self.seen = deque(maxlen=256)

    def feed(self, line, received):
        # Both accepted and rejected sensor detections are useful rhythm inputs;
        # queued=0 may simply mean local playback is suppressed in ensemble mode.
        match = re.search(r'\bHALL:\s+(?:PICK H([1-7]) string=([1-6]) velocity=(\d+) queued=[01]|STRUM H1 strings=6,5,4,3,2,1 interval_ms=\d+ velocity=(\d+) queued=[01])', line)
        if not match:
            return None
        channel = int(match[1]) if match[1] else 1
        string = int(match[2]) if match[2] else 0
        velocity = int(match[3] or match[4])
        if not 1 <= velocity <= 127:
            return None
        stamp = re.search(r'\((\d+)\)', line[:match.start()])
        if stamp:
            device = int(stamp[1])/1000
            key = (device, channel)
            if key in self.seen:
                return None
            if self.last_device is not None and device < self.last_device-1:
                # Device reboot or wrap: establish a fresh clock relation.
                self.offset = None
                self.seen.clear()
            self.seen.append(key)
            self.last_device = device
            estimate = received-device
            self.offset = estimate if self.offset is None else min(self.offset, estimate)
            at = min(received, device+self.offset)
        else:
            at = received
        if received-at > .5:
            return None  # stale USB backlog is not a current hit
        return HallHit(at, string, velocity, channel, stamp is not None)
