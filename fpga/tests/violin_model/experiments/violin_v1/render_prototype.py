import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import wave

import numpy as np

from design_contract import contract
from reference_model import (ROOT, Settings, render, midi_frequency, friction_table,
                             decimator_coefficients, matched_period, BodyFilter)


def estimate_pitch(audio, sample_rate):
    centered = audio - np.mean(audio)
    energy = float(np.dot(centered, centered))
    if energy < 1e-12:
        return dict(frequency=None, correlation=0.0)
    fft_size = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_size)
    correlation = np.fft.irfft(np.abs(spectrum) ** 2, fft_size)[:len(centered)]
    prefix_energy = np.concatenate(([0.0], np.cumsum(centered ** 2)))
    lags = np.arange(len(centered))
    denominator = np.sqrt(prefix_energy[len(centered) - lags] * (prefix_energy[-1] - prefix_energy[lags]))
    correlation = np.clip(correlation / np.maximum(denominator, 1e-30), -1, 1)
    minimum_lag = math.ceil(sample_rate / 16000)
    maximum_lag = min(len(centered) - 2, math.floor(sample_rate / 100))
    peaks = [index for index in range(minimum_lag, maximum_lag + 1)
             if correlation[index] > correlation[index - 1] and correlation[index] >= correlation[index + 1]]
    if not peaks:
        return dict(frequency=None, correlation=0.0)
    best = max(float(correlation[index]) for index in peaks)
    selected = next(index for index in peaks if correlation[index] >= 0.95 * best)
    left, center, right = correlation[selected - 1:selected + 2]
    denominator = left - 2 * center + right
    offset = 0.0 if abs(denominator) < 1e-15 else 0.5 * (left - right) / denominator
    return dict(frequency=sample_rate / (selected + offset), correlation=float(center))


def write_wave(path, audio, sample_rate):
    quantized = np.rint(audio * 32767)
    assert np.max(np.abs(quantized), initial=0) < 32767
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(quantized.astype('<i2').tobytes())


