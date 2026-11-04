from dataclasses import dataclass, replace
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    sample_rate: int = 48000
    oversampling: int = 2
    minimum_frequency_hz: float = 160.0
    maximum_frequency_hz: float = 3200.0
    bow_pressure: float = 0.70
    bow_position: float = 0.127236
    string_cutoff_hz: float = 4200.0
    string_gain: float = 0.985
    released_string_gain: float = 0.94
    attack_seconds: float = 0.035
    release_seconds: float = 0.055
    glide_seconds: float = 0.012
    vibrato_hz: float = 5.6
    vibrato_cents: float = 24.0
    vibrato_delay_seconds: float = 0.25
    vibrato_ramp_seconds: float = 0.2
    output_gain: float = 0.65
    decimator_taps: int = 95
    decimator_cutoff_hz: float = 21000.0

    @classmethod
    def load(cls, **overrides):
        data = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
        settings = cls(**{name: data[name] for name in cls.__dataclass_fields__})
        return replace(settings, **overrides)

    def __post_init__(self):
        if any(type(value) is not int for value in (self.sample_rate, self.oversampling, self.decimator_taps)):
            raise ValueError('Rates, oversampling and tap count require integers')
        if self.sample_rate != 48000 or self.oversampling not in (1, 2):
            raise ValueError('Prototype supports 48 kHz output and 1x/2x internal rates')
        if not all(math.isfinite(value) for value in self.__dict__.values()):
            raise ValueError('Settings must be finite')
        if not 0.08 <= self.bow_position <= 0.30 or not 0.0 <= self.bow_pressure <= 1.0:
            raise ValueError('Bow controls out of prototype range')
        if not 0 < self.released_string_gain <= self.string_gain < 1:
            raise ValueError('String reflection gains must be passive')
        if not 0 < self.minimum_frequency_hz < self.maximum_frequency_hz < self.sample_rate / 2:
            raise ValueError('Invalid frequency range')
        if not 0 < self.string_cutoff_hz < self.sample_rate / 2:
            raise ValueError('Invalid string cutoff')
        if min(self.attack_seconds, self.release_seconds, self.glide_seconds,
               self.vibrato_ramp_seconds) <= 0:
            raise ValueError('Smoothing times must be positive')
        if not 0 <= self.vibrato_cents <= 50 or not 0 <= self.vibrato_hz <= 10:
            raise ValueError('Vibrato out of prototype range')
        if self.vibrato_delay_seconds < 0 or not 0 < self.output_gain <= 1:
            raise ValueError('Invalid delay or output gain')
        if self.decimator_taps < 3 or self.decimator_taps % 2 != 1:
            raise ValueError('FIR length must be odd')
        if not 0 < self.decimator_cutoff_hz < self.sample_rate / 2:
            raise ValueError('Invalid decimation cutoff')


def midi_frequency(note):
    return 440.0 * 2.0 ** ((note - 69.0) / 12.0)


def bow_reflection(relative_velocity, pressure):
    shaped = abs((relative_velocity + 0.001) * (5.0 - 4.0 * pressure))
    return min(0.98, max(0.01, (shaped + 0.75) ** -4.0))


def friction_table(size=1024):
    if size < 2:
        raise ValueError('LUT must have at least two entries')
    coordinates = np.linspace(0.0, 4.0, size)
    return np.rint(np.clip((coordinates + 0.75) ** -4, 0.01, 0.98) * (1 << 18)).astype(np.int64)


def table_reflection(relative_velocity, pressure, table):
    shaped = abs((relative_velocity + 0.001) * (5.0 - 4.0 * pressure))
    position = min(4.0, shaped) * (len(table) - 1) / 4.0
    address = min(len(table) - 2, int(position))
    fraction = position - address
    return (float(table[address]) * (1 - fraction) + float(table[address + 1]) * fraction) / (1 << 18)


class FractionalDelay:
    def __init__(self, capacity):
        if capacity < 4 or capacity & (capacity - 1):
            raise ValueError('Delay capacity must be a power of two')
        self.memory = [0.0] * capacity
        self.mask = capacity - 1
        self.write_index = 0

    def read(self, delay):
        if not math.isfinite(delay) or not 1.0 <= delay <= len(self.memory) - 2:
            raise ValueError(f'Noncausal or out-of-range delay: {delay}')
        integer_delay = int(delay)
        fraction = delay - integer_delay
        recent = self.memory[(self.write_index - integer_delay) & self.mask]
        older = self.memory[(self.write_index - integer_delay - 1) & self.mask]
        return recent + fraction * (older - recent)

    def write(self, value):
        self.memory[self.write_index] = value
        self.write_index = (self.write_index + 1) & self.mask


