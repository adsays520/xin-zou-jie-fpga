import math
import unittest

import numpy as np

from reference_model import (Settings, FractionalDelay, BowedVoice, BodyFilter, bow_reflection,
                             friction_table, table_reflection, matched_period, midi_frequency,
                             decimator_coefficients, decimate, render)
from design_contract import contract
from render_prototype import estimate_pitch


class ViolinReferenceTests(unittest.TestCase):
    def test_pitch_detector_does_not_fold_high_octave_into_note_range(self):
        timeline = np.arange(24000) / 48000
        signal = np.sin(2 * math.pi * 5300 * timeline)
        measured = estimate_pitch(signal, 48000)
        self.assertGreater(measured['frequency'], 5000)
        self.assertLess(measured['frequency'], 5600)
        signal = 0.25 * np.sin(2 * math.pi * 440 * timeline) + np.sin(2 * math.pi * 880 * timeline)
        measured = estimate_pitch(signal, 48000)
        self.assertLess(abs(1200 * math.log2(measured['frequency'] / 440)), 2)

    def test_hardware_reservation_is_only_a_design_contract(self):
        design = contract()
        self.assertEqual(design['reserved_clocks'], 832)
        self.assertEqual(design['reserve_clocks'], 209)
        self.assertFalse(design['physical_bsram_measured'])
        self.assertFalse(design['timing_measured'])

    def test_default_static_pitch_sample_points(self):
        for oversampling in (1, 2):
            for note in (55, 69, 88, 100):
                settings = Settings.load(oversampling=oversampling, vibrato_cents=0)
                audio, statistics = render([dict(time=0.01, type='on', note=note)], 0.60,
                                           settings, body_enabled=False)
                measured = estimate_pitch(audio[round(0.30 * settings.sample_rate):], settings.sample_rate)
                self.assertIsNotNone(measured['frequency'])
                cents = 1200 * math.log2(measured['frequency'] / midi_frequency(note))
                self.assertLess(abs(cents), 10, (oversampling, note, cents))
                self.assertLessEqual(measured['correlation'], 1)
                self.assertGreater(measured['correlation'], 0.8)

    def test_fractional_delay_wrap_and_impulse(self):
        delay = FractionalDelay(16)
        output = []
        for index in range(50):
            output.append(delay.read(3.25))
            delay.write(1.0 if index == 17 else 0.0)
        expected = np.zeros(50)
        expected[20:22] = [0.75, 0.25]
        np.testing.assert_array_equal(output, expected)

    def test_delay_rejects_noncausal_and_oversized(self):
        delay = FractionalDelay(16)
        for value in (-1, 0, 0.9, 15, math.nan):
            with self.assertRaises(ValueError):
                delay.read(value)

    def test_settings_reject_invalid_controls(self):
        for changes in ({'bow_position': 0.0}, {'bow_pressure': math.nan}, {'oversampling': 4},
                        {'attack_seconds': 0}, {'string_gain': 1}, {'decimator_taps': 94}):
            with self.assertRaises(ValueError):
                Settings.load(**changes)

    def test_friction_table_range_and_error(self):
        table = friction_table()
        self.assertEqual(len(table), 1024)
        self.assertTrue(np.all(np.diff(table) <= 0))
        self.assertGreaterEqual(table.min(), round(0.01 * (1 << 18)))
        self.assertLessEqual(table.max(), round(0.98 * (1 << 18)))
        maximum_error = max(abs(bow_reflection(value, pressure) - table_reflection(value, pressure, table))
                            for pressure in (0.0, 0.5, 1.0) for value in np.linspace(-5, 5, 20001))
        self.assertLess(maximum_error, 0.004)

    def test_phase_matched_roundtrip(self):
        for rate in (48000, 96000):
            pole = math.exp(-2 * math.pi * 4200 / rate)
            for frequency in (160, midi_frequency(55), 440, midi_frequency(100), 3200):
                for position in (0.08, 0.127236, 0.30):
                    period = matched_period(frequency, rate, position, pole)
                    angular = 2 * math.pi * frequency / rate
                    total_phase = math.atan2(pole * math.sin(angular), 1 - pole * math.cos(angular))
                    for delay in (period * position, period * (1 - position)):
                        self.assertGreaterEqual(delay, 1)
                        whole = int(delay)
                        fraction = delay - whole
                        total_phase += whole * angular + math.atan2(fraction * math.sin(angular),
                                                                    1 - fraction + fraction * math.cos(angular))
                    self.assertAlmostEqual(total_phase, 2 * math.pi, places=8)

    def test_quantized_body_poles(self):
        for rate in (48000, 96000):
            for coefficients in BodyFilter(rate).coefficients:
                quantized = np.rint(np.array(coefficients) * (1 << 22)) / (1 << 22)
                self.assertTrue(np.all(np.abs(quantized) < 2))
                self.assertLess(np.max(np.abs(np.roots([1, *quantized[3:]]))), 1)

    def test_fir_response_and_symmetry(self):
        taps = decimator_coefficients(Settings.load())
        np.testing.assert_allclose(taps, taps[::-1], atol=1e-15)
        self.assertAlmostEqual(float(taps.sum()), 1)
        response = np.abs(np.fft.rfft(taps, 65536))
        frequencies = np.fft.rfftfreq(65536, 1 / 96000)
        self.assertLess(20 * math.log10(float(response[frequencies >= 24000].max())), -65)
        self.assertLess(float(np.max(np.abs(20 * np.log10(response[frequencies <= 18000])))), 0.1)

    def test_decimator_impulse_is_causal(self):
        impulse = np.zeros(300)
        impulse[50] = 1
        settings = Settings.load()
        result = decimate(impulse, settings)
        expected = np.convolve(impulse, decimator_coefficients(settings))[:len(impulse)][1::2]
        np.testing.assert_array_equal(result, expected)
        np.testing.assert_array_equal(result[:25], 0)

    def test_legato_keeps_history_and_lfo(self):
        voice = BowedVoice(Settings.load(vibrato_cents=0))
        voice.note_on(69)
        for index in range(20000):
            voice.process()
        history = list(voice.neck.memory)
        phase = voice.vibrato_phase
        age = voice.note_age
        voice.note_on(72, legato=True)
        self.assertEqual(history, voice.neck.memory)
        self.assertEqual(phase, voice.vibrato_phase)
        self.assertEqual(age, voice.note_age)

    def test_repeated_notes_are_deterministic(self):
        events = [{'time': 0.01, 'type': 'on', 'note': 69}, {'time': 0.20, 'type': 'off'},
                  {'time': 0.25, 'type': 'on', 'note': 72}, {'time': 0.40, 'type': 'off'}]
        settings = Settings.load(oversampling=1, vibrato_cents=0)
        first, statistics = render(events, 0.6, settings)
        second, repeated = render(events, 0.6, settings)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(statistics, repeated)
        self.assertGreater(np.max(np.abs(first)), 0.01)
        self.assertEqual(statistics['clipping_samples'], 0)

    def test_silent_reset_without_bow(self):
        audio, statistics = render([], 0.05)
        np.testing.assert_array_equal(audio, 0)
        self.assertEqual(statistics['peak_internal'], 0)

    def test_controls_reject_invalid_notes(self):
        voice = BowedVoice()
        for note, velocity in ((54, 100), (101, 100), (69, 0), (69, 128)):
            with self.assertRaises(ValueError):
                voice.note_on(note, velocity)


if __name__ == '__main__':
    unittest.main()
