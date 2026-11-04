import unittest
from unittest.mock import patch

from master_space_effects import MasterSpaceEffects, space_effect_frames
from guitar_controller import GuitarController
from test_drawn_upload import Harness


class MasterSpaceEffectsTests(unittest.TestCase):
    def test_atomic_frames_and_transport(self):
        frames = space_effect_frames(chorus_mix=24, chorus_rate=30, chorus_depth=46,
                                     delay_mix=38, delay_time=47, delay_feedback=36)
        self.assertEqual([frame[1] for frame in frames], [0x60, 0x61, 0x62])
        self.assertEqual(frames[0][2:5], bytes([24, 30, 46]))
        self.assertEqual(frames[1][2:5], bytes([38, 47, 36]))
        self.assertTrue(all(len(frame) == 6 and not __import__('functools').reduce(int.__xor__, frame)
                            for frame in frames))
        app = Harness()
        app.send_master_effects = lambda data: GuitarController.send_master_effects(app, data)
        app.disconnect = lambda: None
        app.draw_upload_busy = True
        self.assertFalse(app.send_master_effects(frames))
        self.assertEqual(app.port.frames, [])
        app.draw_upload_busy = False
        self.assertTrue(app.send_master_effects(frames))
        self.assertEqual(app.port.frames, frames)
        self.assertEqual(len(app.port.frames), 3)  # No guitar/timbre switch command.
        app.port.short_write = True
        self.assertFalse(app.send_master_effects(frames))
        with self.assertRaises(ValueError):
            space_effect_frames(delay_feedback=97)

    def test_all_instrument_window(self):
        with patch('guitar_controller.list_ports') as ports:
            ports.comports.return_value = []
            app = GuitarController(); app.attributes('-alpha', 0)
            try:
                panel = MasterSpaceEffects(app); panel.attributes('-alpha', 0); app.update()
                self.assertGreaterEqual(panel.winfo_width(), 600)
                panel.live.set(False)
                panel.hard_rock()
                with patch.object(app, 'send_master_effects', return_value=True) as send:
                    panel.send()
                    self.assertEqual(send.call_args.args[0][1][2], 38)
                    panel.off()
                    self.assertEqual(send.call_args.args[0][0][2], 0)
                    self.assertEqual(send.call_args.args[0][1][2], 0)
            finally:
                app.destroy()