def matched_period(frequency, sample_rate, position, pole):
    angular = 2.0 * math.pi * frequency / sample_rate
    pole_phase = math.atan2(pole * math.sin(angular), 1.0 - pole * math.cos(angular))

    def delay_phase(delay):
        whole = int(delay)
        fraction = delay - whole
        return whole * angular + math.atan2(fraction * math.sin(angular),
                                            1 - fraction + fraction * math.cos(angular))

    lower = max(1.0 / position, 1.0 / (1 - position))
    upper = sample_rate / frequency + 2.0
    if lower >= upper:
        raise ValueError('Pitch and bow position cannot provide two causal delays')
    for iteration in range(40):
        middle = (lower + upper) / 2.0
        phase = delay_phase(middle * position) + delay_phase(middle * (1 - position)) + pole_phase
        if phase > 2.0 * math.pi:
            upper = middle
        else:
            lower = middle
    return (lower + upper) / 2.0


def peaking_coefficients(sample_rate, frequency, quality, gain_db):
    angular = 2 * math.pi * frequency / sample_rate
    amplitude = 10 ** (gain_db / 40)
    alpha = math.sin(angular) / (2 * quality)
    denominator = 1 + alpha / amplitude
    return ((1 + alpha * amplitude) / denominator,
            -2 * math.cos(angular) / denominator,
            (1 - alpha * amplitude) / denominator,
            -2 * math.cos(angular) / denominator,
            (1 - alpha / amplitude) / denominator)


class BodyFilter:
    def __init__(self, sample_rate, enabled=True):
        data = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
        self.coefficients = [peaking_coefficients(sample_rate, **parameters)
                             for parameters in data['body_filters_unmeasured_candidate']] if enabled else []
        self.states = [[0.0, 0.0] for coefficient in self.coefficients]
        self.previous_input = 0.0
        self.previous_output = 0.0
        self.dc_pole = math.exp(-2 * math.pi * 12 / sample_rate)

    def process(self, value):
        for coefficients, state in zip(self.coefficients, self.states):
            feed0, feed1, feed2, feedback1, feedback2 = coefficients
            output = feed0 * value + state[0]
            state[0] = feed1 * value - feedback1 * output + state[1]
            state[1] = feed2 * value - feedback2 * output
            value = output
        output = value - self.previous_input + self.dc_pole * self.previous_output
        self.previous_input = value
        self.previous_output = output
        return output


