import heapq
from types import SimpleNamespace
import unittest

from mario_score import MEASURES, ScoreNote, bar_order, numbered_measure
from melody_player import CommandPlayer, make_plan, note_frame


class VirtualClock:
    def __init__(self):
        self.now = 0.0
        self.serial = 0
        self.jobs = []
        self.cancelled = set()

    def clock(self):
        return self.now

    def schedule(self, milliseconds, callback):
        self.serial += 1
        heapq.heappush(self.jobs, (self.now + milliseconds / 1000, self.serial, callback))
        return self.serial

    def cancel(self, token):
        self.cancelled.add(token)

    def advance(self, seconds):
        deadline = self.now + seconds
        while self.jobs and self.jobs[0][0] <= deadline:
            when, token, callback = heapq.heappop(self.jobs)
            self.now = when
            if token not in self.cancelled:
                callback()
        self.now = deadline


class ScoreTests(unittest.TestCase):
    def test_all_34_bars_are_exactly_four_beats(self):
        self.assertEqual(len(MEASURES), 34)
        for notes in MEASURES:
            self.assertEqual(sum(note.ticks for note in notes), 96)
            self.assertTrue(all(note.ticks in (6, 8, 12, 24) for note in notes))
            self.assertEqual(numbered_measure(notes).count('/'), 3)

    def test_opening_octaves_rests_and_syncopation(self):
        self.assertEqual([note.pitch for note in MEASURES[0]], [76, 76, 76, None, 72, 76, 79, None, 67, None])
        self.assertEqual([note.ticks for note in MEASURES[0]], [6, 12, 6, 6, 6, 12, 12, 12, 12, 12])
        pitches = [note.pitch for bar in MEASURES for note in bar if note.pitch is not None]
        self.assertEqual((min(pitches), max(pitches)), (64, 81))

    def test_accidentals_are_per_note_not_silently_carried(self):
        self.assertEqual([note.pitch for note in MEASURES[5]][:6], [None, 79, 78, 77, 75, 76])
        self.assertEqual(ScoreNote('#5', 6).pitch, 68)
        self.assertEqual(ScoreNote('b7', 6).pitch, 70)
        with self.assertRaises(ValueError):
            ScoreNote('8', 6).pitch

    def test_triplets_and_repeated_section(self):
        self.assertEqual([note.ticks for note in MEASURES[2]][:3], [8, 8, 8])
        self.assertEqual([note.ticks for note in MEASURES[19]][:6], [8] * 6)
        self.assertEqual(bar_order(), tuple(range(1, 35)) + tuple(range(23, 35)))
        self.assertEqual(bar_order(31, False), (31, 32, 33, 34))
        self.assertEqual(len(make_plan(1).bars), 46)
        self.assertAlmostEqual(make_plan(1).duration, 110.4)
        self.assertAlmostEqual(make_plan(1, score_repeat=False).duration, 81.6)

    def test_protocol_frames_never_change_timbre_or_mode(self):
        for timbre, transpose in ((0, 0), (1, 0), (2, -24), (3, 0)):
            plan = make_plan(timbre, transpose=transpose)
            frames = [event.frame for event in plan.events if event.frame]
            self.assertTrue(frames)
            self.assertEqual({frame[1] for frame in frames}, {0x02 if timbre in (0, 2) else 0x05 if timbre == 1 else 0x08})
            for frame in frames:
                self.assertEqual(len(frame), 6)
                checksum = 0
                for value in frame:
                    checksum ^= value
                self.assertEqual(checksum, 0)

    def test_guitar_and_bass_frame_pitch_mapping(self):
        opens = (64, 59, 55, 50, 45, 40)
        for timbre, transpose in ((0, 0), (2, -24)):
            for event in make_plan(timbre, transpose=transpose).events:
                if event.on is not True:
                    self.assertIsNone(event.frame)
                    continue
                frame = event.frame
                self.assertEqual(opens[frame[2] - 1] + frame[3] - (12 if timbre == 2 else 0), event.pitch)
                self.assertLessEqual(frame[3], 20)
                if timbre == 2:
                    self.assertGreaterEqual(frame[2], 3)

    def test_out_of_range_is_rejected_before_playback(self):
        for parameters in ({'timbre': 2}, {'timbre': 0, 'transpose': 24},
                           {'timbre': 1, 'bpm': 0}, {'timbre': 1, 'velocity': 0},
                           {'timbre': 1, 'gate': 0}, {'timbre': 1, 'start_bar': 35}):
            with self.assertRaises(ValueError):
                make_plan(**parameters)
        self.assertEqual(note_frame(1, 76, 100, True), bytes.fromhex('a5 05 4c 64 01 89'))
        self.assertEqual(note_frame(3, 76, 100, True), bytes.fromhex('a5 08 4c 64 01 84'))

    def test_release_precedes_same_time_attack_at_full_gate(self):
        events = make_plan(1, gate=1).events
        same_time = [event for event in events if abs(event.at - 0.15) < 1e-9]
        self.assertEqual([event.on for event in same_time], [False, True])


