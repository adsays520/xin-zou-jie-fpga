import unittest
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import Mock, patch
from guitar_controller import (TIMBRE_BASS, TIMBRE_GUITAR, TIMBRE_PIANO,
    GuitarController, bass_note_name, bass_note_frequency, note_frequency,
    make_timbre_command, make_command, CMD_PLUCK)


class BassTests(unittest.TestCase):
    def test_protocol_is_backward_compatible(self):
        self.assertEqual(make_timbre_command(TIMBRE_BASS), bytes.fromhex('a5 04 02 00 00 a3'))
        self.assertEqual(make_timbre_command(TIMBRE_GUITAR), bytes.fromhex('a5 04 00 00 00 a1'))
        self.assertEqual(make_timbre_command(TIMBRE_PIANO), bytes.fromhex('a5 04 01 00 00 a0'))
        with self.assertRaises(ValueError): make_timbre_command(3)

    def test_low_four_strings_and_all_frets(self):
        self.assertEqual([bass_note_name(s, 0) for s in (6, 5, 4, 3)], ['E1', 'A1', 'D2', 'G2'])
        for string in range(3, 7):
            for fret in range(21):
                self.assertEqual(bass_note_frequency(string, fret), note_frequency(string, fret) / 2)
                self.assertEqual(len(make_command(CMD_PLUCK, string, fret, 127)), 6)
        for string in (1, 2, 7):
            with self.assertRaises(ValueError): bass_note_frequency(string, 0)

    def test_effects_keep_bass_selected(self):
        app = SimpleNamespace(draw_upload_busy=False, current_timbre=TIMBRE_BASS,
                              port=Mock(is_open=True), send_timbre=Mock(), log=Mock())
        app.port.write.side_effect = lambda frame: len(frame)
        self.assertTrue(GuitarController.send_effects(app, [b'123456']))
        app.send_timbre.assert_not_called()

    def test_upper_string_cannot_pluck_previous_note(self):
        app = SimpleNamespace(current_timbre=TIMBRE_BASS, select_note=Mock(), send_command=Mock())
        GuitarController.pluck_note(app, 1, 0)
        app.select_note.assert_not_called()
        app.send_command.assert_not_called()

    def test_display_matches_selected_instrument(self):
        app = SimpleNamespace(current_timbre=TIMBRE_BASS)
        self.assertEqual(GuitarController.display_note_name(app, 6, 0), 'E1')
        self.assertAlmostEqual(GuitarController.display_note_frequency(app, 6, 0), 41.205)
        app.current_timbre = TIMBRE_GUITAR
        self.assertEqual(GuitarController.display_note_name(app, 6, 0), 'E2')

    def test_real_ui_switch_and_restore(self):
        app = GuitarController()
        app.withdraw()
        try:
            app.port = Mock(is_open=True)
            app.port.write.side_effect = lambda frame: len(frame)
            self.assertTrue(app.send_timbre(TIMBRE_BASS))
            app.update_idletasks()
            self.assertEqual(app._large_note.get(), 'E1')
            self.assertIn('disabled', app.fret_buttons[(1, 0)].state())
            self.assertEqual(app.fret_buttons[(6, 0)].cget('text'), 'E1')
            self.assertEqual(app.fret_buttons[(3, 0)].cget('text'), 'G2')
            app.select_note(3, 12)
            self.assertEqual(app._large_note.get(), 'G3')
            self.assertTrue(app.send_timbre(TIMBRE_GUITAR))
            self.assertNotIn('disabled', app.fret_buttons[(1, 0)].state())
            self.assertEqual(app.fret_buttons[(6, 0)].cget('text'), 'E2')
            self.assertEqual(app._large_note.get(), 'G4')
            app.select_note(1, 0)
            app.riff_playing = True
            self.assertTrue(app.send_timbre(TIMBRE_BASS))
            self.assertFalse(app.riff_playing)
            self.assertEqual(app.selected_string.get(), 6)
            self.assertEqual(app._large_note.get(), 'E1')
        finally:
            for job in app.tk.call('after', 'info'):
                app.after_cancel(job)
            app.port = None
            app.destroy()


if __name__ == '__main__': unittest.main()