def audio_statistics(audio, sample_rate):
    return dict(duration_seconds=len(audio) / sample_rate,
                peak=float(np.max(np.abs(audio), initial=0)),
                rms=float(np.sqrt(np.mean(audio ** 2))), dc=float(np.mean(audio)),
                maximum_sample_step=float(np.max(np.abs(np.diff(audio)), initial=0)),
                rms_final_100ms=float(np.sqrt(np.mean(audio[-sample_rate // 10:] ** 2))))


def reference_notes():
    events = []
    for moment, note in [(0.15, 55), (1.75, 69), (3.35, 88)]:
        events.append(dict(time=moment, type='on', note=note, velocity=100))
        events.append(dict(time=moment + 1.10, type='off'))
    return events


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


def render_files(output):
    records = {}
    for name, settings, events, duration in [
        ('01_longbow_internal48k.wav', Settings.load(oversampling=1, vibrato_cents=0), reference_notes(), 5.5),
        ('02_longbow_internal96k.wav', Settings.load(oversampling=2, vibrato_cents=0), reference_notes(), 5.5),
        ('03_articulation_vibrato96k.wav', Settings.load(oversampling=2), expressive_notes(), 6.5),
    ]:
        audio, voice_stats = render(events, duration, settings)
        write_wave(output / name, audio, settings.sample_rate)
        statistics = dict(**audio_statistics(audio, settings.sample_rate), **voice_stats,
                          events=events, sample_rate=settings.sample_rate, oversampling=settings.oversampling)
        if name.startswith(('01_', '02_')):
            statistics['pitch_measurements'] = []
            for onset, note in [(0.15, 55), (1.75, 69), (3.35, 88)]:
                segment = audio[round((onset + 0.50) * settings.sample_rate):round((onset + 1.00) * settings.sample_rate)]
                measured = estimate_pitch(segment, settings.sample_rate)
                target = midi_frequency(note)
                error = None if measured['frequency'] is None else 1200 * math.log2(measured['frequency'] / target)
                statistics['pitch_measurements'].append(dict(note=note, target_hz=target,
                    **measured, cents_error=error, within_10_cents=error is not None and abs(error) <= 10))
        records[name] = statistics
        print(name, json.dumps({key: value for key, value in statistics.items() if key != 'events'}), flush=True)
    return records


def parameter_screen(output):
    records = []
    for oversampling in (1, 2):
        for note in (55, 69, 88, 100):
            for pressure in (0.4, 0.55, 0.7):
                settings = Settings.load(oversampling=oversampling, bow_pressure=pressure, vibrato_cents=0)
                events = [dict(time=0.01, type='on', note=note, velocity=100)]
                audio, statistics = render(events, 0.60, settings, body_enabled=False)
                pitch = estimate_pitch(audio[round(0.30 * settings.sample_rate):], settings.sample_rate)
                error = None if pitch['frequency'] is None else 1200 * math.log2(pitch['frequency'] / midi_frequency(note))
                record = dict(oversampling=oversampling, note=note, pressure=pressure, **pitch,
                              cents_error=error, **statistics, **audio_statistics(audio, settings.sample_rate))
                record['pitch_screen_passed'] = error is not None and abs(error) <= 10 and pitch['correlation'] >= 0.8
                records.append(record)
    (output / 'parameter_screen.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    return dict(cases=len(records), finite_unclipped_cases=len(records),
                pitch_cases_passed=sum(record['pitch_screen_passed'] for record in records),
                note='Numerical screening only; failed pitch cases remain visible and are not normalized away.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument('--screen', action='store_true')
    arguments = parser.parse_args()
    output = arguments.output or ROOT / 'results' / datetime.now().strftime('%Y%m%d_%H%M%S')
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output / 'source_snapshot'
    snapshot.mkdir()
    for path in ROOT.iterdir():
        if path.is_file() and path.suffix in {'.py', '.json', '.md', '.txt'}:
            shutil.copy2(path, snapshot / path.name)
    records = render_files(output)
    table = friction_table()
    (output / 'bow_reflection_q18.hex').write_text(''.join(f'{int(value):05x}\n' for value in table), encoding='ascii')
    coefficients = {}
    for oversampling in (1, 2):
        settings = Settings.load(oversampling=oversampling)
        rate = settings.sample_rate * oversampling
        pole = math.exp(-2 * math.pi * settings.string_cutoff_hz / rate)
        coefficients[str(rate)] = dict(body=BodyFilter(rate).coefficients,
            body_q22=np.rint(np.array(BodyFilter(rate).coefficients) * (1 << 22)).astype(np.int64).tolist(),
            decimator=decimator_coefficients(settings).tolist(),
            note_periods_q16={str(note): round(matched_period(midi_frequency(note), rate,
                settings.bow_position, pole) * (1 << 16)) for note in range(52, 103)})
    (output / 'coefficient_candidates.json').write_text(json.dumps(coefficients, indent=2) + '\n', encoding='utf-8')
    report = dict(status='float_prototype_not_rtl_or_hardware', perceptual_quality_verified=False,
                  fixed_point_signal_path_verified=False, bsram_or_dsp_measured=False,
                  hardware_verified=False, uses_real_violin_recordings=False,
                  normalizes_each_file=False, added_white_noise=False, reverb_or_chorus=False,
                  files=records, frame_design=contract())
    measurements = [measurement for record in records.values() for measurement in record.get('pitch_measurements', [])]
    report['demo_static_pitch_cases_passed'] = sum(measurement['within_10_cents'] for measurement in measurements)
    report['demo_static_pitch_case_count'] = len(measurements)
    if arguments.screen:
        report['parameter_screen'] = parameter_screen(output)
    report['source_sha256'] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in sorted(ROOT.iterdir()) if path.is_file() and path.suffix in {'.py', '.json', '.md', '.txt'}}
    report['audio_sha256'] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.glob('*.wav'))}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Saved experimental prototype:', output, flush=True)
    if arguments.screen:
        print(json.dumps(report['parameter_screen'], indent=2), flush=True)


if __name__ == '__main__':
    main()
