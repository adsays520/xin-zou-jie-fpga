import os
import ctypes
import unittest

import test_touch_runtime


class EightBoardScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(test_touch_runtime.TouchRuntimeTests, 'sim'):
            test_touch_runtime.TouchRuntimeTests.setUpClass()
        cls.sim = test_touch_runtime.TouchRuntimeTests.sim
        cls.sim.sim_scan_report_at.restype = ctypes.c_char_p

    def setUp(self):
        self.sim.sim_reset(1)

    def ticks(self, count):
        for unused in range(count):
            self.sim.sim_tick(5000)

    def report(self):
        self.sim.sim_scan_report()
        return [self.sim.sim_scan_report_at(i).decode() for i in range(self.sim.sim_scan_report_count())]

    def test_all_eight_boards_receive_reads_and_confirm_together(self):
        for chip in range(8):
            self.sim.sim_buttons(chip, 1 << chip)
        self.ticks(120)
        self.assertEqual(self.sim.sim_mask(), 0xff)
        for chip in range(8):
            self.assertGreaterEqual(self.sim.sim_read_count(chip, 2), 100)
            self.assertEqual(self.sim.sim_state(chip), 1 << chip)

    def test_eighth_board_can_finish_probing_with_seven_busy_online(self):
        self.sim.sim_reset(0)
        self.sim.sim_set_read_cost(800)
        self.ticks(300)
        self.assertEqual(self.sim.sim_mask(), 0xff)
        for chip in range(8):
            self.assertGreater(self.sim.sim_read_count(chip, 2), 0)

    def test_returning_chip2_gets_probe_slot_with_seven_busy_online(self):
        self.sim.sim_set_read_cost(800)
        self.sim.sim_fail(2, 3, 500)
        self.ticks(300)
        self.assertGreater(self.sim.sim_read_count(2, 0), 0)
        self.assertEqual(self.sim.sim_mask(), 0xff)

    def test_repeated_press_release_on_chip0_and_chip2_preserves_all_edges(self):
        self.sim.sim_note_at.restype = ctypes.c_char_p
        for beat in range(8):
            self.sim.sim_buttons(0, 0x800)
            self.sim.sim_buttons(2, 0x200)
            for unused in range(5):
                self.sim.sim_tick(2000)
            self.sim.sim_buttons(0, 0)
            self.sim.sim_buttons(2, 0)
            for unused in range(5):
                self.sim.sim_tick(2000)
        notes = [self.sim.sim_note_at(i).decode() for i in range(self.sim.sim_note_count())]
        for chip in (0, 2):
            self.assertEqual(sum(f'NOTE_KEY: DOWN chip={chip} ' in n for n in notes), 8)
            self.assertEqual(sum(f'NOTE_KEY: UP chip={chip} ' in n for n in notes), 8)

    def test_chip0_and_chip2_remain_confirmed_together(self):
        self.sim.sim_buttons(0, 0x800)
        self.sim.sim_buttons(2, 0x400)
        self.ticks(120)
        self.assertEqual(self.sim.sim_state(0), 0x800)
        self.assertEqual(self.sim.sim_state(2), 0x400)
        self.assertEqual(self.sim.sim_mask(), 0xff)

    def test_report_has_each_chip_and_correct_active_mask(self):
        self.ticks(10)
        lines = self.report()
        self.assertEqual(len(lines), 9)
        self.assertIn('CHIPS,8,ACTIVE,0xFF,ONLINE,0xFF', lines[0])
        for chip in range(8):
            self.assertIn(f'TOUCH,CHIP,{chip},ADDR,0x{0x37 + chip:02X},ACTIVE,1', lines[chip + 1])
            self.assertIn('REQUESTS,10,', lines[chip + 1])

    def test_readonly_report_does_not_poll_or_change_key_state(self):
        self.sim.sim_buttons(2, 0x400)
        self.ticks(4)
        before = [(self.sim.sim_read_count(c, 2), self.sim.sim_state(c)) for c in range(8)]
        mask = self.sim.sim_mask()
        self.report()
        self.report()
        self.assertEqual(before, [(self.sim.sim_read_count(c, 2), self.sim.sim_state(c)) for c in range(8)])
        self.assertEqual(mask, self.sim.sim_mask())

    def test_report_distinguishes_raw_disagreement_from_confirmed_press(self):
        self.sim.sim_button_sample(2, 0x400)
        self.sim.sim_button_sample(2, 0)
        self.ticks(1)
        line = self.report()[3]
        self.assertIn('FIRST,0x0400,SECOND,0x0000,RAW_VALID,3,CONFIRMED,0x0000', line)
        self.assertIn('REQUESTS,1,VERIFIES,1,SAMPLES,2,DISAGREE,1,', line)


if __name__ == '__main__':
    unittest.main()