class PlayerTests(unittest.TestCase):
    def setUp(self):
        self.clock = VirtualClock()
        self.packets = []
        self.player = CommandPlayer(self.send, self.clock.schedule, self.clock.cancel, clock=self.clock.clock)

    def send(self, data):
        self.packets.append(data)
        return True

    def test_complete_song_sends_every_attack_and_release_without_other_commands(self):
        plan = make_plan(1)
        self.player.play(plan)
        self.clock.advance(plan.duration + 1)
        self.assertEqual(self.packets, [event.frame for event in plan.events if event.frame])
        self.assertEqual(self.player.state, 'stopped')
        self.assertEqual(self.player.message, '播放完成')

    def test_stop_releases_held_note_and_cancels_future_attacks(self):
        self.player.play(make_plan(3))
        self.assertEqual(len(self.packets), 1)
        self.player.stop()
        self.assertEqual(len(self.packets), 2)
        self.assertEqual(self.packets[-1][1], 0x08)
        self.assertEqual(self.packets[-1][4], 0)
        self.clock.advance(200)
        self.assertEqual(len(self.packets), 2)

    def test_pause_releases_then_resume_restores_remaining_note(self):
        self.player.play(make_plan(1))
        self.clock.advance(0.05)
        self.player.pause()
        self.assertEqual(self.player.state, 'paused')
        self.assertEqual(self.packets[-1][4], 0)
        self.clock.advance(5)
        self.assertEqual(len(self.packets), 2)
        self.player.resume()
        self.assertEqual(self.packets[-1][4], 1)
        self.clock.advance(0.08)
        self.assertEqual(self.packets[-1][4], 0)

    def test_guitar_pause_stop_never_send_mode_or_panic(self):
        self.player.play(make_plan(0))
        self.player.pause()
        self.player.resume()
        self.player.stop()
        self.assertEqual(len(self.packets), 1)
        self.assertEqual(self.packets[0][1], 0x02)

    def test_pause_after_overdue_release_does_not_restore_an_expired_note(self):
        self.player.play(make_plan(1))
        self.clock.now = 0.14
        self.player.pause()
        self.assertEqual([packet[4] for packet in self.packets], [1, 0])
        self.player.resume()
        self.assertEqual([packet[4] for packet in self.packets], [1, 0, 0])
        self.clock.advance(0.011)
        self.assertEqual(self.packets[-1][4], 1)

    def test_restart_cancels_old_plan(self):
        self.player.play(make_plan(1))
        self.clock.advance(0.05)
        next_plan = make_plan(1, start_bar=34, score_repeat=False)
        self.player.play(next_plan)
        self.packets.clear()
        self.clock.advance(next_plan.duration + 1)
        self.assertEqual(self.packets, [event.frame for event in next_plan.events if event.frame][1:])
        self.assertEqual(self.player.message, '播放完成')

    def test_failed_send_stops_without_scheduling_more(self):
        self.player.send = lambda data: False
        self.assertFalse(self.player.play(make_plan(1)))
        self.assertEqual(self.player.state, 'stopped')
        self.assertFalse(self.clock.jobs)

    def test_late_callback_does_not_dump_backlogged_notes(self):
        self.player.play(make_plan(1))
        when, token, callback = heapq.heappop(self.clock.jobs)
        self.clock.now = when + 1
        callback()
        self.assertEqual(self.player.state, 'stopped')
        self.assertIn('调度延迟', self.player.message)
        self.assertEqual(len(self.packets), 2)
        self.assertEqual(self.packets[-1][4], 0)


class SendBoundaryTests(unittest.TestCase):
    def test_panel_writes_directly_without_auto_switching_interface(self):
        from song_panel import SongPanel
        packets = []
        port = SimpleNamespace(is_open=True, write=lambda data: packets.append(data) or len(data))
        controller = SimpleNamespace(port=port, current_timbre=1, draw_upload_busy=False, log=lambda message: None)
        panel = SimpleNamespace(controller=controller, player=SimpleNamespace(plan=make_plan(1)))
        self.assertTrue(SongPanel._send(panel, note_frame(1, 76, 100, True)))
        self.assertEqual([packet[1] for packet in packets], [0x05])
        controller.draw_upload_busy = True
        self.assertFalse(SongPanel._send(panel, b'ignored'))
        controller.draw_upload_busy = False
        controller.current_timbre = 3
        self.assertFalse(SongPanel._send(panel, b'ignored'))
        self.assertEqual(len(packets), 1)


if __name__ == '__main__':
    unittest.main()
