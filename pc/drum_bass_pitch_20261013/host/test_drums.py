import tempfile
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch
from functools import reduce
from drum_patterns import Pattern, PRESETS, BASIC_PRESETS, preset, frame, tempo_frame, hit_frame
from drum_editor import DrumEditor
from guitar_controller import GuitarController

class Port:
    is_open = True
    def __init__(self): self.data = []; self.short = False
    def write(self, data): self.data.append(data); return len(data) - 1 if self.short else len(data)
    def close(self): self.is_open = False

class DrumTests(unittest.TestCase):
    def test_basic_backbeat_and_accents(self):
        p = preset(BASIC_PRESETS[0])
        self.assertEqual([i for i,v in enumerate(p.cells[0][:16]) if v], [0,8])
        self.assertEqual([i for i,v in enumerate(p.cells[1][:16]) if v], [4,12])
        self.assertEqual([i for i,v in enumerate(p.cells[2][:16]) if v], list(range(0,16,2)))
        self.assertGreater(p.cells[2][0],p.cells[2][2])
        self.assertEqual(p.cells[0][:16],p.cells[0][16:32])
        self.assertEqual([i for i,v in enumerate(preset(BASIC_PRESETS[1]).cells[0][:16]) if v], [0,4,8,12])
        self.assertEqual(sum(bool(v) for v in preset("摇滚16分").cells[2][:16]),16)
    def test_presets_16_beats_and_swing_duration(self):
        for name in PRESETS:
            p = preset(name); p.validate()
            self.assertAlmostEqual(sum(p.step_seconds(i) for i in range(64)), 16 * 60 / p.bpm)
            self.assertTrue(any(p.cells[0])); self.assertTrue(any(p.cells[1]) or any(p.cells[10]))
        self.assertEqual(preset("布鲁斯 Shuffle").swing, 33)

    def test_all_upload_addresses_and_checksum(self):
        p = preset(PRESETS[0]); frames = p.upload_frames()
        cells = [f for f in frames if f[1] == 0x54]
        self.assertEqual(len(cells), 768)
        for i, f in enumerate(cells): self.assertEqual(f[2:5], bytes((i // 64, i % 64, p.cells[i // 64][i % 64])))
        for f in frames: self.assertEqual(reduce(int.__xor__, f), 0)
        self.assertEqual(frames[0], frame(0x52, 0)); self.assertEqual(frames[1], frame(0x53))
        self.assertNotIn(frame(0x52, 1), frames) # Explicit start only after upload finishes.

    def test_validation_and_roundtrip(self):
        p = preset("Funk")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pattern.json"; p.save(path); self.assertEqual(Pattern.load(path), p)
        for bpm, swing in [(29,0),(301,0),(120,51),(120,-1),(120.5,0)]:
            with self.assertRaises(ValueError): tempo_frame(bpm, swing)
        with self.assertRaises(ValueError): hit_frame(12, 100)
        with self.assertRaises(ValueError): hit_frame(0, 0)
        p.cells[0][0] = True
        with self.assertRaises(ValueError): p.validate()

    def make_app(self):
        app = GuitarController(); app.attributes('-alpha', 0); app.port = Port()
        app.open_drums(); app.drum_window.attributes('-alpha', 0); app.update()
        return app, app.drum_window

    def test_ui_grid_and_upload_completion(self):
        with patch('guitar_controller.list_ports') as ports:
            ports.comports.return_value=[]
            app, panel = self.make_app()
            try:
                panel.geometry('1000x650'); app.update()
                self.assertEqual(panel.geometry_values()[0], 16)
                self.assertEqual(sum(panel.canvas.type(item)=="rectangle" for item in panel.canvas.find_all()), 12*16)
                self.assertGreater(panel.canvas.winfo_width(), 700)
                self.assertLessEqual(panel.canvas.bbox('all')[3], panel.canvas.winfo_height())
                for widget in panel.level_widgets + panel.mute_widgets:
                    self.assertTrue(widget.winfo_ismapped())
                    self.assertGreaterEqual(widget.winfo_width(), widget.winfo_reqwidth())
                    self.assertLessEqual(widget.winfo_x() + widget.winfo_width(), widget.master.winfo_width())
                panel.mute(1, True)
                self.assertEqual(app.port.data[-1], frame(0x57, 1, 0))
                count = len(app.port.data); panel.audition(1)
                self.assertEqual(len(app.port.data), count)
                panel.mute(1, False); panel.audition(1)
                self.assertTrue(app.port.data[-1].endswith(hit_frame(1, 100)))
                panel.preset_box.set(BASIC_PRESETS[1]); panel.play_preset()
                self.assertEqual(panel.pattern.name, BASIC_PRESETS[1])
                deadline = __import__('time').monotonic() + 4
                while panel.uploading and __import__('time').monotonic() < deadline: app.update()
                self.assertTrue(panel.playing)
                self.assertEqual(app.port.data[-1], frame(0x52,1))
                old_bpm = panel.pattern.bpm; count = len(app.port.data)
                panel.bpm.set(0); panel.apply_tempo()
                self.assertEqual(panel.pattern.bpm, old_bpm)
                self.assertEqual(len(app.port.data), count)
                self.assertTrue(panel.playing); panel.bpm.set(old_bpm)
                panel.stop(); self.assertFalse(panel.playing); self.assertEqual(app.port.data[-1], frame(0x52,0))
            finally: app.close()

    def test_cancel_and_short_write_never_starts(self):
        with patch('guitar_controller.list_ports') as ports:
            ports.comports.return_value=[]
            app,panel=self.make_app()
            try:
                panel.start();panel.stop();app.update()
                self.assertFalse(panel.playing); self.assertFalse(panel.uploading)
                self.assertFalse(any(data==frame(0x52,1) for data in app.port.data))
                failed=app.port;failed.short=True;panel.start();app.update()
                self.assertIsNone(app.port);self.assertFalse(panel.playing);self.assertFalse(panel.uploading)
            finally:app.close()

if __name__=='__main__': unittest.main()