class BowedVoice:
    def __init__(self, settings=None):
        self.settings = settings or Settings.load()
        self.rate = self.settings.sample_rate * self.settings.oversampling
        self.pole = math.exp(-2 * math.pi * self.settings.string_cutoff_hz / self.rate)
        self.capacity = 512 * self.settings.oversampling
        self.neck = FractionalDelay(self.capacity)
        self.bridge = FractionalDelay(self.capacity)
        self.current_period = matched_period(440, self.rate, self.settings.bow_position, self.pole)
        self.target_period = self.current_period
        self.envelope = 0.0
        self.target_velocity = 0.0
        self.gate = False
        self.started = False
        self.note_age = 0
        self.vibrato_phase = 0.0
        self.loss_state = 0.0
        self.loss_gain = self.settings.released_string_gain
        self.peak_internal = 0.0
        self.steps = 0
        self.contact = False
        self.gliding = 1 - math.exp(-1 / (self.rate * self.settings.glide_seconds))
        self.gain_smoothing = 1 - math.exp(-1 / (self.rate * 0.004))
        self.rebow_remaining = 0

    def note_on(self, note, velocity=100, legato=False):
        if not isinstance(note, int) or not 55 <= note <= 100:
            raise ValueError('Violin prototype accepts MIDI notes 55..100')
        if not isinstance(velocity, int) or not 1 <= velocity <= 127:
            raise ValueError('Note On velocity must be 1..127')
        frequency = midi_frequency(note)
        if not self.settings.minimum_frequency_hz <= frequency <= self.settings.maximum_frequency_hz:
            raise ValueError('Note frequency outside configured range')
        self.target_period = matched_period(frequency, self.rate,
                                             self.settings.bow_position, self.pole)
        if not self.started or (not self.gate and self.envelope < 1e-6):
            self.current_period = self.target_period
        elif not legato:
            self.rebow_remaining = round(0.004 * self.rate)
        self.target_velocity = 0.03 + 0.18 * velocity / 127.0
        if not legato or not self.gate:
            self.note_age = 0
        self.gate = True
        self.started = True

    def note_off(self):
        self.gate = False

    def process(self):
        if self.rebow_remaining:
            self.rebow_remaining -= 1
            target = 0.0
            ramp = 1.0 / (self.rate * 0.004)
        else:
            target = 1.0 if self.gate else 0.0
            seconds = self.settings.attack_seconds if self.gate else self.settings.release_seconds
            ramp = 1.0 / (self.rate * seconds)
        if self.envelope < target:
            self.envelope = min(target, self.envelope + ramp)
        else:
            self.envelope = max(target, self.envelope - ramp)
        self.contact = self.envelope > 1e-10
        gain_target = self.settings.string_gain if self.contact else self.settings.released_string_gain
        self.loss_gain += self.gain_smoothing * (gain_target - self.loss_gain)
        self.current_period += self.gliding * (self.target_period - self.current_period)
        ramp_age = self.note_age / self.rate - self.settings.vibrato_delay_seconds
        vibrato_entry = min(1.0, max(0.0, ramp_age / self.settings.vibrato_ramp_seconds))
        cents = self.settings.vibrato_cents * vibrato_entry * math.sin(self.vibrato_phase)
        period = self.current_period * 2 ** (-cents / 1200.0)
        neck_out = self.neck.read(period * (1 - self.settings.bow_position))
        bridge_out = self.bridge.read(period * self.settings.bow_position)
        self.loss_state = (1 - self.pole) * bridge_out + self.pole * self.loss_state
        bridge_reflection = -self.loss_gain * self.loss_state
        nut_reflection = -neck_out
        difference = self.target_velocity * self.envelope - bridge_reflection - nut_reflection
        interaction = difference * bow_reflection(difference, self.settings.bow_pressure) if self.contact else 0.0
        neck_input = bridge_reflection + interaction
        bridge_input = nut_reflection + interaction
        peak = max(abs(neck_input), abs(bridge_input), abs(self.loss_state))
        if not math.isfinite(peak) or peak > 8:
            raise ArithmeticError('Unstable waveguide; refusing to hide instability with clipping')
        self.peak_internal = max(self.peak_internal, peak)
        self.neck.write(neck_input)
        self.bridge.write(bridge_input)
        self.vibrato_phase = (self.vibrato_phase + 2 * math.pi * self.settings.vibrato_hz / self.rate) % (2 * math.pi)
        self.note_age += 1
        self.steps += 1
        return bridge_out


def decimator_coefficients(settings):
    if settings.oversampling == 1:
        return np.ones(1)
    sample_rate = settings.sample_rate * settings.oversampling
    offsets = np.arange(settings.decimator_taps) - (settings.decimator_taps - 1) / 2
    normalized = 2 * settings.decimator_cutoff_hz / sample_rate
    taps = normalized * np.sinc(normalized * offsets) * np.kaiser(settings.decimator_taps, 8.6)
    return taps / taps.sum()


def decimate(values, settings):
    taps = decimator_coefficients(settings)
    filtered = np.convolve(np.asarray(values, dtype=np.float64), taps, mode='full')[:len(values)]
    return filtered[settings.oversampling - 1::settings.oversampling]


def render(events, duration, settings=None, body_enabled=True):
    settings = settings or Settings.load()
    voice = BowedVoice(settings)
    body = BodyFilter(voice.rate, enabled=body_enabled)
    event_map = {}
    for event in events:
        moment = round(event['time'] * voice.rate)
        if not 0 <= moment < round(duration * voice.rate):
            raise ValueError('Event falls outside render')
        event_map.setdefault(moment, []).append(event)
    frame_count = round(duration * settings.sample_rate)
    output = np.empty(frame_count * settings.oversampling, dtype=np.float64)
    for frame in range(len(output)):
        for event in event_map.get(frame, ()):
            if event['type'] == 'on':
                voice.note_on(event['note'], event.get('velocity', 100), event.get('legato', False))
            elif event['type'] == 'off':
                voice.note_off()
            else:
                raise ValueError('Unknown event type')
        output[frame] = body.process(voice.process()) * settings.output_gain
    audio = decimate(output, settings)
    if not np.isfinite(audio).all() or np.max(np.abs(audio), initial=0) >= 0.98:
        raise ArithmeticError('Audio clips or is nonfinite; no per-file normalization is applied')
    return audio, dict(peak_internal=voice.peak_internal, internal_steps=voice.steps,
                       internal_rate=voice.rate, fixed_output_gain=settings.output_gain,
                       body_is_measured=False, clipping_samples=int(np.count_nonzero(np.abs(audio) >= 1)))
