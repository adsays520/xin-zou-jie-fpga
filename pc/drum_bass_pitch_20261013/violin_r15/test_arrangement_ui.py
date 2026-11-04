from contextlib import contextmanager
from pathlib import Path
import tempfile
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest.mock import patch

from host_controller import ViolinController
from arrangement_model import BAR, Clip, Note, PPQ, Track


class MemoryPort:
    def __init__(self):
        self.is_open = True
        self.packets = []
        self.writes = []
        self.incoming = bytearray()

    def write(self, data):
        self.writes.append(bytes(data))
        self.packets.extend(bytes(data[offset:offset + 6]) for offset in range(0, len(data), 6))
        return len(data)

    def close(self):
        self.is_open = False

    def read(self, count):
        data = bytes(self.incoming[:count])
        del self.incoming[:count]
        return data


class ArrangementInterfaceTests(unittest.TestCase):
    @contextmanager
    def application(self):
        original = tk.Tk.__init__

        def hidden(instance, *arguments, **keywords):
            original(instance, *arguments, **keywords)
            instance.withdraw()

        with patch.object(tk.Tk, '__init__', hidden), patch('guitar_controller.list_ports.comports', return_value=[]):
            app = ViolinController()
        try:
            app.show_page('arrangement')
            app.update_idletasks()
            # Existing synchronous assertions now wait for the real background worker.
            # Production play/stop remain nonblocking. Concurrency tests call the
            # original bound methods directly and deliberately do not pump Tk.
            panel = app.arrangement_panel
            for name in ('play', 'stop'):
                original_action = getattr(panel, name)
                def settled(*arguments, _action=original_action, **keywords):
                    result = _action(*arguments, **keywords)
                    self.assertTrue(panel.player.wait_ready(1))
                    panel._refresh_player()
                    return result
                setattr(panel, name, settled)
            yield app, app.arrangement_panel
        finally:
            app.arrangement_panel.stop()
            app.hall_panel.close()
            app.disconnect()
            for token in app.tk.call('after', 'info'):
                app.tk.call('after', 'cancel', token)
            app.destroy()

    def test_page_is_integrated_and_opening_does_not_send(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            app.show_page('guitar')
            app.show_page('arrangement')
            self.assertEqual(app.active_page, 'arrangement')
            self.assertIn('arrangement', app._nav_buttons)
            self.assertEqual(len(panel.project.tracks), 5)
            self.assertFalse(panel.hardware.get())
            self.assertEqual(port.packets, [])

    def test_preview_and_leaving_page_are_safe(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            panel.play()
            self.assertEqual(panel.player.state, 'playing')
            self.assertEqual(port.packets, [])
            app.show_page('guitar')
            self.assertEqual(panel.player.state, 'stopped')
            self.assertIsNone(panel.player._job)

    def test_hardware_play_is_explicit_and_disconnect_stops(self):
        with self.application() as (app, panel):
            panel.hardware.set(True)
            panel.play()
            self.assertIn('UART', panel.status.get())
            port = MemoryPort()
            app.port = port
            panel.play()
            self.assertEqual(panel.player.state, 'playing')
            self.assertEqual(app.current_timbre, 1)
            self.assertTrue(any(packet[1] == 5 and packet[4] == 1 for packet in port.packets))
            app.disconnect()
            self.assertEqual(panel.player.state, 'stopped')
            self.assertFalse(port.is_open)

    def test_rejects_hardware_conflicts_before_any_write(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            panel.project.tracks.append(Track('violin', clips=[Clip(notes=[Note(pitch=67)])]))
            panel.hardware.set(True)
            panel.play()
            self.assertIn('主音色互斥', panel.status.get())
            self.assertEqual(port.packets, [])

    def test_busy_guard_refuses_upload_riff_and_song(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            panel.hardware.set(True)
            app.draw_upload_busy = True
            panel.play()
            self.assertIn('上传', panel.status.get())
            app.draw_upload_busy = False
            app.riff_playing = True
            panel.play()
            self.assertIn('Riff', panel.status.get())
            app.riff_playing = False
            app.song_panel.player.state = 'paused'
            panel.play()
            self.assertIn('乐曲播放器', panel.status.get())
            app.song_panel.player.state = 'stopped'
            self.assertEqual(port.packets, [])

    def test_tracks_clips_notes_and_undo_redo(self):
        with self.application() as (app, panel):
            panel.add_track()
            self.assertEqual(len(panel.project.tracks), 6)
            panel.add_clip()
            self.assertEqual(len(panel.track().clips), 1)
            panel.note_start.set(0)
            panel.note_length.set(1)
            panel.add_note()
            self.assertEqual(len(panel.clip().notes), 1)
            panel.pitch.set(65)
            panel.apply_note()
            self.assertEqual(panel.note().pitch, 65)
            panel.undo()
            self.assertEqual(panel.note().pitch, 60)
            panel.redo()
            self.assertEqual(panel.note().pitch, 65)
            panel.copy_clip()
            self.assertEqual(len(panel.track().clips), 2)
            panel.delete_clip()
            panel.delete_track()
            self.assertEqual(len(panel.project.tracks), 5)

    def test_invalid_edit_rolls_back_without_changing_uart(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            original = panel.project.to_dict()
            panel.bpm.set(900)
            panel.apply_project()
            self.assertEqual(panel.project.to_dict(), original)
            self.assertIn('未修改', panel.status.get())
            self.assertEqual(port.packets, [])

    def test_automation_point_and_default_edits(self):
        with self.application() as (app, panel):
            panel.point_beat.set(2)
            panel.point_value.set(32)
            panel.apply_point()
            self.assertEqual(next(point.value for point in panel.lane().points if point.tick == 2 * PPQ), 32)
            panel.base_value.set(12)
            panel.apply_base()
            self.assertEqual(panel.project.parameters['space.delay_mix'], 12)
            panel.delete_point()
            self.assertFalse(any(point.tick == 2 * PPQ for point in panel.lane().points))
            panel.clear_automation()
            self.assertIsNone(panel.lane())

    def test_mute_solo_are_undoable(self):
        with self.application() as (app, panel):
            panel.toggle_track('solo')
            self.assertEqual(len(panel.project.active_tracks()), 1)
            panel.undo()
            self.assertEqual(len(panel.project.active_tracks()), 5)
            panel.toggle_track('muted')
            self.assertEqual(len(panel.project.active_tracks()), 4)

    def test_save_open_and_export_no_hardware_writes(self):
        with self.application() as (app, panel), tempfile.TemporaryDirectory() as folder:
            port = MemoryPort()
            app.port = port
            project_path = str(Path(folder) / 'song.tang.json')
            csv_path = str(Path(folder) / 'events.csv')
            with patch('arrangement_panel.filedialog.asksaveasfilename', return_value=project_path):
                panel.save()
            self.assertTrue(Path(project_path).exists())
            with patch('arrangement_panel.filedialog.askopenfilename', return_value=project_path):
                panel.open()
            with patch('arrangement_panel.filedialog.asksaveasfilename', return_value=csv_path):
                panel.export()
            self.assertIn('instrument', Path(csv_path).read_text(encoding='utf-8-sig'))
            self.assertEqual(port.packets, [])

    def test_mouse_clip_move_and_resize(self):
        with self.application() as (app, panel):
            clip = panel.clip()
            panel.drag = ('clip', 0, clip.start, clip.length, False)
            panel._timeline_release(SimpleNamespace(x=panel.pixels_per_beat))
            self.assertEqual(panel.clip().start, PPQ)
            panel.undo()
            clip = panel.clip()
            panel.drag = ('clip', 0, clip.start, clip.length, True)
            panel._timeline_release(SimpleNamespace(x=panel.pixels_per_beat))
            self.assertEqual(panel.clip().length, 2 * BAR + PPQ)

    def test_mouse_note_move_and_resize(self):
        with self.application() as (app, panel):
            panel.note_id = panel.clip().notes[0].id
            old = panel.note()
            panel.drag = ('note', 0, 0, deepcopy_note(old), False)
            panel._roll_release(SimpleNamespace(x=panel.pixels_per_beat, y=0))
            self.assertEqual(panel.note().start, PPQ)
            panel.drag = ('note', 0, 0, deepcopy_note(panel.note()), True)
            panel._roll_release(SimpleNamespace(x=panel.pixels_per_beat, y=0))
            self.assertEqual(panel.note().duration, 3 * PPQ)

    def test_unsaved_discard_can_cancel(self):
        with self.application() as (app, panel):
            panel.add_track()
            with patch('arrangement_panel.messagebox.askyesno', return_value=False):
                panel.new()
            self.assertEqual(len(panel.project.tracks), 6)

    def test_partial_serial_write_stops_future_events(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            port.write = lambda data: len(data) - 1
            app.port = port
            panel.hardware.set(True)
            panel.play()
            self.assertEqual(panel.player.state, 'stopped')
            self.assertIsNone(panel.player._job)


def deepcopy_note(note):
    return Note(note.start, note.duration, note.pitch, note.velocity, note.id)


if __name__ == '__main__':
    unittest.main()
