import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from pitch_analysis import pitch_record
from violin_model import ROOT, Settings, baseline, bow_controls, render


def measure(audio, start, end, note, settings, tolerance=10, minimum_rms=0):
    segment = audio[round(start * settings.sample_rate):round(end * settings.sample_rate)]
    result = pitch_record(segment, settings.sample_rate, baseline.midi_frequency(note))
    result.update(window_seconds=[start, end], note=note)
    result['passed'] = (result['cents_error'] is not None and abs(result['cents_error']) <= tolerance
                        and result['correlation'] >= 0.8 and result['spectral_support']
                        and result['steady_rms'] > minimum_rms)
    return result


def static_screen(settings, friction_mode):
    records = []
    for note in range(55, 101):
        for velocity in (1, 32, 64, 100, 127):
            events = [dict(time=0.01, type='on', note=note, velocity=velocity)]
            record = dict(note=note, velocity=velocity, friction_mode=friction_mode,
                          bow_controls=bow_controls(note, velocity, settings))
            try:
                audio, statistics = render(events, 0.8, settings, body_enabled=False, friction_mode=friction_mode)
                windows = [measure(audio, start, end, note, settings, minimum_rms=0.00001)
                           for start, end in ((0.25, 0.50), (0.55, 0.80))]
                record.update(statistics, windows=windows, passed=all(window['passed'] for window in windows))
            except (ValueError, ArithmeticError) as error:
                record.update(passed=False, error=str(error))
            records.append(record)
        print('Static', friction_mode, note, flush=True)
    return records


def long_screen(settings, friction_mode):
    records = []
    for note in (55, 69, 81, 88, 89, 91, 93, 94, 95, 98, 100):
        for velocity in (17, 79, 118):
            record = dict(note=note, velocity=velocity, friction_mode=friction_mode)
            try:
                events = [dict(time=0.01, type='on', note=note, velocity=velocity)]
                audio, statistics = render(events, 2.4, settings, body_enabled=False, friction_mode=friction_mode)
                windows = [measure(audio, start, end, note, settings, minimum_rms=0.00001)
                           for start, end in ((0.25, 0.50), (1.0, 1.3), (2.0, 2.4))]
                record.update(statistics, windows=windows, passed=all(window['passed'] for window in windows))
            except (ValueError, ArithmeticError) as error:
                record.update(passed=False, error=str(error))
            records.append(record)
        print('Long', friction_mode, note, flush=True)
    return records


def dynamic_screen(settings, friction_mode):
    records = []
    for ascending in (True, False):
        notes = list(range(55, 101)) if ascending else list(range(100, 54, -1))
        events = [dict(time=0.1 + index * 0.30, type='on', note=note,
                       velocity=64 if index % 2 else 127, legato=index > 0)
                  for index, note in enumerate(notes)]
        audio, statistics = render(events, events[-1]['time'] + 0.35, settings,
                                   body_enabled=False, friction_mode=friction_mode)
        windows = [measure(audio, event['time'] + 0.17, event['time'] + 0.29, event['note'], settings)
                   for event in events]
        records.append(dict(kind='ascending_legato' if ascending else 'descending_legato',
                            events=events, **statistics, windows=windows,
                            passed=all(window['passed'] for window in windows)))
        print('Legato', friction_mode, ascending, flush=True)
    for note in (55, 69, 88, 93, 95, 100):
        events = []
        for index in range(5):
            events.extend([dict(time=0.1 + index * 0.38, type='on', note=note, velocity=32 + index * 23),
                           dict(time=0.1 + index * 0.38 + 0.24, type='off')])
        audio, statistics = render(events, 2.7, settings, body_enabled=False, friction_mode=friction_mode)
        windows = [measure(audio, event['time'] + 0.12, event['time'] + 0.23, note, settings)
                   for event in events if event['type'] == 'on']
        tail_rms = float(np.sqrt(np.mean(audio[-4800:] ** 2)))
        records.append(dict(kind='repeated_notes', note=note,
                            **statistics, windows=windows, final_100ms_rms=tail_rms,
                            passed=all(window['passed'] for window in windows) and tail_rms < 0.0001))
    return records


def vibrato_screen(friction_mode):
    settings = Settings.load()
    records = []
    for note in (69, 88, 100):
        audio, statistics = render([dict(time=0.01, type='on', note=note, velocity=100)],
                                   2.3, settings, body_enabled=False, friction_mode=friction_mode)
        windows = []
        for start in np.arange(0.60, 2.13, 0.08):
            result = measure(audio, float(start), float(start + 0.08), note, settings, tolerance=35)
            result['expected_center_cents'] = settings.vibrato_cents * math.sin(2 * math.pi * settings.vibrato_hz * (start + 0.04))
            windows.append(result)
        records.append(dict(kind='vibrato_no_octave_screen', note=note,
                            **statistics, windows=windows, passed=all(window['passed'] for window in windows)))
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--friction-mode', choices=('analytic', 'lut'), default='analytic')
    parser.add_argument('--suite', choices=('static', 'long', 'dynamic', 'vibrato', 'all'), default='all')
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise FileExistsError(arguments.output)
    settings = Settings.load(vibrato_cents=0)
    records = []
    for suite, screen in [('static', static_screen), ('long', long_screen), ('dynamic', dynamic_screen)]:
        if arguments.suite in (suite, 'all'):
            records.extend(dict(suite=suite, **record) for record in screen(settings, arguments.friction_mode))
    if arguments.suite in ('vibrato', 'all'):
        records.extend(dict(suite='vibrato', **record) for record in vibrato_screen(arguments.friction_mode))
    failures = [record for record in records if not record['passed']]
    errors = [abs(window['cents_error']) for record in records for window in record.get('windows', [])
              if window['cents_error'] is not None and record['suite'] != 'vibrato']
    report = dict(status='float_validation_not_rtl_or_perceptual_acceptance', suite=arguments.suite,
                  friction_mode=arguments.friction_mode, cases=len(records),
                  passed=len(records) - len(failures), failed=len(failures),
                  maximum_nonvibrato_absolute_cents=max(errors, default=None),
                  full_suite_passed=arguments.suite == 'all' and not failures,
                  full_fixed_point_verified=False, hardware_verified=False,
                  source_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in ROOT.iterdir() if path.suffix in {'.py', '.json'}},
                  failures=failures, records=records)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in {'records', 'failures', 'source_sha256'}}, indent=2))


if __name__ == '__main__':
    main()
