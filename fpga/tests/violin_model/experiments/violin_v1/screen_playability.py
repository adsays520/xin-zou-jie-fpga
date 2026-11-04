import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from reference_model import ROOT, Settings, midi_frequency, render
from render_prototype import estimate_pitch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--oversampling', type=int, choices=(1, 2), default=2)
    parser.add_argument('--velocities', type=int, nargs='+', default=[64, 100, 127])
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    assert not arguments.output.exists()
    assert all(1 <= velocity <= 127 for velocity in arguments.velocities)
    settings = Settings.load(oversampling=arguments.oversampling, vibrato_cents=0)
    records = []
    for note in range(55, 101):
        for velocity in arguments.velocities:
            record = dict(note=note, velocity=velocity, pressure=settings.bow_pressure,
                          bow_position=settings.bow_position, oversampling=settings.oversampling)
            try:
                events = [dict(time=0.01, type='on', note=note, velocity=velocity)]
                audio, statistics = render(events, 0.60, settings, body_enabled=False)
                steady = audio[round(0.30 * settings.sample_rate):]
                pitch = estimate_pitch(steady, settings.sample_rate)
                cents = None if pitch['frequency'] is None else 1200 * math.log2(pitch['frequency'] / midi_frequency(note))
                record.update(statistics, **pitch, cents_error=cents, steady_rms=float(np.sqrt(np.mean(steady ** 2))))
                record['passed'] = (cents is not None and abs(cents) <= 10 and pitch['correlation'] >= 0.8
                                    and record['steady_rms'] > 0.005)
            except (ArithmeticError, ValueError) as failure:
                record.update(passed=False, error=str(failure))
            records.append(record)
        print('Screened MIDI', note, flush=True)
    failures = [record for record in records if not record['passed']]
    report = dict(status='static_float_playability_screen_not_perceptual_validation',
                  target_note_range=[55, 100], oversampling=settings.oversampling,
                  cases=len(records), passed=len(records) - len(failures), failed=len(failures),
                  full_range_validated=not failures, legato_or_vibrato_validated=False,
                  failure_cases=failures, cases_detail=records,
                  source_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (ROOT / 'reference_model.py', ROOT / 'config.json',
                                              ROOT / 'render_prototype.py', Path(__file__))})
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in {'cases_detail', 'failure_cases', 'source_sha256'}}, indent=2))


if __name__ == '__main__':
    main()
