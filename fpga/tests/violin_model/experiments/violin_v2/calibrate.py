import argparse
import json
from pathlib import Path

from pitch_analysis import pitch_record
from violin_model import Settings, baseline, calibration_signature, render


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise FileExistsError(arguments.output)
    settings = Settings.load(vibrato_cents=0)
    records = []
    corrections = {}
    for note in range(55, 101):
        events = [dict(time=0.01, type='on', note=note, velocity=90)]
        audio, statistics = render(events, 1.4, settings, body_enabled=False, calibrated=False)
        measured = pitch_record(audio[round(0.9 * settings.sample_rate):], settings.sample_rate,
                                baseline.midi_frequency(note))
        error = measured['cents_error']
        if error is None or abs(error) > 40 or measured['correlation'] < 0.8 or not measured['spectral_support']:
            raise ArithmeticError(f'MIDI {note} has no usable fundamental: {measured}')
        corrections[str(note)] = -error
        records.append(dict(note=note, velocity=90, **measured, **statistics))
        print('Calibrated', note, round(-error, 4), flush=True)
    report = dict(status='offline_float_residual_tuning_not_octave_repair',
                  signature=calibration_signature(settings), cents_correction=corrections,
                  training_velocity=90, training_window_seconds=[0.9, 1.4],
                  held_out_validation_required=True, records=records)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
