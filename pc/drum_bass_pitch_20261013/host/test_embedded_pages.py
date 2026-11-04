"""Navigation, piano persistence, live control and inline editing regressions."""
import time
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from guitar_controller import GuitarController, CMD_PLUCK, make_piano_key_command
from performance_mixer import level_frame
from master_space_effects import space_effect_frames
from ui_pages import PAGE_TITLES


class Port:
    is_open = True
    out_waiting = 0
    def __init__(self): self.data = []
    def write(self, data): self.data.append(data); return len(data)
    def flush(self): pass
    def close(self): self.is_open = False


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class EmbeddedPagesTests(unittest.TestCase):
    def setUp(self):
        with patch.object(GuitarController, 'refresh_ports'):
            self.app = GuitarController()
        self.app.attributes('-alpha', 0)
        self.app.port = Port()
        self.port = self.app.port
        self.errors = []
        self.app.report_callback_exception = lambda *args: self.errors.append(args)
        self.app.update()

    def tearDown(self):
        self.app.close()
        self.assertEqual(self.errors, [])

    def pump(self, seconds=.13):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.app.update()
            time.sleep(.004)

    def assert_single_window(self):
        self.assertFalse(any(isinstance(w, tk.Toplevel) for w in descendants(self.app)))

    def test_five_pages_have_no_redundant_entries_or_toplevels(self):
        self.assertEqual(list(PAGE_TITLES), ['guitar', 'piano', 'drums', 'pitch', 'effects', 'mix', 'verify'])
        for key in PAGE_TITLES:
            page = self.app.show_page(key); self.app.update()
            self.assertIs(page.winfo_toplevel(), self.app)
            self.assertEqual(self.app.active_page, key)
            self.assertIs(self.app.show_page(key), page)
        self.assert_single_window()
        texts = [w.cget('text') for w in descendants(self.app) if isinstance(w, (ttk.Button, ttk.Label))]
        self.assertNotIn('钢琴快捷控制', texts)
        self.assertNotIn('手绘包络', texts)
        self.assertNotIn('吉他手绘包络', texts)
        self.app.open_mixer(); page = self.app._pages['mix']
        self.app.open_master_effects()
        self.assertIs(self.app._pages['mix'], page)

    def test_piano_envelope_and_wave_survive_navigation(self):
        page = self.app.show_page('piano'); self.app.update()
        panel = page.drawn_panel
        panel.duration.set('2000')
        for canvas in (panel.wave_canvas, panel.env_canvas):
            left, top, right, bottom = canvas.bounds()
            canvas.start(SimpleNamespace(x=left, y=bottom))
            canvas.drag(SimpleNamespace(x=right, y=top))
        expected = panel.project()
        self.app.show_page('mix'); self.app.show_page('guitar')
        restored = self.app.show_page('piano')
        self.assertIs(restored, page)
        self.assertEqual(panel.project(), expected)
        for key in range(21, 109): self.assertTrue(page.canvas.find_withtag('key_'+str(key)))

    def test_piano_note_released_on_main_window_mouseup_and_navigation(self):
        page = self.app.show_page('piano'); self.app.update()
        page._press_key(60)
        self.assertEqual(page.held_key, 60)
        self.app.event_generate('<ButtonRelease-1>'); self.app.update()
        self.assertIsNone(page.held_key)
        self.assertEqual(self.port.data[-1], make_piano_key_command(60, self.app.piano_velocity.get(), False))
        page._press_key(64); self.app.show_page('mix')
        self.assertIsNone(page.held_key)
        self.assertEqual(self.port.data[-1], make_piano_key_command(64, self.app.piano_velocity.get(), False))
        self.app.show_page('piano')
        count = len(self.port.data)
        self.app.guitar_shortcut(SimpleNamespace(widget=self.app), lambda: self.app.send_command(CMD_PLUCK))
        self.assertEqual(len(self.port.data), count)

    def test_combined_page_live_pointer_slider_preserves_exact_frames(self):
        self.app.show_page('mix'); self.app.update()
        mixer = self.app.mixer_window
        sliders = [w for w in descendants(mixer) if isinstance(w, ttk.Scale)]
        slider = sliders[0]
        x, y = slider.winfo_width()-10, slider.winfo_height()//2
        slider.event_generate('<ButtonPress-1>', x=x, y=y)
        slider.event_generate('<B1-Motion>', x=slider.winfo_width()//2, y=y)
        slider.event_generate('<ButtonRelease-1>', x=slider.winfo_width()//2, y=y)
        self.pump()
        self.assertTrue(45 < mixer.levels[0].get() < 85)
        self.assertIn(level_frame(0, mixer.levels[0].get()), self.port.data)
        mixer.set_level(0, 72)
        space = self.app.space_effects_window
        space.vars['chorus_mix'].set(24); space.vars['delay_mix'].set(38)
        self.app.show_page('guitar'); self.pump()
        self.assertIn(level_frame(0, 72), self.port.data)
        frames = space_effect_frames(chorus_mix=24, delay_mix=38)
        self.assertEqual(self.port.data[-3:], frames)
        self.app.show_page('mix')
        self.assertEqual(mixer.levels[0].get(), 72)
        self.assertEqual(space.vars['delay_mix'].get(), 38)

    def test_riff_and_drum_playback_continue_across_pages(self):
        drums = self.app.show_page('drums'); self.app.update()
        self.app.toggle_riff(3)
        drums.start(); self.pump(.55)
        self.assertTrue(drums.playing)
        self.app.show_page('mix'); self.app.show_page('piano'); self.app.show_page('guitar')
        self.pump(.15)
        self.assertTrue(drums.playing)
        self.assertTrue(self.app.riff_playing)
        self.assertEqual(self.app.riff_active, 3)
        self.assertEqual(self.app.bus_levels[0], 72)

    def test_drum_detail_edit_is_inline_and_applies_four_velocities(self):
        page = self.app.show_page('drums'); self.app.update()
        page.details(SimpleNamespace(x=10, y=45)); self.app.update()
        self.assert_single_window()
        for var, value in zip(page.detail_values, (91, 0, 55, 0)): var.set(value)
        page.apply_detail()
        self.assertEqual(page.pattern.cells[0][:4], [91, 0, 55, 0])
        self.assertEqual(page.detail_slot.winfo_children(), [])

    def test_offline_warning_appears_inline(self):
        self.app.port = None
        self.app.send_command(CMD_PLUCK); self.app.update()
        self.assertTrue(self.app._notice_bar.winfo_ismapped())
        self.assertIn('未连接', self.app._notice_text.get())
        self.assert_single_window()


if __name__ == '__main__': unittest.main()
