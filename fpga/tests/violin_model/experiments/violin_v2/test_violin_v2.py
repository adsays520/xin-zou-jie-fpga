from dataclasses import replace
import json
import math
import unittest
from unittest.mock import patch

import numpy as np

from pitch_analysis import estimate_pitch, pitch_record
from violin_model import (BowedVoice, ROOT, Settings, baseline, bow_controls, delay_capacities,
                          load_calibration, render, friction_table, table_reflection,
                          FRICTION_SHAPE_LOWER, FRICTION_SHAPE_UPPER)


class ControlTests(unittest.TestCase):
    def test_control_map_is_bounded_and_monotonic(self):
        settings = Settings.load()
        for note in range(55, 101):
            controls = [bow_controls(note, velocity, settings) for velocity in range(1, 128)]
            self.assertTrue(all(0.70 <= pressure <= 0.95 for pressure, drive, gain in controls))
            self.assertTrue(all(0.143 <= drive <= 0.172 for pressure, drive, gain in controls))
            self.assertTrue(all(controls[index + 1][1] > controls[index][1] for index in range(126)))
            self.assertAlmostEqual(controls[-1][2], 1.27)

    def test_invalid_controls_and_settings(self):
        settings = Settings.load()
        for note, velocity in [(54, 100), (101, 100), (69, 0), (69, 128), (True, 100), (69, False)]:
            with self.assertRaises(ValueError):
                bow_controls(note, velocity, settings)
        for parameters in [dict(oversampling=1), dict(high_register_pressure=1.1),
                           dict(control_smoothing_seconds=0), dict(drive_velocity_min=101),
                           dict(pressure_ramp_end_note=81), dict(pressure_ramp_end_note=88.5)]:
            with self.assertRaises(ValueError):
                replace(settings, **parameters)

    def test_calibration_rejects_stale_or_octave_correction(self):
        table = json.loads((ROOT / 'calibration.json').read_text(encoding='utf-8'))
        self.assertEqual(len(load_calibration(Settings.load())['cents_correction']), 46)
        with self.assertRaises(ValueError):
            load_calibration(Settings.load(bow_position=0.13))
        settings = Settings.load()
        table['cents_correction']['100'] = -1200
        with patch('violin_model.Path.read_text', return_value=json.dumps(table)):
            with self.assertRaises(ValueError):
                load_calibration(settings)

    def test_legato_preserves_memory_phase_and_smooths_controls(self):
        voice = BowedVoice(Settings.load(vibrato_cents=0))
        voice.note_on(81, 64)
        for sample in range(30000):
            voice.process()
        memory = voice.neck.memory.copy()
        phase, age, pressure, gain = voice.vibrato_phase, voice.note_age, voice.pressure, voice.loudness
        voice.note_on(88, 127, legato=True)
        self.assertEqual(voice.neck.memory, memory)
        self.assertEqual((voice.vibrato_phase, voice.note_age, voice.pressure, voice.loudness),
                         (phase, age, pressure, gain))
        voice.process()
        self.assertTrue(pressure < voice.pressure < voice.target_pressure)
        self.assertTrue(gain < voice.loudness < voice.target_loudness)

    def test_zero_state_and_deterministic_release(self):
        for mode in ('analytic', 'lut'):
            voice = BowedVoice(friction_mode=mode)
            self.assertEqual([voice.process() for sample in range(1000)], [0.0] * 1000)
            events = [dict(time=0.01, type='on', note=69), dict(time=0.2, type='off')]
            first, statistics = render(events, 0.7, friction_mode=mode)
            second, unused = render(events, 0.7, friction_mode=mode)
            np.testing.assert_array_equal(first, second)
            self.assertEqual(statistics['clipping_samples'], 0)
            self.assertLess(np.sqrt(np.mean(first[-4800:] ** 2)), 0.0001)

    def test_high_notes_do_not_select_octave(self):
        settings = Settings.load(vibrato_cents=0)
        for mode in ('analytic', 'lut'):
            for note, velocity in [(89, 127), (93, 100), (95, 64), (100, 127)]:
                audio, unused = render([dict(time=0.01, type='on', note=note, velocity=velocity)],
                                       0.8, settings, body_enabled=False, friction_mode=mode)
                pitch = pitch_record(audio[24000:], 48000, baseline.midi_frequency(note))
                self.assertTrue(pitch['spectral_support'])
                self.assertLess(abs(pitch['cents_error']), 10, (mode, note, velocity, pitch))

    def test_compact_delays_are_bit_identical_to_oversized_memory(self):
        settings = Settings.load(vibrato_cents=50)
        compact = BowedVoice(settings, calibrated=False)
        oversized = BowedVoice(settings, calibrated=False)
        oversized.neck = baseline.FractionalDelay(1024)
        oversized.bridge = baseline.FractionalDelay(1024)
        self.assertEqual(delay_capacities(settings), (512, 128))
        compact_values, oversized_values = [], []
        for note in (55, 100, 69, 55):
            compact.note_on(note, 127, legato=True)
            oversized.note_on(note, 127, legato=True)
            for sample in range(40000):
                compact_values.append(compact.process())
                oversized_values.append(oversized.process())
        np.testing.assert_array_equal(compact_values, oversized_values)

    def test_knee_aligned_friction_lut_accuracy(self):
        table = friction_table()
        self.assertEqual(len(table), 1024)
        self.assertTrue(np.all(np.diff(table) <= 0))
        coordinates = np.concatenate((np.linspace(0, 4, 32769),
                                      [FRICTION_SHAPE_LOWER, FRICTION_SHAPE_UPPER]))
        for pressure in (0.0, 0.7, 0.95, 1.0):
            for direction in (-1, 1):
                velocities = direction * coordinates / (5 - 4 * pressure) - 0.001
                error = max(abs(table_reflection(float(velocity), pressure, table) -
                                baseline.bow_reflection(float(velocity), pressure)) for velocity in velocities)
                self.assertLess(error, 0.000014)

    def test_low_note_retrigger_lut_regression(self):
        settings = Settings.load(vibrato_cents=0)
        events = []
        for index in range(5):
            events.extend([dict(time=0.1 + index * 0.38, type='on', note=55, velocity=32 + index * 23),
                           dict(time=0.1 + index * 0.38 + 0.24, type='off')])
        audio, unused = render(events, 2.7, settings, body_enabled=False, friction_mode='lut')
        for index in range(5):
            start = round((0.1 + index * 0.38 + 0.12) * 48000)
            end = round((0.1 + index * 0.38 + 0.23) * 48000)
            measured = pitch_record(audio[start:end], 48000, baseline.midi_frequency(55))
            self.assertLess(abs(measured['cents_error']), 10)


class PitchTests(unittest.TestCase):
    def test_broad_frequency_search_and_spectral_refinement(self):
        moments = np.arange(19200) / 48000
        for frequency in (196.0, 440.0, 1318.51, 2637.02, 5346.56):
            audio = np.sin(2 * math.pi * frequency * moments) + 0.2 * np.sin(4 * math.pi * frequency * moments)
            result = estimate_pitch(audio, 48000)
            self.assertTrue(result['spectral_support'])
            self.assertLess(abs(1200 * math.log2(result['frequency'] / frequency)), 0.1)

    def test_strong_second_harmonic_keeps_supported_fundamental(self):
        moments = np.arange(19200) / 48000
        audio = 0.4 * np.sin(2 * math.pi * 440 * moments) + np.sin(2 * math.pi * 880 * moments)
        self.assertAlmostEqual(estimate_pitch(audio, 48000)['frequency'], 440, delta=0.05)
        self.assertIsNone(estimate_pitch(np.zeros(1000), 48000)['frequency'])


if __name__ == '__main__':
    unittest.main()
