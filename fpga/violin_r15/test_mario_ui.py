from contextlib import contextmanager
import tkinter as tk
import unittest
from unittest.mock import patch

from host_controller import ViolinController


class MemoryPort:
    def __init__(self):
        self.is_open = True
        self.packets = []

    def write(self, data):
        self.packets.append(bytes(data))
        return len(data)

    def close(self):
        self.is_open = False


class SongInterfaceTests(unittest.TestCase):
    @contextmanager
    def application(self):
        original = tk.Tk.__init__

        def hidden(instance, *arguments, **keywords):
            original(instance, *arguments, **keywords)
            instance.withdraw()

        with patch.object(tk.Tk, '__init__', hidden), patch('guitar_controller.list_ports.comports', return_value=[]):
            app = ViolinController()
        try:
            yield app, app.song_panel
        finally:
            app.song_panel.stop()
            app.hall_panel.close()
            app.disconnect()
            for token in app.tk.call('after', 'info'):
                app.tk.call('after', 'cancel', token)
            app.destroy()

    def test_page_is_registered_and_opening_does_not_send_commands(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            app.show_page('song')
            app.update_idletasks()
            self.assertEqual(app.active_page, 'song')
            self.assertEqual(len(panel.score.get_children()), 34)
            self.assertEqual(port.packets, [])
            self.assertIn('song', app._nav_buttons)

    def test_play_and_stop_only_emit_current_instrument_note_commands(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            app.current_timbre = 1
            app.show_page('song')
            panel.play()
            self.assertEqual(panel.player.state, 'playing')
            self.assertEqual([packet[1] for packet in port.packets], [0x05])
            panel.stop()
            self.assertEqual([packet[4] for packet in port.packets], [1, 0])
            self.assertEqual(app.current_timbre, 1)

    def test_hiding_page_and_disconnect_stop_future_playback(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            app.current_timbre = 1
            app.show_page('song')
            panel.play()
            app.show_page('guitar')
            self.assertEqual(panel.player.state, 'stopped')
            self.assertIsNone(panel.player._job)
            app.show_page('song')
            panel.play()
            app.disconnect()
            self.assertEqual(panel.player.state, 'stopped')
            self.assertFalse(port.is_open)

    def test_unconnected_upload_riff_and_bass_range_are_refused(self):
        with self.application() as (app, panel):
            panel.play()
            self.assertEqual(panel.player.state, 'stopped')
            port = MemoryPort()
            app.port = port
            app.draw_upload_busy = True
            panel.play()
            app.draw_upload_busy = False
            app.riff_playing = True
            panel.play()
            app.riff_playing = False
            app.current_timbre = 2
            panel.play()
            self.assertIn('移调', panel.status.get())
            self.assertEqual(port.packets, [])
            panel.transpose.set(-24)
            panel.play()
            self.assertEqual(port.packets[0][1], 0x02)

    def test_invalid_restart_stops_the_old_song_before_rejecting_input(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            app.current_timbre = 1
            panel.play()
            panel.bpm.set(0)
            panel.play()
            self.assertEqual(panel.player.state, 'stopped')
            self.assertIsNone(panel.player._job)
            self.assertEqual([packet[4] for packet in port.packets], [1, 0])


if __name__ == '__main__':
    unittest.main()
