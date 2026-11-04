import binascii
import time
import unittest
from unittest.mock import patch
import numpy as np
from guitar_controller import GuitarController
from live_verification import Capture, CaptureParser, PreviewSynth, configure, encode_capture, frame, peaks, spectrum, N, FS


class VerificationProtocolTests(unittest.TestCase):
    def test_atomic_stop_config_start_and_validation(self):
        data = configure([375, 750, 1125, 1500], [80, 80, 80, 0], [24, 104, 64, 64])
        self.assertEqual(data[:6], frame(0x82, 0))
        self.assertEqual(data[-6:], frame(0x82, 1))
        self.assertEqual(len(data), 60)
        for i in range(0, len(data), 6):
            check = 0
            for byte in data[i:i+6]: check ^= byte
            self.assertEqual(check, 0)
        for f in (0, 49, 5001, 65536):
            with self.assertRaises(ValueError): configure([f]*4, [80]*4, [64]*4)

    def test_fragmentation_noise_crc_and_recovery(self):
        c = PreviewSynth().capture([375, 750, 1125, 1500], [80]*4, [64]*4)
        packet = encode_capture(c)
        parser = CaptureParser()
        damaged = bytearray(packet); damaged[119] ^= 3
        data = b'noise\xd3' + bytes(damaged) + b'junk' + packet
        captures = []
        for i in range(0, len(data), 37): captures.extend(parser.feed(data[i:i+37]))
        self.assertEqual(len(captures), 1)
        np.testing.assert_array_equal(captures[0].samples, c.samples)
        self.assertGreater(parser.bad_packets, 0)
        self.assertLess(len(parser.buffer), 2)

    def test_one_to_four_independent_peaks_and_silence(self):
        for count in range(1, 5):
            c = PreviewSynth().capture([375, 750, 1125, 1500], [80 if i<count else 0 for i in range(4)], [64]*4)
            detected = peaks(c.samples, FS)
            self.assertEqual(len(detected), count)
            self.assertEqual(sorted(round(v[0]) for v in detected), [375, 750, 1125, 1500][:count])
        self.assertEqual(peaks(np.zeros((N, 2)), FS), [])

    def test_opposite_phase_stereo_does_not_cancel_spectrum(self):
        signal = np.sin(2*np.pi*750*np.arange(N)/FS)*10000
        detected = peaks(np.column_stack((signal, -signal)), FS)
        self.assertEqual(len(detected), 1)
        self.assertEqual(detected[0][0], 750)

    def test_parser_buffer_bounded_under_garbage_and_invalid_headers(self):
        parser = CaptureParser()
        for _ in range(50): parser.feed(b'\xd3\x91'+b'\xff'*10000)
        self.assertLessEqual(len(parser.buffer), 1)


class Port:
    is_open = True
    out_waiting = 0
    in_waiting = 0
    def __init__(self): self.data = []
    def write(self, data): self.data.append(data); return len(data)
    def close(self): self.is_open = False
    def flush(self): pass


class VerificationPageTests(unittest.TestCase):
    def setUp(self):
        with patch.object(GuitarController, 'refresh_ports'):
            self.app = GuitarController()
        self.app.attributes('-alpha', 0)
        self.app.port = Port()
        self.port = self.app.port
        self.page = self.app.show_page('verify')
        self.errors = []
        self.app.report_callback_exception = lambda *args: self.errors.append(args)
        self.app.update()

    def tearDown(self):
        self.app.update_idletasks()
        self.app.close()
        self.assertEqual(self.errors, [])

    def test_unknown_firmware_cannot_start_test(self):
        self.page.start()
        self.assertEqual(self.port.data, [])
        self.page.monitor()
        self.page.start()
        self.assertFalse(self.page.running)
        self.assertFalse(any(frame(0x82, 1) in d for d in self.port.data))

    def test_live_capture_then_start_and_disconnect_sends_stop(self):
        self.page.monitor()
        c = PreviewSynth().capture([375, 750, 1125, 1500], [80]*4, [64]*4)
        self.page.accept(c, time.monotonic())
        self.page.start()
        self.assertTrue(self.page.running)
        self.assertEqual(self.port.data[-1][-6:], frame(0x82, 1))
        self.app.disconnect()
        self.assertIn(frame(0x82, 0), self.port.data)
        self.assertFalse(self.page.monitoring)
        self.assertIn('断开', self.page.evidence.get())

    def test_preview_has_no_serial_writes_and_clearly_labels_evidence(self):
        self.page.mode.set('离线预览'); self.page.change_mode()
        count = len(self.port.data)
        self.page.start()
        self.page.poll()
        self.assertEqual(len(self.port.data), count)
        self.assertIn('离线', self.page.evidence.get())
        self.assertIn('不能验证', self.page.evidence.get())
        self.app.show_page('piano'); self.app.show_page('verify')
        self.assertIs(self.app._pages['verify'], self.page)

    def test_short_write_disconnects_without_recursive_failure(self):
        self.page.running = True
        self.port.write = lambda data: 0
        self.page.stop()
        self.assertIsNone(self.app.port)
        self.assertFalse(self.page.running)


if __name__ == '__main__': unittest.main()
