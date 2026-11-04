import unittest

from guitar_controller import (
    CMD_ENV_BEGIN,
    CMD_ENV_SELECT,
    CMD_TIMBRE,
    CMD_PLUCK,
    ENVELOPE_POINTS,
    MODE_MONO,
    MODE_POLY4,
    TIMBRE_GUITAR,
    TIMBRE_PIANO,
    crc16_ccitt,
    make_command,
    make_envelope_control,
    make_envelope_data,
    make_envelope_upload,
    make_mode_command,
    make_piano_key_command,
    make_piano_pedal_command,
    make_riff_event_frames,
    make_riff_attack_frames,
    riff_tail_ms,
    make_timbre_command,
    note_frequency,
    xor_checksum,
    RIFF_EVENTS,
    RIFF2_EVENTS,
    RIFF2_STEPS,
    RIFF_PROFILES,
    RIFF_STEPS,
    RIFF_VOICINGS,
)


class ProtocolTests(unittest.TestCase):
    def test_command_frame(self):
        frame = make_command(CMD_PLUCK, 6, 20, 110)
        self.assertEqual(frame[:5], bytes((0xA5, 0x02, 0x06, 0x14, 0x6E)))
        self.assertEqual(frame[5], xor_checksum(frame[:5]))

    def test_frequencies_preserve_open_note(self):
        self.assertEqual(note_frequency(6, 0), 82.41)
        self.assertAlmostEqual(note_frequency(1, 12), 659.26, places=10)

    def test_mode_frames(self):
        self.assertEqual(make_mode_command(MODE_MONO), bytes((0xA5, 0x03, 0, 0, 0, 0xA6)))
        self.assertEqual(make_mode_command(MODE_POLY4), bytes((0xA5, 0x03, 1, 0, 0, 0xA7)))

    def test_timbre_frames(self):
        self.assertEqual(
            make_timbre_command(TIMBRE_GUITAR),
            bytes((0xA5, CMD_TIMBRE, 0, 0, 0, 0xA1)),
        )

    def test_direct_88_key_piano_and_pedal_frames(self):
        self.assertEqual(
            make_piano_key_command(60, 100, True),
            bytes((0xA5, 0x05, 60, 100, 1, 0xF9)),
        )
        self.assertEqual(
            make_piano_key_command(60, 100, False),
            bytes((0xA5, 0x05, 60, 100, 0, 0xF8)),
        )
        self.assertEqual(
            make_piano_pedal_command(4),
            bytes((0xA5, 0x06, 4, 0, 0, 0xA7)),
        )
        self.assertEqual(
            make_timbre_command(TIMBRE_PIANO),
            bytes((0xA5, CMD_TIMBRE, 1, 0, 0, 0xA0)),
        )

    def test_every_piano_key_including_a0_and_c8(self):
        frames = [make_piano_key_command(key, 90, True)
                  for key in range(21, 109)]
        self.assertEqual(len(frames), 88)
        self.assertEqual([frame[2] for frame in frames], list(range(21, 109)))
        for frame in frames:
            self.assertEqual(frame[5], xor_checksum(frame[:5]))
        with self.assertRaises(ValueError):
            make_piano_key_command(20, 90, True)
        with self.assertRaises(ValueError):
            make_piano_key_command(109, 90, True)

    def test_envelope_control_frames(self):
        self.assertEqual(
            make_envelope_control(CMD_ENV_BEGIN),
            bytes((0xA5, 0x10, 0, 0, 0, 0xB5)),
        )
        self.assertEqual(
            make_envelope_control(CMD_ENV_SELECT, 1),
            bytes((0xA5, 0x13, 1, 0, 0, 0xB7)),
        )

    def test_envelope_data_crc_and_upload_size(self):
        words = list(range(16))
        frame = make_envelope_data(0x120, words)
        self.assertEqual(len(frame), 38)
        self.assertEqual(frame[:4], bytes((0xA5, 0x11, 0x01, 0x20)))
        self.assertEqual(int.from_bytes(frame[-2:], "big"), crc16_ccitt(frame[:-2]))
        upload = make_envelope_upload([0] * ENVELOPE_POINTS)
        self.assertEqual(len(upload), 6 + 256 * 38 + 6 + 6)

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            make_command(CMD_PLUCK, 0, 0, 110)
        with self.assertRaises(ValueError):
            make_command(CMD_PLUCK, 1, 21, 110)
        with self.assertRaises(ValueError):
            make_command(CMD_PLUCK, 1, 0, 0)
        with self.assertRaises(ValueError):
            make_mode_command(2)
        with self.assertRaises(ValueError):
            make_piano_key_command(20, 100, True)
        with self.assertRaises(ValueError):
            make_piano_pedal_command(5)
        with self.assertRaises(ValueError):
            make_envelope_data(1, [0] * 16)
        with self.assertRaises(ValueError):
            make_envelope_upload([0] * 32)

    def test_hard_rock_riff_is_four_bars_of_valid_power_chords(self):
        self.assertTrue(RIFF_EVENTS)
        self.assertTrue(all(0 <= step < RIFF_STEPS for step, _name, _accent in RIFF_EVENTS))
        self.assertEqual(sorted(step for step, _name, _accent in RIFF_EVENTS),
                         [step for step, _name, _accent in RIFF_EVENTS])
        self.assertTrue(all(name in RIFF_VOICINGS for _step, name, _accent in RIFF_EVENTS))
        self.assertEqual(len(RIFF_EVENTS), 23)
        for name, notes in RIFF_VOICINGS.items():
            frames = make_riff_event_frames(name, 110)
            self.assertEqual(len(frames), 6 * len(notes))
            for offset in range(0, len(frames), 6):
                frame = frames[offset:offset + 6]
                self.assertEqual(frame[0], 0xA5)
                self.assertEqual(frame[1], CMD_PLUCK)
                self.assertEqual(frame[5], xor_checksum(frame[:5]))

    def test_riff_velocity_is_clamped(self):
        self.assertEqual(make_riff_event_frames("E5", 999)[4], 127)
        self.assertEqual(make_riff_event_frames("E5", -10)[4], 1)
        with self.assertRaises(ValueError):
            make_riff_event_frames("not-a-chord", 100)

    def test_slow_riff2_is_simple_four_four_progression(self):
        self.assertEqual(RIFF_PROFILES[2]["subdivision"], 2)
        self.assertLess(RIFF_PROFILES[2]["bpm"], 100)
        self.assertTrue(all(0 <= step < RIFF2_STEPS for step, _name, _accent in RIFF2_EVENTS))
        self.assertEqual(len(RIFF2_EVENTS), 24)
        self.assertTrue(all(name in RIFF_VOICINGS for _step, name, _accent in RIFF2_EVENTS))

    def test_both_riffs_clear_old_voices_before_each_attack(self):
        for riff_number in (1, 2):
            frames = make_riff_attack_frames(riff_number, "E5", 110)
            self.assertEqual(frames[:6], make_mode_command(MODE_POLY4))
            self.assertEqual(frames[6], 0xA5)
            self.assertEqual(frames[7], CMD_PLUCK)
            self.assertGreater(RIFF_PROFILES[riff_number]["tail_min_ms"], 0)

    def test_riff_sustain_control_spans_short_to_previous_natural_tail(self):
        self.assertEqual(riff_tail_ms(1, 0), 190)
        self.assertEqual(riff_tail_ms(2, 0), 290)
        self.assertEqual(riff_tail_ms(1, 126), 1400)
        self.assertIsNone(riff_tail_ms(1, 127))
        natural = make_riff_attack_frames(1, "E5", 110, 127)
        self.assertEqual(natural[1], CMD_PLUCK)  # No prepended mode/voice clear.
        with self.assertRaises(ValueError):
            riff_tail_ms(1, 128)


if __name__ == "__main__":
    unittest.main()
