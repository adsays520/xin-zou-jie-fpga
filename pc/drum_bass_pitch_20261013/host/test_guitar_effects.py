import unittest
from unittest.mock import patch
from guitar_effects import AMPS,MODS,GuitarEffects,effect_frames
from guitar_controller import GuitarController
from test_drawn_upload import Harness

class FxTests(unittest.TestCase):
    def test_atomic_frames(self):
        frames=effect_frames(amp=4,modulation=3,compressor=True)
        self.assertEqual([f[1] for f in frames],[0x40,0x41,0x42,0x43,0x44])
        self.assertEqual(frames[0][2:5],bytes([4,64,64]))
        self.assertEqual(frames[1][4],7)
        for f in frames:
            self.assertEqual(len(f),6)
            self.assertEqual(0,__import__('functools').reduce(int.__xor__,f))

    def test_all_modes_and_bounds(self):
        for a in range(len(AMPS)):
            for m in range(len(MODS)): self.assertEqual(len(effect_frames(amp=a,modulation=m)),5)
        for k,v in [('amp',11),('modulation',6),('drive',128),('threshold',-1),('level',2.5)]:
            with self.assertRaises(ValueError):effect_frames(**{k:v})

    def test_send_guard_and_short_write(self):
        app=Harness();app.send_effects=lambda frames:GuitarController.send_effects(app,frames)
        app.current_timbre=0
        app.draw_upload_busy=True
        self.assertFalse(app.send_effects(effect_frames()))
        self.assertEqual(app.port.frames,[])
        app.draw_upload_busy=False
        self.assertTrue(app.send_effects(effect_frames(amp=4)))
        self.assertEqual(len(app.port.frames),5)  # No timbre flush while already playing guitar.
        app.port.short_write=True
        self.assertFalse(app.send_effects(effect_frames()))
        self.assertIsNone(app.port)

    def test_window_and_clean(self):
        with patch('guitar_controller.list_ports') as ports:
            ports.comports.return_value=[]
            app=GuitarController();app.attributes('-alpha',0)
            try:
                panel=GuitarEffects(app);panel.attributes('-alpha',0);app.update()
                self.assertGreater(panel.winfo_width(),700)
                panel.slash();self.assertEqual(panel.amp.get(),AMPS[4])
                with patch.object(app,'send_effects',return_value=True) as send:
                    panel.send();self.assertEqual(send.call_args.args[0][0][2],4)
                    panel.clean();frames=send.call_args.args[0]
                    self.assertEqual(frames[0][2],0);self.assertEqual(frames[1][4]&6,0)
            finally:app.destroy()
