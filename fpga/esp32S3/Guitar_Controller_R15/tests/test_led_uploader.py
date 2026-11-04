import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("led_score_upload", Path(__file__).resolve().parents[1] / "tools/led_score_upload.py")
upload = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(upload)


class Port:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.sent = []

    def write(self, data):
        self.sent.append(data)
        return len(data)

    def flush(self):
        pass

    def readline(self):
        return next(self.replies)


class LedUploaderTests(unittest.TestCase):
    def test_native_usb_log_prefix_and_ansi_ack(self):
        port = Port([b'I (20) NOTE_KEY: DOWN\n', b'\x1b[0;32mI (21) HOST_REPLY: OK,LED\x1b[0m\r\n'])
        upload.send(port, "LED,STOP")
        self.assertEqual(port.sent, [b'LED,STOP\n'])

    def test_raw_uart_ack(self):
        upload.send(Port([b'OK,LED\r\n']), "LED,PLAY")

    def test_prefixed_error_is_not_accepted_or_retried(self):
        port = Port([b'I (1) HOST_REPLY: ERROR,LED,ARG_OR_BUSY\n'])
        with self.assertRaises(RuntimeError):
            upload.send(port, "LED,PLAY")
        self.assertEqual(len(port.sent), 1)

    def test_old_firmware_error_is_reported(self):
        with self.assertRaises(RuntimeError):
            upload.send(Port([b'I (1) HOST_REPLY: ERROR,USB_COMMAND\n']), "LED,STOP")

    def test_upload_only_led_commands_and_starts_after_cues(self):
        port = Port([b'OK,LED\n'] * 5)
        upload.upload(port, [(0, 21, 6, 200)], both=True)
        self.assertEqual(port.sent, [b'LED,STOP\n', b'LED,CLEAR\n', b'LED,ADD,0,21,6,200\n', b'LED,MODE,BOTH\n', b'LED,PLAY\n'])

    def test_csv_bounds_and_sorting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'score.csv'
            path.write_text('time_ms,position,string,duration_ms\n200,1,1,50\n0,21,6,200\n', encoding='utf8')
            self.assertEqual(upload.load_score(path), [(0, 21, 6, 200), (200, 1, 1, 50)])
            for row in ('0,0,0,10', '0,22,1,10', '0,1,7,10', '3599999,1,1,2', '0,1,1,0'):
                path.write_text('time_ms,position,string,duration_ms\n' + row + '\n', encoding='utf8')
                with self.assertRaises(ValueError):
                    upload.load_score(path)

    def test_csv_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'score.csv'
            for count in (0, 257):
                path.write_text('time_ms,position,string,duration_ms\n' + '0,1,1,10\n' * count, encoding='utf8')
                with self.assertRaises(ValueError):
                    upload.load_score(path)


if __name__ == '__main__':
    unittest.main()
