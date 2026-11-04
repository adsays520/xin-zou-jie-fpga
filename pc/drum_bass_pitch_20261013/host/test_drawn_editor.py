"""Layout and freehand interaction smoke tests; no hardware communication."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from guitar_controller import GuitarController, PianoKeyboard


class DrawnEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(GuitarController, "refresh_ports"):
            cls.app = GuitarController()
        cls.app.attributes("-alpha", 0)
        cls.keyboard = PianoKeyboard(cls.app)
        cls.keyboard.attributes("-alpha", 0)
        cls.app.piano_keyboard = cls.keyboard
        cls.app.update()
        cls.panel = cls.keyboard.drawn_panel

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def test_two_canvases_and_88_keys_fit_at_minimum_size(self):
        self.keyboard.geometry("1000x730")
        self.app.update()
        for canvas in (self.panel.wave_canvas, self.panel.env_canvas):
            self.assertGreater(canvas.winfo_width(), 400)
            self.assertGreaterEqual(canvas.winfo_height(), 190)
        self.assertGreaterEqual(self.keyboard.canvas.winfo_height(), 210)
        for key in range(21, 109):
            self.assertTrue(self.keyboard.canvas.find_withtag(f"key_{key}"))
        self.assertLess(self.panel.winfo_y() + self.panel.winfo_height(), self.keyboard.canvas.winfo_y())

    def test_drawing_interpolation_and_vertical_motion(self):
        canvas = self.panel.wave_canvas
        canvas.values[:] = [0.] * 1024
        left, top, right, bottom = canvas.bounds()
        canvas.start(SimpleNamespace(x=left, y=bottom))
        canvas.drag(SimpleNamespace(x=right, y=top))
        self.assertAlmostEqual(canvas.values[0], -1)
        self.assertAlmostEqual(canvas.values[-1], 1)
        self.assertAlmostEqual(canvas.values[512], 2 * 512 / 1023 - 1)
        canvas.drag(SimpleNamespace(x=right, y=bottom))
        self.assertEqual(canvas.values[-1], -1)

    def test_envelope_has_expanded_onset_and_persists(self):
        self.panel.duration.set("1400")
        canvas = self.panel.env_canvas
        self.assertAlmostEqual(canvas.sample_position(.3), 30 / 1400 * 4095)
        project = self.panel.project()
        self.panel.clear_envelope()
        self.panel.apply_project(project)
        self.assertEqual(self.panel.envelope, project["envelope"])
        self.panel.duration.set("nan")
        with self.assertRaises(ValueError):
            self.panel.project()
        self.panel.duration.set("1400")


if __name__ == "__main__":
    unittest.main()
