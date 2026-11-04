import argparse
import hashlib
import json
from pathlib import Path
import shutil
import wave

import numpy as np

from pitch_analysis import pitch_record
from violin_model import (ROOT, Settings, baseline, render, friction_table,
                          FRICTION_SHAPE_LOWER, FRICTION_SHAPE_UPPER)


def write_wave(path, audio):
    quantized = np.rint(audio * 32767)
    if np.max(np.abs(quantized), initial=0) >= 32767:
        raise ArithmeticError('Refusing to clip WAV output')
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(48000)
        handle.writeframes(quantized.astype('<i2').tobytes())


def statistics(audio):
    return dict(peak=float(np.max(np.abs(audio))), rms=float(np.sqrt(np.mean(audio ** 2))),
                maximum_sample_step=float(np.max(np.abs(np.diff(audio)))),
                final_100ms_rms=float(np.sqrt(np.mean(audio[-4800:] ** 2))))


def expressive_notes():
    return [dict(time=0.10, type='on', note=69, velocity=100), dict(time=0.55, type='off'),
            dict(time=0.80, type='on', note=69, velocity=90), dict(time=0.98, type='off'),
            dict(time=1.10, type='on', note=69, velocity=100), dict(time=1.28, type='off'),
            dict(time=1.45, type='on', note=69, velocity=110), dict(time=1.63, type='off'),
            dict(time=1.85, type='on', note=69, velocity=100),
            dict(time=2.20, type='on', note=71, velocity=100, legato=True),
            dict(time=2.55, type='on', note=72, velocity=100, legato=True),
            dict(time=2.90, type='on', note=74, velocity=100, legato=True),
            dict(time=3.25, type='on', note=76, velocity=100, legato=True),
            dict(time=3.85, type='off'), dict(time=4.30, type='on', note=69, velocity=95),
            dict(time=5.80, type='off')]


def snapshot_sources(output):
    snapshot = output / 'source_snapshot' / 'experiments'
    for directory, names in [(ROOT, None), (baseline.ROOT, {'reference_model.py', 'config.json', 'LICENSE_STK.txt', 'NOTICE.md'})]:
        target = snapshot / directory.name
        target.mkdir(parents=True)
        for path in directory.iterdir():
            if path.is_file() and path.suffix in {'.py', '.json', '.md', '.txt'} and (names is None or path.name in names):
                shutil.copy2(path, target / path.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=False)
    snapshot_sources(arguments.output)
    settings = Settings.load(vibrato_cents=0)
    longbow = []
    for index, note in enumerate((55, 69, 88, 93, 100)):
        longbow.extend([dict(time=0.15 + index * 1.4, type='on', note=note, velocity=100),
                        dict(time=1.25 + index * 1.4, type='off')])
    high_register = [dict(time=0.1, type='on', note=93, velocity=100), dict(time=1.2, type='off'),
                     dict(time=1.7, type='on', note=100, velocity=127), dict(time=2.8, type='off')]
    dynamics = []
    for index, velocity in enumerate((16, 32, 64, 96, 112, 127)):
        dynamics.extend([dict(time=0.1 + index * 0.9, type='on', note=69, velocity=velocity),
                         dict(time=0.7 + index * 0.9, type='off')])
    records = {}
    for name, events, duration, parameters, renderer, options in [
        ('00_v1c_high_register.wav', high_register, 3.5, baseline.Settings.load(vibrato_cents=0), baseline.render, {}),
        ('01_v2_high_register.wav', high_register, 3.5, settings, render, {}),
        ('02_v2_longbow.wav', longbow, 7.8, settings, render, {}),
        ('03_v2_articulation_vibrato.wav', expressive_notes(), 6.5, Settings.load(), render, {}),
        ('04_v2_velocity_steps.wav', dynamics, 6.4, settings, render, {}),
        ('05_v2_lut_high_register.wav', high_register, 3.5, settings, render, dict(friction_mode='lut')),
    ]:
        audio, diagnostics = renderer(events, duration, parameters, **options)
        write_wave(arguments.output / name, audio)
        measurements = []
        if name in ('00_v1c_high_register.wav', '01_v2_high_register.wav', '02_v2_longbow.wav', '05_v2_lut_high_register.wav'):
            for event in events:
                if event['type'] == 'on':
                    segment = audio[round((event['time'] + 0.5) * 48000):round((event['time'] + 1) * 48000)]
                    measurements.append(dict(note=event['note'], **pitch_record(segment, 48000, baseline.midi_frequency(event['note']))))
        records[name] = dict(**statistics(audio), **diagnostics, events=events, pitch_measurements=measurements)
        print(name, json.dumps(statistics(audio)), flush=True)
    periods = []
    calibration = json.loads((ROOT / 'calibration.json').read_text(encoding='utf-8'))
    rate = settings.sample_rate * settings.oversampling
    pole = np.exp(-2 * np.pi * settings.string_cutoff_hz / rate)
    for note in range(55, 101):
        frequency = baseline.midi_frequency(note) * 2 ** (calibration['cents_correction'][str(note)] / 1200)
        periods.append(round(baseline.matched_period(frequency, rate, settings.bow_position, pole) * (1 << 16)))
    (arguments.output / 'periods_55_100_q16.hex').write_text(''.join(f'{value:07x}\n' for value in periods), encoding='ascii')
    (arguments.output / 'bow_reflection_q18.hex').write_text(''.join(f'{int(value):05x}\n' for value in friction_table()), encoding='ascii')
    report = dict(status='independent_v2_float_audio_not_bitstream', fixed_point_signal_path_verified=False,
                  hardware_verified=False, resource_usage_measured=False, body_is_measured=False,
                  normalizes_each_file=False, adds_white_noise=False, reverb_or_chorus=False,
                  lut_audio_is_float_except_q18_friction_coefficients=True, files=records,
                  friction_rom=dict(entries=1024, width=18, fractional_bits=18,
                                    shaped_velocity_lower=FRICTION_SHAPE_LOWER,
                                    shaped_velocity_upper=FRICTION_SHAPE_UPPER,
                                    clamp_outside_domain=True, compatible_with_v1_addressing=False),
                  period_rom=dict(first_midi_note=55, last_midi_note=100, fractional_bits=16, width=26,
                                  internal_sample_rate=96000, bow_position=settings.bow_position),
                  audio_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in arguments.output.glob('*.wav')},
                  source_sha256={str(path.relative_to(arguments.output / 'source_snapshot')):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (arguments.output / 'source_snapshot').rglob('*') if path.is_file()})
    (arguments.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Saved', arguments.output, flush=True)


if __name__ == '__main__':
    main()
