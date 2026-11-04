from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from experiments.violin_v2 import violin_model as reference


Settings = reference.Settings
CONTROL_ONE = 1 << 24
RATIO_ONE = 1 << 22
ROUNDING = {shift: ((1 << shift) - 1, 1 << (shift - 1)) for shift in range(1, 57)}
LIMITS = {(width, unsigned): ((0, (1 << width) - 1) if unsigned else
                             (-(1 << (width - 1)), (1 << (width - 1)) - 1))
          for width in range(1, 65) for unsigned in (False, True)}


def round_shift(value, shift):
    if shift == 0:
        return value
    mask, halfway = ROUNDING[shift]
    quotient = value >> shift
    remainder = value & mask
    return quotient + int(remainder > halfway or (remainder == halfway and quotient & 1))


def round_shift_array(values, shift):
    mask, halfway = ROUNDING[shift]
    quotient = values >> shift
    remainder = values & mask
    return quotient + ((remainder > halfway) | ((remainder == halfway) & ((quotient & 1) != 0)))


def dissipative_shift(value, shift):
    return value >> shift if value >= 0 else -((-value) >> shift)


class Arithmetic:
    def __init__(self, strict=True):
        self.strict = strict
        self.overflows = {}

    def fit(self, value, width, stage, unsigned=False):
        lower, upper = LIMITS[width, unsigned]
        if lower <= value <= upper:
            return value
        self.overflows[stage] = self.overflows.get(stage, 0) + 1
        if self.strict:
            raise ArithmeticError(f'{stage}: {value} does not fit {width} bits; no hidden wraparound')
        return min(upper, max(lower, value))


def quantize(value, fraction_bits, width, unsigned=False):
    quantized = round(value * (1 << fraction_bits))
    lower, upper = LIMITS[width, unsigned]
    if not lower <= quantized <= upper:
        raise ValueError('Offline coefficient does not fit declared format')
    return quantized


@dataclass(frozen=True)
class Tables:
    internal_rate: int
    neck_capacity: int
    bridge_capacity: int
    periods: tuple
    pressure: tuple
    drive: tuple
    loudness: tuple
    friction: tuple
    vibrato_ratio: tuple
    body: tuple
    fir: tuple
    attack_step: int
    release_step: int
    rebow_step: int
    rebow_samples: int
    vibrato_delay_samples: int
    vibrato_entry_step: int
    phase_increment: int
    control_alpha: int
    glide_alpha: int
    loss_alpha: int
    loss_gain_on: int
    loss_gain_off: int
    string_feed: int
    dc_pole: int
    output_gain: int
    bow_position: int
    friction_lower: int
    friction_upper: int
    friction_scale: int


