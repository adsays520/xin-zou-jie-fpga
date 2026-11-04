import ctypes
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BlePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = ROOT / 'tests/build'
        build.mkdir(exist_ok=True)
        library = build / f'ble_packet_{os.getpid()}.dll'
        compiler = os.environ.get('TOUCH_TEST_TCC', str(ROOT / 'tests/tools/tcc/tcc.exe'))
        subprocess.run([compiler, '-shared', '-o', str(library),
                        str(ROOT / 'tests/ble_packet_sim.c')], check=True, capture_output=True)
        cls.sim = ctypes.CDLL(str(library))

    def setUp(self):
        self.sim.packet_reset()

    def feed(self, flags, data, identity=17, epoch=1):
        value = bytes([flags, identity]) + bytes(data)
        array = (ctypes.c_uint8 * len(value)).from_buffer_copy(value)
        return self.sim.packet_feed(array, len(value), epoch)

    def test_all_wire_sizes_at_minimum_and_large_mtu(self):
        for size in (6, 12, 18, 24, 30, 36, 38, 266):
            for payload in (18, 240, 244):
                with self.subTest(size=size, payload=payload):
                    self.sim.packet_reset()
                    data = bytes(i % 256 for i in range(size))
                    for offset in range(0, size, payload):
                        part = data[offset:offset + payload]
                        last = offset + len(part) == size
                        self.assertEqual(self.feed((offset == 0) | (last << 1), part), int(last))
                    self.assertEqual(self.sim.packet_length(), size)
                    self.assertEqual(bytes(self.sim.packet_byte(i) for i in range(size)), data)
                    self.assertEqual(self.sim.packet_byte(size), 0)

    def test_continuation_requires_first(self):
        self.assertEqual(self.feed(2, b'abcdef'), -1)

    def test_wrong_id_cancels_assembly(self):
        self.assertEqual(self.feed(1, b'abc'), 0)
        self.assertEqual(self.feed(2, b'def', identity=18), -1)
        self.assertEqual(self.feed(2, b'def'), -1)

    def test_connection_change_cannot_complete_old_packet(self):
        self.assertEqual(self.feed(1, b'abc'), 0)
        self.assertEqual(self.feed(2, b'def', epoch=2), -1)

    def test_text_binary_type_cannot_change_mid_packet(self):
        self.assertEqual(self.feed(1, b'abc'), 0)
        self.assertEqual(self.feed(6, b'def'), -1)

    def test_oversize_packet_is_never_exposed(self):
        self.assertEqual(self.feed(1, bytes(244)), 0)
        self.assertEqual(self.feed(2, bytes(23)), -1)
        self.assertEqual(self.sim.packet_length(), 0)

    def test_illegal_flags_short_writes_and_short_binary(self):
        for flags, payload in ((8, b'abcdef'), (3, b''), (3, b'abc')):
            self.assertEqual(self.feed(flags, payload), -1)

    def test_text_rejects_embedded_command_terminators(self):
        for value in (b'LED\0MODE', b'PING\nLED,MODE,OFF', b'PING\r'):
            self.assertEqual(self.feed(7, value), -1)

    def test_new_first_replaces_only_the_unsubmitted_partial(self):
        self.assertEqual(self.feed(1, b'old'), 0)
        self.assertEqual(self.feed(7, b'PING', identity=18), 1)
        self.assertEqual(self.sim.packet_length(), 4)
        self.assertEqual(bytes(self.sim.packet_byte(i) for i in range(4)), b'PING')

    def test_completed_packet_cannot_be_extended(self):
        self.assertEqual(self.feed(3, b'abcdef'), 1)
        self.assertEqual(self.feed(2, b'ghi'), -1)


if __name__ == '__main__':
    unittest.main()
