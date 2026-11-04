from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from experiments.violin_v1 import reference_model as baseline


FRICTION_SHAPE_LOWER = 0.98 ** (-0.25) - 0.75
FRICTION_SHAPE_UPPER = 0.01 ** (-0.25) - 0.75


@dataclass(frozen=True)
class Settings(baseline.Settings):
    high_register_pressure: float = 0.95
    pressure_ramp_start_note: int = 81
    pressure_ramp_end_note: int = 88
    drive_velocity_min: float = 80.0
    drive_velocity_max: float = 100.0
    control_smoothing_seconds: float = 0.004

    @classmethod
    def load(cls, **overrides):
        data = baseline.Settings.load().__dict__.copy()
        data.update(json.loads((ROOT / 'config.json').read_text(encoding='utf-8')))
        return replace(cls(**data), **overrides)

    def __post_init__(self):
        super().__post_init__()
        if self.oversampling != 2:
            raise ValueError('V2 calibration and control map require 96 kHz internal rate')
        if not 0 <= self.bow_pressure <= self.high_register_pressure <= 1:
            raise ValueError('Invalid coordinated pressure range')
        if any(type(value) is not int for value in
               (self.pressure_ramp_start_note, self.pressure_ramp_end_note)):
            raise ValueError('Pressure ramp notes must be integers')
        if not 55 <= self.pressure_ramp_start_note < self.pressure_ramp_end_note <= 100:
            raise ValueError('Invalid pressure ramp note range')
        if not 1 <= self.drive_velocity_min <= self.drive_velocity_max <= 127:
            raise ValueError('Invalid physical drive range')
        if self.control_smoothing_seconds <= 0:
            raise ValueError('Control smoothing must be positive')


def bow_controls(note, velocity, settings):
    if type(note) is not int or not 55 <= note <= 100:
        raise ValueError('Violin prototype accepts MIDI notes 55..100')
    if type(velocity) is not int or not 1 <= velocity <= 127:
        raise ValueError('Note On velocity must be 1..127')
    position = min(1.0, max(0.0, (note - settings.pressure_ramp_start_note) /
                            (settings.pressure_ramp_end_note - settings.pressure_ramp_start_note)))
    pressure = settings.bow_pressure + position * (settings.high_register_pressure - settings.bow_pressure)
    drive = settings.drive_velocity_min + (settings.drive_velocity_max - settings.drive_velocity_min) * velocity / 127
    return pressure, 0.03 + 0.18 * drive / 127, velocity / 100.0


def delay_capacities(settings):
    minimum_tuned = baseline.midi_frequency(55) * 2 ** (-40 / 1200)
    longest_period = (settings.sample_rate * settings.oversampling / minimum_tuned + 2) * 2 ** (settings.vibrato_cents / 1200)
    capacities = []
    for ratio in (1 - settings.bow_position, settings.bow_position):
        required = math.ceil(longest_period * ratio) + 2
        capacities.append(1 << (required - 1).bit_length())
    return tuple(capacities)


def friction_table(size=1024):
    if type(size) is not int or size < 2:
        raise ValueError('Friction table size must be an integer of at least two')
    coordinates = np.linspace(FRICTION_SHAPE_LOWER, FRICTION_SHAPE_UPPER, size)
    return np.rint((coordinates + 0.75) ** -4 * (1 << 18)).astype(np.int64)


def table_reflection(relative_velocity, pressure, table):
    shaped = abs((relative_velocity + 0.001) * (5 - 4 * pressure))
    position = min(1.0, max(0.0, (shaped - FRICTION_SHAPE_LOWER) /
                            (FRICTION_SHAPE_UPPER - FRICTION_SHAPE_LOWER))) * (len(table) - 1)
    address = min(len(table) - 2, int(position))
    fraction = position - address
    return (float(table[address]) * (1 - fraction) + float(table[address + 1]) * fraction) / (1 << 18)


def calibration_signature(settings):
    parameters = settings.__dict__.copy()
    for name in ('vibrato_cents', 'vibrato_hz', 'vibrato_delay_seconds', 'vibrato_ramp_seconds', 'output_gain'):
        parameters.pop(name)
    sources = [Path(__file__), ROOT / 'config.json', baseline.ROOT / 'reference_model.py', baseline.ROOT / 'config.json']
    return dict(parameters=parameters, source_sha256={str(path.relative_to(ROOT.parent)):
                hashlib.sha256(path.read_bytes()).hexdigest() for path in sources})


