import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("monitor_notes", Path(__file__).resolve().parents[1] / "monitor_notes.py")
MONITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MONITOR)


class NoteMonitorTests(unittest.TestCase):
    def test_guard_disagreement_is_visible_without_claiming_physical_false_touch(self):
        text = MONITOR.readable("W (190) TOUCH_SERIAL: READ_DISAGREE chip=0 first=0xFF01 verify=0x0000 total=1")
        self.assertEqual(text, "复读不一致：0号板 0xFF01 → 0x0000，未发布本次变化")

    def test_ack_displays_board_key_pitch_and_frame(self):
        text = MONITOR.readable("I (190) NOTE_ACK: DOWN chip=0 cs=8 key=4 note=G3 midi=55 "
                                "instrument=PIANO role=NOTE_ON seq=18 event_ms=185")
        self.assertIn("FPGA已收 按下 0号板 CS8 键4 → G3 (MIDI 55)", text)
        self.assertIn("帧18", text)

    def test_forced_release_is_visible_and_raw_is_hidden(self):
        text = MONITOR.readable("I (190) NOTE_KEY: UP chip=1 cs=8 key=22 reason=STALE event_ms=185")
        self.assertIn("超时保护松键", text)
        self.assertIsNone(MONITOR.readable("I (190) TOUCH_TRACE: RAW chip=0 raw=0x0100"))

    def test_dropped_logs_and_unverified_ack_are_not_hidden(self):
        self.assertIn("警告", MONITOR.readable("W (190) TOUCH_OUTPUT: QUEUE_OVERFLOW logs=1"))
        self.assertIn("警告", MONITOR.readable("W (190) FPGA_LINK: No verified ACK; retrying"))
