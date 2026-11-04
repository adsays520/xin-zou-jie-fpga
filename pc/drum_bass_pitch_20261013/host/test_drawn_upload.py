"""Exercise the GUI's asynchronous uploader without opening a COM port or Tk window."""
import unittest
from collections import deque

from drawn_synth import CMD_DRAW_SELECT, ENV_POINTS, WAVE_POINTS, control_frame, make_upload_frames
from guitar_controller import GuitarController, TIMBRE_PIANO, make_timbre_command


class Variable:
    def set(self, value):
        self.value = value


class Port:
    def __init__(self):
        self.is_open = True
        self.out_waiting = 0
        self.frames = []
        self.short_write = False

    def write(self, frame):
        self.frames.append(frame)
        return len(frame) - int(self.short_write)

    def flush(self):
        pass

    def close(self):
        self.is_open = False


class Harness:
    send_drawn_synth = GuitarController.send_drawn_synth
    restore_piano = GuitarController.restore_piano
    _finish_draw_upload = GuitarController._finish_draw_upload
    disconnect = GuitarController.disconnect

    def __init__(self):
        self.port = Port()
        self.draw_upload_busy = False
        self.draw_upload_token = 0
        self.draw_upload_done = None
        self.drawn_enabled_requested = False
        self.timbre_text = Variable()
        self.connection_text = Variable()
        self.connect_button = self
        self.queue = deque()
        self.results, self.progress = [], []

    def configure(self, **_):
        pass

    def log(self, _):
        pass

    def after(self, _, function):
        self.queue.append(function)

    def send_timbre(self, timbre):
        self.port.write(make_timbre_command(timbre))
        return True

    def upload(self):
        self.send_drawn_synth([0.] * WAVE_POINTS, [0.] * ENV_POINTS, 1400,
                             lambda *args: self.progress.append(args),
                             lambda *args: self.results.append(args))

    def drain(self):
        for _ in range(1000):
            if not self.queue:
                return
            self.queue.popleft()()
        raise AssertionError("uploader failed to finish")


class DrawnUploadTests(unittest.TestCase):
    def test_complete_order_and_nonblocking_progress(self):
        app = Harness()
        app.upload()
        self.assertTrue(app.draw_upload_busy)
        self.assertEqual(len(app.port.frames), 2)
        app.drain()
        expected = [make_timbre_command(TIMBRE_PIANO), control_frame(CMD_DRAW_SELECT, 0)]
        expected += make_upload_frames([0.] * WAVE_POINTS, [0.] * ENV_POINTS, 1400)
        self.assertEqual(app.port.frames, expected)
        self.assertFalse(app.draw_upload_busy)
        self.assertTrue(app.drawn_enabled_requested)
        self.assertEqual(len(app.results), 1)
        self.assertTrue(app.results[0][0])
        self.assertIn("无ACK", app.results[0][1])
        self.assertEqual(app.progress[-1], (774, 774))

    def test_cancel_prevents_pending_data_after_restore(self):
        app = Harness()
        app.upload()
        app.queue.popleft()()
        app.restore_piano()
        count = len(app.port.frames)
        app.drain()
        self.assertEqual(len(app.port.frames), count)
        self.assertFalse(app.draw_upload_busy)
        self.assertFalse(app.drawn_enabled_requested)
        self.assertEqual(len(app.results), 1)
        self.assertFalse(app.results[0][0])

    def test_disconnect_cancels_before_reconnect(self):
        app = Harness()
        app.upload()
        old_port = app.port
        app.disconnect()
        self.assertFalse(old_port.is_open)
        app.port = Port()
        app.drain()
        self.assertEqual(app.port.frames, [])
        self.assertEqual(len(app.results), 1)
        self.assertFalse(app.results[0][0])

    def test_short_write_never_enables_mode(self):
        app = Harness()
        app.upload()
        old_port = app.port
        old_port.short_write = True
        app.drain()
        self.assertFalse(old_port.is_open)
        self.assertFalse(app.drawn_enabled_requested)
        self.assertEqual(len(app.results), 1)
        self.assertFalse(app.results[0][0])

    def test_offline_never_uploads(self):
        app = Harness()
        app.port = None
        app.upload()
        self.assertEqual(app.queue, deque())
        self.assertFalse(app.draw_upload_busy)
        self.assertFalse(app.results[0][0])


if __name__ == "__main__":
    unittest.main()
