import unittest

from host_controller import MonoKeys, frame, violin_command
from hall_panel import pick_command, trigger_command, strum_command


class ProtocolTests(unittest.TestCase):
    def test_strum_command_is_not_an_individual_pick(self):
        self.assertEqual(strum_command(100), b'FPGA,STRUM,100\n')
        for velocity in (0, 128, True, 100.0, '100'):
            with self.assertRaises(ValueError):
                strum_command(velocity)

    def test_hall_and_direct_controls_are_distinct(self):
        self.assertEqual(trigger_command('HALL'), b'FPGA,TRIGGER,HALL\n')
        self.assertEqual(trigger_command('DIRECT'), b'FPGA,TRIGGER,DIRECT\n')
        self.assertEqual(trigger_command('AUTO'), b'FPGA,TRIGGER,AUTO\n')
        self.assertEqual(pick_command(6, 100), b'FPGA,PICK,6,100\n')
        self.assertEqual(pick_command(6, 100, 0), b'FPGA,PLUCK,6,0,100\n')
        for arguments in [(0, 100), (7, 100), (6, 0), (6, 128), (6, 100, 21), (True, 100)]:
            with self.assertRaises(ValueError):
                pick_command(*arguments)
        with self.assertRaises(ValueError):
            trigger_command('POLY')

    def test_checksums(self):
        for key in range(55, 101):
            for velocity in (1, 80, 100, 127):
                for action in (0, 1, 3):
                    packet = violin_command(key, velocity, action)
                    checksum = 0
                    for value in packet:
                        checksum ^= value
                    self.assertEqual(checksum, 0)
        self.assertEqual(frame(4, 3), bytes.fromhex('a5 04 03 00 00 a2'))

    def test_validation(self):
        for arguments in [(54, 100, 1), (101, 100, 1), (69, 0, 1), (69, 128, 1), (69, 100, 2)]:
            with self.assertRaises(ValueError):
                violin_command(*arguments)

    def test_legato_and_last_note_priority(self):
        keys = MonoKeys()
        self.assertEqual(keys.event(69, 100, True), violin_command(69, 100, 1))
        self.assertEqual(keys.event(72, 80, True), violin_command(72, 80, 3))
        self.assertEqual(keys.event(72, 1, False), violin_command(69, 100, 3))
        self.assertIsNone(keys.event(72, 1, False))
        self.assertEqual(keys.event(69, 1, False), violin_command(69, 1, 0))
        self.assertEqual(keys.held, {})

    def test_detached_and_stale_release(self):
        keys = MonoKeys()
        keys.event(55, 127, True, False)
        self.assertEqual(keys.event(100, 1, True, False), violin_command(100, 1, 1))
        self.assertIsNone(keys.event(55, 1, False, False))
        self.assertEqual(keys.event(100, 1, False), violin_command(100, 1, 0))


if __name__ == '__main__':
    unittest.main()
