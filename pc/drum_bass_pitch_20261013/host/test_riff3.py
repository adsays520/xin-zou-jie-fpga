import unittest
from pathlib import Path
from unittest.mock import patch

from drum_patterns import Pattern
from guitar_controller import (
    GuitarController, MODE_POLY4, RIFF_PROFILES, RIFF_VOICINGS,
    make_mode_command, make_riff_attack_frames, riff_tail_ms,
)


class RecordingPort:
    is_open = True

    def __init__(self):
        self.data = []

    def write(self, data):
        self.data.append(data)
        return len(data)

    def flush(self):
        pass

    def close(self):
        self.is_open = False


class Riff3Tests(unittest.TestCase):
    def test_guitar_and_drums_share_four_bar_meter_and_tempo(self):
        profile = RIFF_PROFILES[3]
        pattern = Pattern.load(Path(__file__).resolve().parent / 'presets/hard_rock_riff_drums.json')
        self.assertEqual(profile['steps'] / profile['subdivision'], 16)
        self.assertEqual(pattern.bpm, profile['bpm'])
        self.assertEqual(pattern.swing, 0)
        self.assertAlmostEqual(sum(pattern.step_seconds(i) for i in range(64)), 7.5)
        steps = [step for step, _, _ in profile['events']]
        self.assertEqual(steps, sorted(set(steps)))
        self.assertTrue(all(0 <= step < profile['steps'] for step in steps))
        for _, voicing, accent in profile['events']:
            self.assertIn(voicing, RIFF_VOICINGS)
            frames = make_riff_attack_frames(3, voicing, 110 + accent)
            for offset in range(0, len(frames), 6):
                packet = frames[offset:offset + 6]
                self.assertEqual(packet[5], packet[0] ^ packet[1] ^ packet[2] ^ packet[3] ^ packet[4])

    def test_default_gates_leave_space_before_every_following_attack(self):
        profile = RIFF_PROFILES[3]
        step_ms = 60000 / profile['bpm'] / profile['subdivision']
        events = profile['events']
        for i, (step, voicing, _) in enumerate(events):
            next_step = events[i + 1][0] if i + 1 < len(events) else profile['steps']
            self.assertLess(riff_tail_ms(3, 0, voicing), (next_step - step) * step_ms)
        self.assertEqual(riff_tail_ms(3, 0, 'E5·'), 70)
        self.assertEqual(riff_tail_ms(3, 0, 'E5'), 225)
        self.assertIsNone(riff_tail_ms(3, 127, 'E5·'))
        self.assertEqual(riff_tail_ms(3, 126, 'E5·'), 1400)

    def test_new_button_schedules_attacks_and_stale_tail_cannot_cut_new_hit(self):
        with patch('guitar_controller.list_ports') as ports:
            ports.comports.return_value = []
            app = GuitarController()
            app.attributes('-alpha', 0)
            app.geometry('980x660')
            app.port = RecordingPort()
            app.update_idletasks()
            jobs = []

            def schedule(delay, callback):
                jobs.append((delay, callback))
                return f'riff-job-{len(jobs)}'

            try:
                self.assertTrue(app.riff3_button.winfo_ismapped())
                self.assertLessEqual(app.riff3_button.winfo_x() + app.riff3_button.winfo_width(),
                                     app.riff3_button.master.winfo_width())
                with patch.object(app, 'after', side_effect=schedule), patch.object(app, 'after_cancel'):
                    app.riff3_button.invoke()
                    self.assertTrue(app.riff_playing)
                    self.assertEqual(app.riff_active, 3)
                    self.assertEqual(jobs[-1][0], 7500)
                    jobs[0][1]()  # First full E5 chord.
                    full_tail = jobs[-1][1]
                    self.assertEqual(jobs[-1][0], 225)
                    jobs[1][1]()  # First muted E dyad.
                    self.assertEqual(jobs[-1][0], 70)
                    count = len(app.port.data)
                    full_tail()
                    self.assertEqual(len(app.port.data), count)
                    jobs[-1][1]()
                    self.assertEqual(app.port.data[-1], make_mode_command(MODE_POLY4))
                    app.riff3_button.invoke()
                    self.assertFalse(app.riff_playing)
                    count = len(app.port.data)
                    jobs[2][1]()
                    self.assertEqual(len(app.port.data), count)
            finally:
                app.close()
