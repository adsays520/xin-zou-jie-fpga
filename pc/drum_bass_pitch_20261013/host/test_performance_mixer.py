import unittest

from performance_mixer import DUET_LEVELS, level_frame


class PerformanceMixerProtocolTests(unittest.TestCase):
    def test_guitar_balance_frame_and_checksum(self):
        packet = level_frame(0, DUET_LEVELS[0])
        self.assertEqual(packet, bytes((0xA5, 0x70, 0, 72, 0, 0x9D)))
        self.assertEqual(len(packet), 6)

    def test_all_buses_and_limits(self):
        for bus in range(3):
            for level in (0, 1, 72, 127):
                packet = level_frame(bus, level)
                self.assertEqual(packet[2:5], bytes((bus, level, 0)))
                self.assertEqual(packet[-1], packet[0] ^ packet[1] ^ packet[2] ^ packet[3] ^ packet[4])
        for bus, level in ((-1, 0), (3, 0), (0, -1), (0, 128)):
            with self.assertRaises(ValueError):
                level_frame(bus, level)


if __name__ == "__main__":
    unittest.main()
