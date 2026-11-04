import ctypes
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TCC = Path(os.environ.get("TOUCH_TEST_TCC", ROOT / "tests/tools/tcc/tcc.exe"))


class TouchRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = ROOT / "tests/build"
        build.mkdir(exist_ok=True)
        library = build / f"touch_sim_{os.getpid()}.dll"
        shared = ROOT.parent.parent / "esp32C3/Bluedroid_Connection/main"
        command = [str(TCC), "-shared", "-o", str(library),
                   "-include", str(ROOT / "tests/include/idf_test.h"),
                   "-I", str(ROOT / "tests/include"), "-I", str(ROOT / "main"), "-I", str(shared),
                   str(ROOT / "tests/touch_sim.c"), str(ROOT / "main/note_trace.c"),
                   str(shared / "touch_layout.c")]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        cls.sim = ctypes.CDLL(str(library))
        cls.sim.sim_note_at.restype = ctypes.c_char_p

    def setUp(self):
        self.sim.sim_reset(1)

    def ticks(self, count, elapsed=5000):
        return [self.sim.sim_tick(elapsed) for unused in range(count)]

    def notes(self):
        return [self.sim.sim_note_at(index).decode() for index in range(self.sim.sim_note_count())]

    def ack(self, keys=(), instrument=1, hall=False, enabled=True, sequence=1):
        bitmap = (ctypes.c_uint8 * 16)()
        for key in keys:
            bitmap[(key - 1) // 8] |= 1 << ((key - 1) % 8)
        self.sim.sim_ack(bitmap, instrument, hall, enabled, sequence)

    def samples(self, chip, values):
        for value in values:
            self.sim.sim_button_sample(chip, value)

    def test_guard_rejects_successful_spikes_without_press_or_probe_backoff(self):
        self.samples(0, (0xFF01, 0, 0x0100, 0, 0xFF01, 0))
        self.ticks(3)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.assertEqual(self.sim.sim_disagreements(0), 3)
        self.assertEqual(self.sim.sim_online(0), 1)
        self.assertEqual(self.sim.sim_read_count(0, 0), 0)
        self.assertEqual(self.notes(), [])

    def test_two_adjacent_bad_reads_do_not_confirm_nine_keys(self):
        self.samples(0, (0xFF01, 0xFF01, 0, 0))
        self.ticks(3)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.assertEqual(self.notes(), [])

    def test_overlapping_corrupt_words_do_not_confirm_shared_bit(self):
        self.samples(0, (0x0100, 0, 0xFF01, 0))
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.assertEqual(self.notes(), [])

    def test_guard_does_not_add_reads_to_stable_keys(self):
        self.sim.sim_buttons(0, 1)
        self.ticks(2)
        self.assertEqual(self.sim.sim_read_count(0, 2), 4)
        self.ticks(10)
        self.assertEqual(self.sim.sim_read_count(0, 2), 14)
        self.assertEqual(self.sim.sim_state(0), 1)

    def test_failed_verification_read_cannot_become_a_press(self):
        self.samples(0, (1, 0x10000, 1, 1, 1, 1))
        self.ticks(1)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.ticks(1)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.ticks(1)
        self.assertEqual(self.sim.sim_state(0), 1)

    def test_real_chord_change_between_pair_reads_is_retried_not_blacklisted(self):
        self.sim.sim_buttons(0, 3)
        self.samples(0, (1, 3))
        self.ticks(1)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(0), 3)

    def test_real_presses_on_all_active_boards_still_confirm(self):
        for chip in tuple(range(8)):
            self.sim.sim_buttons(chip, 1)
        self.ticks(8)
        for chip in tuple(range(8)):
            self.assertEqual(self.sim.sim_state(chip), 1)
        self.assertEqual(self.sim.sim_mask(), 0xFF)

    def test_four_consistent_bad_reads_are_not_claimed_detectable(self):
        self.samples(0, (0xFF01,) * 4)
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(0), 0xFF01)

    def test_guard_adds_no_fixed_sleep_and_confirms_single_key_within_model_budget(self):
        started = self.sim.sim_time_us()
        self.sim.sim_buttons(0, 1)
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(0), 1)
        self.assertLessEqual(self.sim.sim_confirmed_us(0) - started, 20000)

    def test_multi_board_change_confirmation_stays_below_stale_in_model(self):
        started = self.sim.sim_time_us()
        for chip in tuple(range(8)):
            self.sim.sim_buttons(chip, 1)
        for unused in range(6):
            self.ticks(1)
            if all(self.sim.sim_state(chip) == 1 for chip in tuple(range(8))):
                break
        self.assertTrue(all(self.sim.sim_state(chip) == 1 for chip in tuple(range(8))))
        self.assertLess(self.sim.sim_time_us() - started, 60000)

    def test_readable_key_log_only_follows_confirmed_edges(self):
        self.sim.sim_buttons(0, 1 << 8)
        self.ticks(1)
        self.assertEqual(self.notes(), [])
        self.ticks(1)
        self.assertEqual(self.notes(), [
            "NOTE_KEY: DOWN chip=0 cs=8 key=4 string=3 fret=0 reason=FILTER"])
        self.ticks(4)
        self.assertEqual(len(self.notes()), 1)
        self.sim.sim_buttons(0, 0)
        self.ticks(2)
        self.assertIn("NOTE_KEY: UP chip=0 cs=8 key=4", self.notes()[-1])

    def test_safety_release_and_retrigger_have_readable_reason(self):
        self.sim.sim_buttons(0, 1 << 8)
        self.ticks(2)
        self.ticks(1, 65000)
        self.assertIn("UP chip=0 cs=8 key=4", self.notes()[-1])
        self.assertIn("reason=STALE", self.notes()[-1])
        self.ticks(1)
        self.assertIn("DOWN chip=0 cs=8 key=4", self.notes()[-1])
        self.assertIn("reason=FILTER", self.notes()[-1])

    def test_offline_release_is_not_labelled_finger_release(self):
        self.sim.sim_buttons(0, 1 << 8)
        self.ticks(2)
        self.sim.sim_fail(0, 3, 500)
        self.ticks(3)
        self.assertIn("UP chip=0 cs=8 key=4", self.notes()[-1])
        self.assertIn("reason=OFFLINE", self.notes()[-1])

    def test_ack_decodes_board_zero_and_one_pitch_and_release(self):
        self.ack((4, 22), sequence=18)
        self.assertIn("DOWN chip=0 cs=8 key=4 note=G3 midi=55 instrument=PIANO role=NOTE_ON seq=18",
                      self.notes()[1])
        self.assertIn("DOWN chip=1 cs=8 key=22 note=A#3 midi=58", self.notes()[2])
        count = len(self.notes())
        self.ack((4, 22), sequence=19)
        self.assertEqual(len(self.notes()), count)
        self.ack(sequence=20)
        self.assertIn("UP chip=0 cs=8 key=4 note=G3 midi=55 instrument=PIANO role=NOTE_OFF seq=20",
                      self.notes()[-2])

    def test_key_numbers_above_64_and_126_are_decoded(self):
        self.ack((65, 126))
        self.assertIn("chip=4 cs=8 key=65 note=A4 midi=69", self.notes()[1])
        self.assertIn("chip=7 cs=0 key=126 note=C6 midi=84", self.notes()[2])

    def test_ack_idle_does_not_emit_note_events(self):
        self.ack()
        self.ack(sequence=2)
        self.assertEqual(len(self.notes()), 1)
        self.assertTrue(self.notes()[0].startswith("NOTE_MODE:"))

    def test_mode_changes_are_not_fabricated_note_edges(self):
        self.ack((4,))
        count = len(self.notes())
        self.ack((4,), instrument=0)
        self.assertEqual(len(self.notes()), count + 1)
        self.assertIn("NOTE_MODE: instrument=GUITAR", self.notes()[-1])

    def test_non_piano_roles_do_not_claim_note_off_or_all_violin_keys_play(self):
        self.ack((4,), instrument=0)
        self.assertIn("role=PLUCK", self.notes()[-1])
        self.ack(instrument=0)
        self.assertIn("role=KEY_RELEASE", self.notes()[-1])
        self.ack((4, 5), instrument=3)
        self.assertIn("key=4 note=D4 midi=62", self.notes()[-2])
        self.assertTrue(all("role=MONO_CANDIDATE" in item for item in self.notes()[-2:]))

    def test_bass_ignores_high_two_strings_and_uses_low_octave(self):
        self.ack((1, 5), instrument=2)
        self.assertIn("note=E1 midi=28", self.notes()[-2])
        self.assertIn("note=NONE midi=-1 instrument=BASS role=BASS_UNUSED", self.notes()[-1])

    def test_pick_mode_and_disabled_touch_are_not_reported_as_note_on(self):
        self.ack((4,), hall=True)
        self.assertIn("role=FRET_SELECT", self.notes()[-1])
        self.ack(hall=True)
        self.ack((4,), enabled=False)
        self.assertIn("role=TOUCH_DISABLED", self.notes()[-1])

    def test_existing_filter_regressions(self):
        self.assertEqual(self.sim.sim_filter_test(), 1)

    def test_probe_delay_is_bounded_to_200ms(self):
        self.assertEqual(self.sim.sim_probe_limit_test(), 1)

    def test_two_good_samples_confirm_real_press_and_release(self):
        self.sim.sim_buttons(0, 1)
        self.ticks(1)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.ticks(1)
        self.assertEqual(self.sim.sim_state(0), 1)
        self.sim.sim_buttons(0, 0)
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(0), 0)

    def test_transient_failure_does_not_disconnect(self):
        self.sim.sim_fail(0, 1, 500)
        self.ticks(1)
        self.assertEqual(self.sim.sim_online(0), 1)
        self.ticks(3)
        self.assertEqual(self.sim.sim_mask(), 0xFF)
        self.assertEqual(self.sim.sim_read_count(0, 0), 0)

    def test_stale_safety_release_does_not_enter_probe_backoff(self):
        self.sim.sim_buttons(0, 1)
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(0), 1)
        self.ticks(1, 65000)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.assertEqual(self.sim.sim_online(0), 1)
        self.assertEqual(self.sim.sim_read_count(0, 0), 0)
        self.ticks(1)
        self.assertEqual(self.sim.sim_state(0), 1)

    def test_busy_bus_releases_keys_without_device_fail_strikes(self):
        self.sim.sim_buttons(0, 1)
        self.ticks(2)
        reads = self.sim.sim_read_count(0, 2)
        self.sim.sim_bus(0)
        self.ticks(5, 20000)
        self.assertEqual(self.sim.sim_mask(), 0)
        self.assertEqual(self.sim.sim_read_count(0, 2), reads)
        self.assertEqual(self.sim.sim_online(0), 1)
        self.sim.sim_bus(1)
        self.ticks(6)
        self.assertEqual(self.sim.sim_mask(), 0xFF)
        self.assertEqual(self.sim.sim_state(0), 1)
        self.assertEqual(self.sim.sim_read_count(0, 0), 0)

    def test_slow_failure_yields_to_other_boards(self):
        self.sim.sim_fail(0, -1, 10000)
        costs = self.ticks(80)
        self.assertLessEqual(max(costs), 15000)
        for chip in tuple(range(1, 8)):
            self.assertGreater(self.sim.sim_read_count(chip, 2), 35)
            self.assertEqual(self.sim.sim_read_count(chip, 0), 0)
            self.assertEqual(self.sim.sim_online(chip), 1)
        self.assertEqual(self.sim.sim_mask(), 0xFE)

    def test_master_bus_recovery_does_not_wait_forever(self):
        self.sim.sim_recoverable_bus(1)
        self.sim.sim_bus(0)
        self.ticks(12)
        self.assertEqual(self.sim.sim_mask(), 0xFF)
        self.assertEqual(self.sim.sim_bus_resets(), 1)
        self.assertEqual(self.sim.sim_read_count(0, 0), 0)

    def test_persistently_low_bus_recovery_is_rate_limited(self):
        self.sim.sim_bus(0)
        self.ticks(200)
        self.assertGreaterEqual(self.sim.sim_bus_resets(), 1)
        self.assertLessEqual(self.sim.sim_bus_resets(), 3)
        self.assertEqual(self.sim.sim_mask(), 0)
        self.assertEqual(self.sim.sim_online(0), 1)

    def test_returned_chip2_is_probed_and_keys_confirm(self):
        self.sim.sim_reset(0)
        self.ticks(120)
        self.assertGreater(self.sim.sim_read_count(2, 0), 0)
        self.assertGreater(self.sim.sim_read_count(2, 1), 0)
        self.assertGreater(self.sim.sim_read_count(2, 2), 0)
        self.sim.sim_buttons(2, 1 << 12)
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(2), 1 << 12)
        self.assertEqual(self.sim.sim_mask(), 0xFF)

    def test_bad_id_cannot_rejoin(self):
        self.sim.sim_reset(0)
        self.sim.sim_id(0, 0xFFFF)
        self.ticks(120)
        self.assertEqual(self.sim.sim_mask(), 0xFE)
        self.assertEqual(self.sim.sim_read_count(0, 1), 0)
        self.assertEqual(self.sim.sim_read_count(0, 2), 0)

    def test_three_failures_require_strict_reverification(self):
        self.sim.sim_fail(0, 3, 500)
        self.ticks(3)
        self.assertEqual(self.sim.sim_online(0), 0)
        self.ticks(16)
        self.assertEqual(self.sim.sim_online(0), 1)
        self.assertGreater(self.sim.sim_read_count(0, 0), 0)
        self.assertGreater(self.sim.sim_read_count(0, 1), 0)

    def test_all_pressed_is_not_mistaken_for_corruption(self):
        self.sim.sim_buttons(0, 0xFFFF)
        self.ticks(2)
        self.assertEqual(self.sim.sim_state(0), 0xFFFF)

    def test_diagnostic_work_is_split_between_regular_polls(self):
        self.sim.sim_diag()
        self.ticks(150)
        for chip in tuple(range(8)):
            self.assertEqual(self.sim.sim_read_count(chip, 3), 16)
            self.assertGreaterEqual(self.sim.sim_read_count(chip, 2), 150)
            self.assertEqual(self.sim.sim_read_count(chip, 0), 0)

    def test_polling_never_calls_uart_driver(self):
        self.sim.sim_fail(0, -1, 500)
        self.sim.sim_diag()
        self.ticks(150)
        self.assertEqual(self.sim.sim_uart_writes(), 0)

    def test_trace_does_not_generate_edges_or_extra_reads_while_idle(self):
        raw = self.sim.sim_trace_count(0)
        edges = self.sim.sim_trace_count(1)
        self.ticks(20)
        self.assertEqual(self.sim.sim_trace_count(0), raw)
        self.assertEqual(self.sim.sim_trace_count(1), edges)
        self.assertEqual(self.sim.sim_state(0), 0)
        self.assertEqual(self.sim.sim_read_count(0, 2), 20)

    def test_raw_and_confirmed_edge_traces_are_distinct(self):
        raw = self.sim.sim_trace_count(0)
        edges = self.sim.sim_trace_count(1)
        self.sim.sim_buttons(0, 1)
        self.ticks(1)
        self.assertEqual(self.sim.sim_trace_count(0), raw + 1)
        self.assertEqual(self.sim.sim_trace_count(1), edges)
        self.ticks(1)
        self.assertEqual(self.sim.sim_trace_count(1), edges + 1)


if __name__ == "__main__":
    unittest.main()
