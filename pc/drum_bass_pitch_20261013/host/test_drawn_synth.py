import math
import unittest

import numpy as np

from drawn_synth import (
    BANK_HIGH_KEYS, CMD_DRAW_ENV_DATA, CMD_DRAW_SELECT, CMD_DRAW_STEP,
    CMD_WAVE_DATA, ENV_POINTS, WAVE_POINTS, control_frame, crc16, data_frame,
    envelope_step, make_upload_frames, piano_envelope, position_to_time,
    prepare_envelope, prepare_wave, time_to_position,
)


class DrawnSynthTests(unittest.TestCase):
    def test_standard_crc(self):
        self.assertEqual(crc16(b"123456789"), 0x29B1)

    def test_controls_and_duration(self):
        self.assertEqual(control_frame(CMD_DRAW_SELECT, 1), bytes((0xA5, 0x23, 1, 0, 0, 0x87)))
        self.assertEqual(envelope_step(1400), 3994)
        self.assertEqual(envelope_step(50), 111821)
        self.assertEqual(envelope_step(8000), 699)
        for value in (0, 49, 8001, float("nan")):
            with self.assertRaises(ValueError):
                envelope_step(value)

    def test_signed_word_serialization_and_final_addresses(self):
        words = [0x8000, 0xFFFF, 0, 0x7FFF] * 4
        frame = data_frame(CMD_WAVE_DATA, 8176, words)
        self.assertEqual(frame[:8], bytes((0xA5, 0x21, 0x1F, 0xF0, 0x80, 0, 0xFF, 0xFF)))
        self.assertEqual(int.from_bytes(frame[-2:], "big"), crc16(frame[:-2]))
        self.assertEqual(data_frame(CMD_DRAW_ENV_DATA, 4080, [0] * 16)[2:4], bytes((15, 240)))
        for address in (-16, 1, 8192):
            with self.assertRaises(ValueError):
                data_frame(CMD_WAVE_DATA, address, [0] * 16)

    def test_silence_and_dc_removal(self):
        self.assertEqual(prepare_wave([0.0] * WAVE_POINTS), [0] * 8192)
        self.assertEqual(prepare_wave([0.7] * WAVE_POINTS), [0] * 8192)
        self.assertEqual(prepare_envelope([0] * ENV_POINTS), [0] * ENV_POINTS)
        envelope = prepare_envelope([1] * ENV_POINTS)
        self.assertEqual(envelope[0], 0)
        self.assertEqual(envelope[-1], 0)
        self.assertEqual(envelope[200], 32768)

    def test_octave_antialias_banks(self):
        wave = [math.sin(2 * math.pi * i / WAVE_POINTS) + .35 * math.sin(2 * math.pi * 12 * i / WAVE_POINTS)
                for i in range(WAVE_POINTS)]
        words = prepare_wave(wave)
        signed = np.array([w if w < 32768 else w - 65536 for w in words]).reshape(8, 1024)
        self.assertLessEqual(np.max(abs(signed)), 16384)
        for bank, highest_key in zip(signed, BANK_HIGH_KEYS):
            spectrum = np.abs(np.fft.rfft(bank))
            cutoff = min(511, int(.45 * 48000 / (440 * 2 ** ((highest_key - 69) / 12))))
            self.assertLess(np.max(spectrum[cutoff + 1:]), 100)
            self.assertLess(abs(float(bank.mean())), .1)
        self.assertGreater(np.abs(np.fft.rfft(signed[0]))[12], 100000)
        self.assertLess(np.abs(np.fft.rfft(signed[-1]))[12], 100)

    def test_complete_pair_upload(self):
        frames = make_upload_frames([0.0] * WAVE_POINTS, piano_envelope(), 1400)
        wave_packets = [f for f in frames if f[1] == CMD_WAVE_DATA]
        env_packets = [f for f in frames if f[1] == CMD_DRAW_ENV_DATA]
        self.assertEqual(len(wave_packets), 512)
        self.assertEqual(len(env_packets), 256)
        self.assertEqual([int.from_bytes(f[2:4], "big") for f in wave_packets], list(range(0, 8192, 16)))
        self.assertEqual([int.from_bytes(f[2:4], "big") for f in env_packets], list(range(0, 4096, 16)))
        self.assertEqual([f[1] for f in frames if len(f) == 6], [0x20, 0x22, 0x30, 0x32, 0x24, 0x23])
        for frame in wave_packets + env_packets:
            self.assertEqual(int.from_bytes(frame[-2:], "big"), crc16(frame[:-2]))

    def test_envelope_zoom_maps_real_time(self):
        for duration in (50, 1400, 8000):
            for index in range(101):
                t = duration * index / 100
                self.assertAlmostEqual(position_to_time(time_to_position(t, duration), duration), t, places=8)
        self.assertAlmostEqual(time_to_position(30, 1400), .3)
        self.assertGreater(time_to_position(3, 1400), 3 / 1400)

    def test_preset_onset_and_natural_end(self):
        curve = piano_envelope()
        self.assertEqual((curve[0], curve[-1]), (0, 0))
        self.assertGreater(max(curve), .98)
        self.assertGreater(curve[round(3 / 1400 * 4095)], .9)
        self.assertLess(curve[round(1200 / 1400 * 4095)], .025)


if __name__ == "__main__":
    unittest.main()