def load_calibration(settings, path=None):
    table = json.loads((path or ROOT / 'calibration.json').read_text(encoding='utf-8'))
    if table['signature'] != calibration_signature(settings):
        raise ValueError('Calibration is stale or incompatible; regenerate it for these settings')
    if set(table['cents_correction']) != {str(note) for note in range(55, 101)}:
        raise ValueError('Calibration must cover all MIDI notes 55..100')
    if any(not math.isfinite(value) or abs(value) > 40 for value in table['cents_correction'].values()):
        raise ValueError('Calibration cannot repair octave jumps or large pitch errors')
    return table


class BowedVoice(baseline.BowedVoice):
    def __init__(self, settings=None, calibrated=True, friction_mode='analytic'):
        settings = settings or Settings.load()
        super().__init__(settings)
        neck_capacity, bridge_capacity = delay_capacities(settings)
        self.neck = baseline.FractionalDelay(neck_capacity)
        self.bridge = baseline.FractionalDelay(bridge_capacity)
        self.capacity = max(neck_capacity, bridge_capacity)
        if friction_mode not in ('analytic', 'lut'):
            raise ValueError('Unknown friction mode')
        self.calibration = load_calibration(settings) if calibrated else None
        self.friction_table = friction_table() if friction_mode == 'lut' else None
        self.pressure = settings.bow_pressure
        self.target_pressure = self.pressure
        self.bow_velocity = 0.0
        self.loudness = 0.0
        self.target_loudness = 0.0
        self.control_smoothing = 1 - math.exp(-1 / (self.rate * settings.control_smoothing_seconds))

    def note_on(self, note, velocity=100, legato=False):
        pressure, drive, loudness = bow_controls(note, velocity, self.settings)
        fresh = not self.started or (not self.gate and self.envelope < 1e-6)
        super().note_on(note, velocity, legato)
        correction = self.calibration['cents_correction'][str(note)] if self.calibration else 0.0
        frequency = baseline.midi_frequency(note) * 2 ** (correction / 1200)
        self.target_period = baseline.matched_period(frequency, self.rate, self.settings.bow_position, self.pole)
        self.target_velocity = drive
        self.target_pressure = pressure
        self.target_loudness = loudness
        if fresh:
            self.current_period = self.target_period
            self.pressure = pressure
            self.bow_velocity = drive

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
        self.pressure += self.control_smoothing * (self.target_pressure - self.pressure)
        self.bow_velocity += self.control_smoothing * (self.target_velocity - self.bow_velocity)
        self.loudness += self.control_smoothing * (self.target_loudness - self.loudness)
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
        difference = self.bow_velocity * self.envelope - bridge_reflection - nut_reflection
        if not self.contact:
            interaction = 0.0
        elif self.friction_table is None:
            interaction = difference * baseline.bow_reflection(difference, self.pressure)
        else:
            interaction = difference * table_reflection(difference, self.pressure, self.friction_table)
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
        return bridge_out * self.loudness


def render(events, duration, settings=None, body_enabled=True, calibrated=True, friction_mode='analytic'):
    settings = settings or Settings.load()
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Duration must be positive and finite')
    voice = BowedVoice(settings, calibrated, friction_mode)
    body = baseline.BodyFilter(voice.rate, enabled=body_enabled)
    frame_count = round(duration * settings.sample_rate)
    if frame_count == 0:
        raise ValueError('Duration is shorter than one output sample')
    output = np.empty(frame_count * settings.oversampling, dtype=np.float64)
    event_map = {}
    for event in events:
        moment = round(event['time'] * voice.rate)
        if not 0 <= moment < len(output):
            raise ValueError('Event falls outside render')
        event_map.setdefault(moment, []).append(event)
    for frame in range(len(output)):
        for event in event_map.get(frame, ()):
            if event['type'] == 'on':
                voice.note_on(event['note'], event.get('velocity', 100), event.get('legato', False))
            elif event['type'] == 'off':
                voice.note_off()
            else:
                raise ValueError('Unknown event type')
        output[frame] = body.process(voice.process()) * settings.output_gain
    audio = baseline.decimate(output, settings)
    if not np.isfinite(audio).all() or np.max(np.abs(audio), initial=0) >= 0.98:
        raise ArithmeticError('Audio clips or is nonfinite; no per-file normalization is applied')
    return audio, dict(peak_internal=voice.peak_internal, internal_steps=voice.steps,
                       internal_rate=voice.rate, fixed_output_gain=settings.output_gain,
                       calibrated=calibrated, friction_mode=friction_mode,
                       delay_capacities=[len(voice.neck.memory), len(voice.bridge.memory)],
                       body_is_measured=False, clipping_samples=int(np.count_nonzero(np.abs(audio) >= 1)))
