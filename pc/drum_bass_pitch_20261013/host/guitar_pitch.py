"""Host-side pitch gestures. No UART writes or note retriggers are performed.

The future FPGA/encoder adapter consumes snapshot(); detents enter through
handle_encoder_delta(), the same path used by the UI's encoder simulator.
"""
from dataclasses import asdict, dataclass, replace
import math
import time


LIMITS = {
    'slide_range_cents': (0.0, 1200.0),
    'slide_ms': (20.0, 3000.0),
    'vibrato_depth_cents': (0.0, 200.0),
    'vibrato_rate_hz': (0.5, 12.0),
}
ENCODER_STEPS = {
    'slide_range_cents': 25.0, 'slide_ms': 20.0,
    'vibrato_depth_cents': 5.0, 'vibrato_rate_hz': 0.25,
}


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Pitch values must be finite')
    return value


def clamp(value, lo, hi):
    return min(hi, max(lo, finite(value)))


def smoothstep(value):
    value = clamp(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


@dataclass(frozen=True)
class PitchSettings:
    slide_range_cents: float = 200.0
    slide_ms: float = 250.0
    vibrato_depth_cents: float = 35.0
    vibrato_rate_hz: float = 5.0

    def normalized(self):
        return PitchSettings(**{key: clamp(value, *LIMITS[key])
                                for key, value in asdict(self).items()})

    def to_dict(self):
        return {'version': 1, **asdict(self.normalized())}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get('version') != 1:
            raise ValueError('Unsupported pitch settings version')
        if set(data) != {'version', *LIMITS}:
            raise ValueError('Incomplete or unknown pitch settings')
        return cls(**{key: data[key] for key in LIMITS}).normalized()


class PitchControl:
    def __init__(self, settings=None, clock=time.monotonic):
        self.clock = clock
        self.settings = (settings or PitchSettings()).normalized()
        self._last = finite(clock())
        self._phase = 0.0
        self._slide_start = self._last
        self._slide_from = self._slide_target = 0.0
        self._slide_duration = self.settings.slide_ms / 1000.0
        self._position = 0.0
        self.vibrato_enabled = False
        self._depth_from = self._depth_target = 0.0
        self._depth_start = self._last

    def _now(self, now):
        # Monotonic elapsed time; delayed UI redraws do not slow the gesture.
        return max(self._last, finite(self.clock() if now is None else now))

    def _slide(self, now):
        mix = smoothstep((now - self._slide_start) / self._slide_duration)
        return self._slide_from + (self._slide_target - self._slide_from) * mix

    def _depth(self, now):
        mix = smoothstep((now - self._depth_start) / 0.02)
        return self._depth_from + (self._depth_target - self._depth_from) * mix

    def advance(self, now=None):
        now = self._now(now)
        self._phase = (self._phase + (now - self._last) *
                       self.settings.vibrato_rate_hz) % 1.0
        self._last = now
        return self._slide(now) + self._depth(now) * math.sin(2 * math.pi * self._phase)

    def set_settings(self, settings, now=None):
        settings = settings.normalized()  # Validate before changing any state.
        self.advance(now)
        current_slide, current_depth = self._slide(self._last), self._depth(self._last)
        self.settings = settings
        self._slide_from = current_slide
        self._slide_start = self._last
        self._slide_target = self._position * settings.slide_range_cents
        self._slide_duration = settings.slide_ms / 1000.0
        self._depth_from = current_depth
        self._depth_start = self._last
        self._depth_target = settings.vibrato_depth_cents if self.vibrato_enabled else 0.0

    def set_slide_position(self, position, now=None):
        position = clamp(position, -1.0, 1.0)
        self.advance(now)
        self._slide_from = self._slide(self._last)
        self._slide_start = self._last
        self._position = position
        self._slide_target = position * self.settings.slide_range_cents
        self._slide_duration = self.settings.slide_ms / 1000.0

    def enable_vibrato(self, enabled, now=None):
        self.advance(now)
        self._depth_from = self._depth(self._last)
        self._depth_start = self._last
        self.vibrato_enabled = bool(enabled)
        self._depth_target = self.settings.vibrato_depth_cents if enabled else 0.0

    def handle_encoder_delta(self, field, detents, fine=False, now=None):
        if field not in ENCODER_STEPS:
            raise ValueError('Unknown encoder target: ' + str(field))
        if isinstance(detents, bool) or not isinstance(detents, int):
            raise ValueError('Encoder detents must be an integer')
        step = ENCODER_STEPS[field] / (5.0 if fine else 1.0)
        value = clamp(getattr(self.settings, field) + detents * step, *LIMITS[field])
        self.set_settings(replace(self.settings, **{field: value}), now)
        return value

    @property
    def slide_position(self):
        return self._position

    def reset(self, now=None):
        self._last = self._now(now)
        self._phase = self._position = 0.0
        self._slide_from = self._slide_target = 0.0
        self._slide_start = self._last
        self._depth_from = self._depth_target = 0.0
        self._depth_start = self._last
        self.vibrato_enabled = False

    def snapshot(self, base_hz, now=None):
        base_hz = finite(base_hz)
        if base_hz <= 0:
            raise ValueError('Base frequency must be positive')
        cents = self.advance(now)
        ratio = 2.0 ** (cents / 1200.0)
        return {'cents': cents, 'frequency_hz': base_hz * ratio,
                'ratio_q20': round(ratio * (1 << 20)),
                'slide_cents': self._slide(self._last),
                'vibrato_cents': cents - self._slide(self._last)}

    def frequency_bounds(self, base_hz):
        base_hz = finite(base_hz)
        if base_hz <= 0:
            raise ValueError('Base frequency must be positive')
        extent = self.settings.slide_range_cents + self.settings.vibrato_depth_cents
        return (base_hz * 2 ** (-extent / 1200), base_hz * 2 ** (extent / 1200))