@lru_cache(maxsize=16)
def compile_tables(settings):
    calibration = reference.load_calibration(settings)
    rate = settings.sample_rate * settings.oversampling
    pole = math.exp(-2 * math.pi * settings.string_cutoff_hz / rate)
    periods = []
    pressures = []
    for note in range(55, 101):
        frequency = reference.baseline.midi_frequency(note) * 2 ** (calibration['cents_correction'][str(note)] / 1200)
        periods.append(quantize(reference.baseline.matched_period(frequency, rate, settings.bow_position, pole), 16, 26, True))
        pressures.append(quantize(reference.bow_controls(note, 100, settings)[0], 24, 26))
    controls = [reference.bow_controls(69, velocity, settings) for velocity in range(1, 128)]
    body = tuple(tuple(quantize(coefficient, 22, 24) for coefficient in section)
                 for section in reference.baseline.BodyFilter(rate).coefficients)
    fir = [quantize(float(value), 23, 24) for value in reference.baseline.decimator_coefficients(settings)]
    fir[len(fir) // 2] += (1 << 23) - sum(fir)
    if fir != fir[::-1] or not LIMITS[24, False][0] <= fir[len(fir) // 2] <= LIMITS[24, False][1]:
        raise ValueError('FIR quantization violated symmetry or coefficient range')
    neck, bridge = reference.delay_capacities(settings)
    return Tables(internal_rate=rate, neck_capacity=neck, bridge_capacity=bridge,
                  periods=tuple(periods), pressure=tuple(pressures),
                  drive=tuple(quantize(control[1], 24, 26) for control in controls),
                  loudness=tuple(quantize(control[2], 24, 26) for control in controls),
                  friction=tuple(int(value) for value in reference.friction_table()),
                  vibrato_ratio=tuple(quantize(2 ** (-settings.vibrato_cents * math.sin(2 * math.pi * index / 1024) / 1200),
                                               22, 24, True) for index in range(1024)),
                  body=body, fir=tuple(fir), attack_step=max(1, round(CONTROL_ONE / (rate * settings.attack_seconds))),
                  release_step=max(1, round(CONTROL_ONE / (rate * settings.release_seconds))),
                  rebow_step=max(1, round(CONTROL_ONE / (rate * 0.004))), rebow_samples=round(rate * 0.004),
                  vibrato_delay_samples=round(rate * settings.vibrato_delay_seconds),
                  vibrato_entry_step=max(1, round(CONTROL_ONE / (rate * settings.vibrato_ramp_seconds))),
                  phase_increment=round(settings.vibrato_hz * (1 << 32) / rate),
                  control_alpha=quantize(1 - math.exp(-1 / (rate * settings.control_smoothing_seconds)), 24, 24, True),
                  glide_alpha=quantize(1 - math.exp(-1 / (rate * settings.glide_seconds)), 24, 24, True),
                  loss_alpha=quantize(1 - math.exp(-1 / (rate * 0.004)), 24, 24, True),
                  loss_gain_on=quantize(settings.string_gain, 24, 26),
                  loss_gain_off=quantize(settings.released_string_gain, 24, 26),
                  string_feed=quantize(1 - pole, 22, 24, True),
                  dc_pole=quantize(math.exp(-2 * math.pi * 12 / rate), 22, 24, True),
                  output_gain=quantize(settings.output_gain, 24, 26),
                  bow_position=quantize(settings.bow_position, 24, 24, True),
                  friction_lower=quantize(reference.FRICTION_SHAPE_LOWER, 20, 24, True),
                  friction_upper=quantize(reference.FRICTION_SHAPE_UPPER, 20, 24, True),
                  friction_scale=quantize(1023 / (reference.FRICTION_SHAPE_UPPER - reference.FRICTION_SHAPE_LOWER), 16, 26, True))


class FractionalDelay:
    def __init__(self, capacity, arithmetic):
        if type(capacity) is not int or capacity < 4 or capacity & (capacity - 1):
            raise ValueError('Delay capacity must be a power of two')
        self.memory = [0] * capacity
        self.mask = capacity - 1
        self.write_index = 0
        self.arithmetic = arithmetic

    def read(self, delay_q16):
        if type(delay_q16) is not int or not 1 << 16 <= delay_q16 <= (len(self.memory) - 2) << 16:
            raise ValueError('Noncausal or out-of-range fixed delay')
        whole = delay_q16 >> 16
        fraction = delay_q16 & 65535
        recent = self.memory[(self.write_index - whole) & self.mask]
        older = self.memory[(self.write_index - whole - 1) & self.mask]
        return self.arithmetic.fit(recent + round_shift((older - recent) * fraction, 16), 24, 'delay_interpolation')

    def write(self, value):
        self.memory[self.write_index] = self.arithmetic.fit(value, 24, 'waveguide_write')
        self.write_index = (self.write_index + 1) & self.mask


def friction_coefficient(relative_q20, pressure_q24, tables):
    slope = 5 * CONTROL_ONE - 4 * pressure_q24
    shaped = abs(round_shift((relative_q20 + 1049) * slope, 24))
    if shaped <= tables.friction_lower:
        return tables.friction[0]
    if shaped >= tables.friction_upper:
        return tables.friction[-1]
    position = min(1023 << 16, round_shift((shaped - tables.friction_lower) * tables.friction_scale, 20))
    address = min(1022, position >> 16)
    fraction = position - (address << 16)
    return tables.friction[address] + round_shift((tables.friction[address + 1] - tables.friction[address]) * fraction, 16)


class BowedVoice:
    def __init__(self, settings=None, arithmetic=None):
        self.tables = compile_tables(settings or Settings.load())
        self.arithmetic = arithmetic or Arithmetic()
        self.neck = FractionalDelay(self.tables.neck_capacity, self.arithmetic)
        self.bridge = FractionalDelay(self.tables.bridge_capacity, self.arithmetic)
        self.period = self.tables.periods[69 - 55]
        self.target_period = self.period
        self.pressure = self.tables.pressure[69 - 55]
        self.target_pressure = self.pressure
        self.velocity = 0
        self.target_velocity = 0
        self.loudness = 0
        self.target_loudness = 0
        self.loss_gain = self.tables.loss_gain_off
        self.loss_state = 0
        self.envelope = 0
        self.note_age = 0
        self.phase = 0
        self.vibrato_entry = 0
        self.rebow_remaining = 0
        self.gate = False
        self.started = False
        self.steps = 0
        self.peak_waveguide_q20 = 0
        self.residues = [0] * 5

    def note_on(self, note, velocity=100, legato=False):
        if type(note) is not int or not 55 <= note <= 100:
            raise ValueError('Violin accepts integer MIDI notes 55..100')
        if type(velocity) is not int or not 1 <= velocity <= 127 or type(legato) is not bool:
            raise ValueError('Invalid velocity or legato flag')
        fresh = not self.started or (not self.gate and self.envelope < 17)
        self.target_period = self.tables.periods[note - 55]
        self.target_pressure = self.tables.pressure[note - 55]
        self.target_velocity = self.tables.drive[velocity - 1]
        self.target_loudness = self.tables.loudness[velocity - 1]
        if fresh:
            self.period = self.target_period
            self.pressure = self.target_pressure
            self.velocity = self.target_velocity
            self.residues[0] = self.residues[1] = self.residues[2] = 0
        elif not legato:
            self.rebow_remaining = self.tables.rebow_samples
        if not legato or not self.gate:
            self.note_age = 0
            self.vibrato_entry = 0
        self.gate = True
        self.started = True

    def note_off(self):
        self.gate = False

    def smooth(self, current, target, alpha, slot):
        accumulator = (target - current) * alpha + self.residues[slot]
        change = round_shift(accumulator, 24)
        self.residues[slot] = accumulator - (change << 24)
        return current + change

    def process(self):
        tables = self.tables
        if self.rebow_remaining:
            self.rebow_remaining -= 1
            target = 0
            step = tables.rebow_step
        else:
            target = CONTROL_ONE if self.gate else 0
            step = tables.attack_step if self.gate else tables.release_step
        self.envelope = min(target, self.envelope + step) if self.envelope < target else max(target, self.envelope - step)
        self.period = self.smooth(self.period, self.target_period, tables.glide_alpha, 0)
        self.pressure = self.smooth(self.pressure, self.target_pressure, tables.control_alpha, 1)
        self.velocity = self.smooth(self.velocity, self.target_velocity, tables.control_alpha, 2)
        self.loudness = self.smooth(self.loudness, self.target_loudness, tables.control_alpha, 3)
        gain_target = tables.loss_gain_on if self.envelope else tables.loss_gain_off
        self.loss_gain = self.smooth(self.loss_gain, gain_target, tables.loss_alpha, 4)
        if self.note_age >= tables.vibrato_delay_samples:
            self.vibrato_entry = min(CONTROL_ONE, self.vibrato_entry + tables.vibrato_entry_step)
        address = self.phase >> 22
        fraction = self.phase & ((1 << 22) - 1)
        ratio = tables.vibrato_ratio[address] + round_shift(
            (tables.vibrato_ratio[(address + 1) & 1023] - tables.vibrato_ratio[address]) * fraction, 22)
        ratio = RATIO_ONE + round_shift((ratio - RATIO_ONE) * self.vibrato_entry, 24)
        period = self.arithmetic.fit(round_shift(self.period * ratio, 22), 26, 'modulated_period', True)
        bridge_delay = round_shift(period * tables.bow_position, 24)
        neck_out = self.neck.read(period - bridge_delay)
        bridge_out = self.bridge.read(bridge_delay)
        self.loss_state = self.arithmetic.fit(self.loss_state + round_shift(
            ((bridge_out << 6) - self.loss_state) * tables.string_feed, 22), 32, 'string_loss_state')
        reflection_product = self.loss_state * self.loss_gain
        bridge_reflection = -(round_shift(reflection_product, 30) if self.envelope else
                              dissipative_shift(reflection_product, 30))
        bow_velocity = round_shift(self.velocity * self.envelope, 28)
        difference = self.arithmetic.fit(bow_velocity - bridge_reflection + neck_out, 26, 'relative_velocity')
        interaction = round_shift(difference * friction_coefficient(difference, self.pressure, tables), 18) if self.envelope else 0
        neck_input = bridge_reflection + interaction
        bridge_input = -neck_out + interaction
        self.peak_waveguide_q20 = max(self.peak_waveguide_q20, abs(neck_input), abs(bridge_input))
        self.neck.write(neck_input)
        self.bridge.write(bridge_input)
        self.phase = (self.phase + tables.phase_increment) & ((1 << 32) - 1)
        self.note_age += 1
        self.steps += 1
        return self.arithmetic.fit(round_shift(bridge_out * self.loudness, 18), 32, 'voice_output_q26')


class BodyFilter:
    def __init__(self, tables, arithmetic, enabled=True):
        self.coefficients = tables.body if enabled else ()
        self.states = [[0, 0] for section in self.coefficients]
        self.dc_pole = tables.dc_pole
        self.previous_input = 0
        self.previous_output = 0
        self.dc_residue = 0
        self.arithmetic = arithmetic
        self.peak_state_q30 = 0

    def process(self, value):
        arithmetic = self.arithmetic
        value = arithmetic.fit(value, 32, 'body_input_q30')
        for coefficients, state in zip(self.coefficients, self.states):
            feed0, feed1, feed2, feedback1, feedback2 = coefficients
            accumulator = arithmetic.fit(feed0 * value + (state[0] << 22), 58, 'body_accumulator')
            output = arithmetic.fit(round_shift(accumulator, 22), 32, 'body_output')
            accumulator = arithmetic.fit(feed1 * value - feedback1 * output + (state[1] << 22), 58, 'body_accumulator')
            state[0] = arithmetic.fit(round_shift(accumulator, 22), 32, 'body_state')
            accumulator = arithmetic.fit(feed2 * value - feedback2 * output, 58, 'body_accumulator')
            state[1] = arithmetic.fit(round_shift(accumulator, 22), 32, 'body_state')
            self.peak_state_q30 = max(self.peak_state_q30, abs(state[0]), abs(state[1]))
            value = output
        accumulator = self.previous_output * self.dc_pole + self.dc_residue
        feedback = round_shift(accumulator, 22)
        self.dc_residue = accumulator - (feedback << 22)
        output = arithmetic.fit(value - self.previous_input + feedback, 32, 'dc_blocker')
        self.previous_input = value
        self.previous_output = output
        return output


def decimate_int(values, tables, arithmetic):
    values = np.asarray(values, dtype=np.int64)
    if values.ndim != 1 or not len(values):
        raise ValueError('FIR requires a nonempty integer vector')
    if np.min(values) < -(1 << 23) or np.max(values) >= 1 << 23:
        raise ArithmeticError('FIR input is not signed 24 bit')
    accumulators = np.convolve(values, np.asarray(tables.fir, dtype=np.int64), mode='full')[:len(values)]
    arithmetic.fit(int(np.max(accumulators)), 56, 'fir_accumulator')
    arithmetic.fit(int(np.min(accumulators)), 56, 'fir_accumulator')
    rounded = round_shift_array(accumulators[1::2], 23)
    arithmetic.fit(int(np.max(rounded)), 24, 'fir_output')
    arithmetic.fit(int(np.min(rounded)), 24, 'fir_output')
    return np.clip(rounded, -(1 << 23), (1 << 23) - 1).astype(np.int32)


def render_int(events, duration, settings=None, body_enabled=True, strict=True):
    settings = settings or Settings.load()
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Duration must be positive and finite')
    arithmetic = Arithmetic(strict)
    voice = BowedVoice(settings, arithmetic)
    tables = voice.tables
    body = BodyFilter(tables, arithmetic, body_enabled)
    frame_count = round(duration * settings.sample_rate)
    if frame_count < 1:
        raise ValueError('Duration is shorter than one output sample')
    event_map = {}
    output = np.empty(frame_count * 2, dtype=np.int64)
    for event in events:
        moment = round(event['time'] * tables.internal_rate)
        if not 0 <= moment < len(output):
            raise ValueError('Event falls outside render')
        event_map.setdefault(moment, []).append(event)
    for sample in range(len(output)):
        for event in event_map.get(sample, ()):
            if event['type'] == 'on':
                voice.note_on(event['note'], event.get('velocity', 100), event.get('legato', False))
            elif event['type'] == 'off':
                voice.note_off()
            else:
                raise ValueError('Unknown event type')
        value = body.process(voice.process() << 4)
        output[sample] = arithmetic.fit(round_shift(value * tables.output_gain, 31), 24, 'pre_fir_audio')
    audio = decimate_int(output, tables, arithmetic)
    return audio, dict(status='integer_sample_model_not_cycle_verified_rtl', integer_signal_path=True,
                       internal_steps=voice.steps, internal_rate=tables.internal_rate,
                       overflow_events=sum(arithmetic.overflows.values()), overflow_by_stage=arithmetic.overflows,
                       peak_waveguide_q20=voice.peak_waveguide_q20, peak_body_state_q30=body.peak_state_q30,
                       delay_capacities=[tables.neck_capacity, tables.bridge_capacity],
                       clipping_samples=int(np.count_nonzero((audio == -(1 << 23)) | (audio == (1 << 23) - 1))),
                       fixed_output_gain=settings.output_gain, body_is_measured=False,
                       hardware_verified=False, resource_usage_measured=False)


def render(events, duration, settings=None, body_enabled=True, **options):
    if options.get('friction_mode', 'lut') != 'lut':
        raise ValueError('Fixed model implements only integer friction lookup')
    audio, statistics = render_int(events, duration, settings, body_enabled)
    return audio.astype(np.float64) / (1 << 23), statistics
