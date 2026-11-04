from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from arrangement_model import (Automation, BAR, Clip, History, Note, PARAMETERS, PPQ,
                               Point, Project, Track, demo_project, duplicate_clip, snap)
from arrangement_playback import ArrangementPlayer, compile_plan, parameter_frames, score_notes


def one_track(instrument='piano', notes=None):
    return Project(tracks=[Track(instrument=instrument, clips=[Clip(notes=notes or [Note()])])])


class ModelTests(unittest.TestCase):
    def test_demo_roundtrip_and_hardware_plan(self):
        project = demo_project()
        restored = Project.from_dict(project.to_dict())
        self.assertEqual(project, restored)
        self.assertTrue(compile_plan(restored, True).hardware)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '测试.tang.json'
            project.save(path)
            project.bpm = 123
            project.save(path)
            self.assertEqual(project, Project.load(path))
            self.assertEqual(len(list(Path(folder).iterdir())), 1)

    def test_wrong_format_and_unknown_field(self):
        for version in ('anything', None):
            data = demo_project().to_dict()
            if version is None:
                del data['format']
            else:
                data['format'] = version
            with self.assertRaises(ValueError):
                Project.from_dict(data)
        data = demo_project().to_dict()
        data['executable'] = 'not allowed'
        with self.assertRaises(ValueError):
            Project.from_dict(data)

    def test_invalid_file_does_not_become_project(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.json'
            for content in ('[]', '{', 'null', '{"format":"tang-arrangement-v1"}'):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    Project.load(path)

    def test_bounded_integer_fields(self):
        for field, value in [('bpm', True), ('bpm', 0), ('bpm', 301), ('bpm', float('nan')),
                             ('bars', 0), ('bars', 257), ('loop_end', 0)]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                project = demo_project()
                setattr(project, field, value)
                project.validate()

    def test_duplicate_id_and_notes_outside_clip(self):
        for change in ('id', 'start', 'duration', 'velocity', 'pitch'):
            project = one_track()
            note = project.tracks[0].clips[0].notes[0]
            setattr(note, change, {'id': project.tracks[0].id, 'start': BAR, 'duration': BAR + 1,
                                   'velocity': 0, 'pitch': 128}[change])
            with self.subTest(change=change), self.assertRaises(ValueError):
                project.validate()

    def test_drum_indices_and_track_attributes(self):
        for instrument, pitch in [('drums', 12), ('drums', -1), ('no such synth', 60)]:
            with self.assertRaises(ValueError):
                one_track(instrument, [Note(pitch=pitch)]).validate()
        project = one_track()
        project.tracks[0].muted = 1
        with self.assertRaises(ValueError):
            project.validate()

    def test_history_undo_redo_and_atomic_rollback(self):
        history = History(demo_project())
        original = deepcopy(history.project)
        history.edit(lambda project: setattr(project, 'bpm', 130))
        history.undo()
        self.assertEqual(history.project, original)
        history.redo()
        self.assertEqual(history.project.bpm, 130)
        with self.assertRaises(ValueError):
            history.edit(lambda project: setattr(project, 'bpm', 900))
        self.assertEqual(history.project.bpm, 130)
        history.undo()
        history.edit(lambda project: setattr(project, 'bpm', 140))
        self.assertFalse(history.redo_stack)

    def test_copy_rekeys_all_events(self):
        clip = one_track().tracks[0].clips[0]
        copy = duplicate_clip(clip, BAR)
        self.assertNotEqual(copy.id, clip.id)
        self.assertNotEqual(copy.notes[0].id, clip.notes[0].id)
        self.assertEqual(copy.start, BAR)

    def test_mute_solo_and_zero_track_level(self):
        project = demo_project()
        project.tracks[0].solo = True
        self.assertEqual([track.instrument for track in project.active_tracks()], ['piano'])
        project.tracks[0].muted = True
        self.assertEqual(len(project.active_tracks()), 4)
        project.tracks[1].level = 0
        self.assertEqual(len(project.active_tracks()), 3)

    def test_snap(self):
        self.assertEqual(snap(-50, 120), 0)
        self.assertEqual(snap(59, 120), 0)
        self.assertEqual(snap(60, 120), 120)

    def test_automation_chase_and_interpolation(self):
        lane = Automation('space.delay_mix', 'linear', [Point(480, 20), Point(960, 40)])
        self.assertEqual(lane.value_at(0, 5), 5)
        self.assertEqual(lane.value_at(480, 5), 20)
        self.assertEqual(lane.value_at(720, 5), 30)
        self.assertEqual(lane.value_at(1000, 5), 40)
        lane.interpolation = 'step'
        self.assertEqual(lane.value_at(720, 5), 20)

    def test_automation_validation(self):
        for lane in [Automation('space.delay_feedback', points=[Point(0, 97)]),
                     Automation('space.delay_mix', points=[Point(0, 1), Point(0, 2)]),
                     Automation('guitar.amp', 'linear', [Point(0, 1)]),
                     Automation('unknown'), Automation(points=[Point(-1, 0)])]:
            project = one_track()
            project.automation = [lane]
            with self.subTest(lane=lane), self.assertRaises(ValueError):
                project.validate()


class CompilerTests(unittest.TestCase):
    def test_simultaneous_piano_chord_has_independent_attacks_and_releases(self):
        project = one_track(notes=[Note(pitch=pitch) for pitch in (60, 64, 67, 72)])
        plan = compile_plan(project, True)
        attacks = [event for event in plan.events if event.kind == 'on']
        releases = [event for event in plan.events if event.kind == 'off']
        self.assertEqual(len(attacks), 4)
        self.assertEqual(len(releases), 4)
        self.assertTrue(all(event.at == 0 for event in attacks))
        self.assertEqual({event.data[2] for event in attacks}, {60, 64, 67, 72})
        self.assertTrue(all(event.data[1] == 5 and event.data[4] == 0 for event in releases))

    def test_master_timbres_overlap_is_rejected_not_silently_switched(self):
        project = one_track()
        project.tracks.append(Track('violin', clips=[Clip(notes=[Note(pitch=67)])]))
        self.assertTrue(compile_plan(project).events)
        with self.assertRaisesRegex(ValueError, '主音色互斥'):
            compile_plan(project, True)

    def test_drums_overlay_and_velocity_scale(self):
        project = one_track()
        project.tracks[0].level = 50
        project.tracks.append(Track('drums', clips=[Clip(notes=[Note(pitch=0)])]))
        plan = compile_plan(project, True)
        attacks = [event for event in plan.events if event.kind == 'on']
        self.assertEqual({event.data[1] for event in attacks}, {5, 0x50})
        self.assertEqual(next(event for event in attacks if event.note.instrument == 'piano').note.velocity, 50)

    def test_cross_track_same_pitch_rejected(self):
        project = one_track()
        project.tracks.append(Track(clips=[Clip(notes=[Note()])]))
        with self.assertRaisesRegex(ValueError, '相同音高'):
            compile_plan(project, True)

    def test_limits_are_actual_instrument_limits_not_unlimited_tracks(self):
        for instrument, pitches in [('piano', range(40, 57)), ('violin', (60, 64)),
                                    ('bass', range(28, 37)), ('guitar', [40] * 33)]:
            with self.subTest(instrument=instrument), self.assertRaisesRegex(ValueError, '声部上限'):
                compile_plan(one_track(instrument, [Note(pitch=pitch) for pitch in pitches]), True)

    def test_guitar_and_bass_have_no_individual_note_off(self):
        for instrument, pitch in [('guitar', 40), ('bass', 28)]:
            plan = compile_plan(one_track(instrument, [Note(pitch=pitch)]), True)
            self.assertEqual(next(event.data[1] for event in plan.events if event.kind == 'on'), 2)
            self.assertEqual(next(event.data for event in plan.events if event.kind == 'off'), b'')

    def test_out_of_range_rejected_but_can_be_edited_offline(self):
        for instrument, pitch in [('guitar', 10), ('bass', 80), ('piano', 20), ('violin', 54)]:
            project = one_track(instrument, [Note(pitch=pitch)])
            self.assertTrue(compile_plan(project).events)
            with self.assertRaises(ValueError):
                compile_plan(project, True)

    def test_boundary_off_then_switch_then_on(self):
        project = one_track(notes=[Note(0, PPQ, 60)])
        project.tracks.append(Track('violin', clips=[Clip(notes=[Note(PPQ, PPQ, 67)])]))
        plan = compile_plan(project, True)
        boundary = [event.kind for event in plan.events if event.at == 60 / project.bpm]
        self.assertEqual(boundary, ['off', 'timbre', 'on'])

    def test_seek_chases_piano_and_effects_but_does_not_repluck_guitar(self):
        project = one_track(notes=[Note(0, 2 * PPQ)])
        project.automation = [Automation('space.delay_mix', 'linear', [Point(0, 0), Point(2 * PPQ, 100)])]
        plan = compile_plan(project, True, PPQ)
        self.assertEqual(next(event.at for event in plan.events if event.kind == 'on'), 0)
        fx = next(event.data for event in plan.events if event.kind == 'effects')
        delay = next(fx[offset:offset + 6] for offset in range(0, len(fx), 6) if fx[offset + 1] == 0x61)
        self.assertEqual(delay[2], 50)
        guitar = one_track('guitar', [Note(0, 2 * PPQ, 40)])
        self.assertFalse(any(event.kind == 'on' for event in compile_plan(guitar, True, PPQ).events))

    def test_frames_are_checksummed_and_fx_commit_is_contiguous(self):
        current = {key: spec[3] for key, spec in PARAMETERS.items()}
        data = parameter_frames(None, current)
        opcodes = []
        for offset in range(0, len(data), 6):
            frame = data[offset:offset + 6]
            checksum = 0
            for byte in frame:
                checksum ^= byte
            self.assertEqual(checksum, 0)
            opcodes.append(frame[1])
        self.assertEqual(opcodes[-5:], [0x40, 0x41, 0x42, 0x43, 0x44])
        self.assertEqual(parameter_frames(current, current), b'')

    def test_plan_range_and_automation_before_attack(self):
        project = one_track()
        for start, end in [(0, 0), (-1, BAR), (0, project.length + 1)]:
            with self.assertRaises(ValueError):
                compile_plan(project, start_tick=start, end_tick=end)
        plan = compile_plan(project, True)
        events = [event.kind for event in plan.events if event.at == 0]
        self.assertLess(events.index('effects'), events.index('on'))

    def test_same_pitch_retrigger_at_boundary_allowed(self):
        plan = compile_plan(one_track(notes=[Note(0, PPQ), Note(PPQ, PPQ)]), True)
        events = [event for event in plan.events if event.at == 60 / 110]
        self.assertEqual([event.kind for event in events], ['off', 'on'])

    def test_mute_removes_hardware_conflict(self):
        project = one_track()
        project.tracks.append(Track('violin', muted=True, clips=[Clip(notes=[Note(pitch=67)])]))
        self.assertTrue(compile_plan(project, True).hardware)

    def test_serial_density_guard(self):
        notes = [Note(index, 1, 60) for index in range(300)]
        with self.assertRaisesRegex(ValueError, '串口命令过密'):
            compile_plan(one_track(notes=notes), True)


class Clock:
    def __init__(self):
        self.now = 0.0
        self.jobs = {}
        self.counter = 0

    def schedule(self, milliseconds, callback):
        self.counter += 1
        self.jobs[self.counter] = (self.now + milliseconds / 1000, callback)
        return self.counter

    def cancel(self, token):
        self.jobs.pop(token, None)

    def advance(self, duration):
        ending = self.now + duration
        while self.jobs:
            token = min(self.jobs, key=lambda key: self.jobs[key][0])
            at, callback = self.jobs[token]
            if at > ending:
                break
            self.jobs.pop(token)
            self.now = at
            callback()
        self.now = ending


class PlayerTests(unittest.TestCase):
    def player(self, send=None):
        clock = Clock()
        sent = []
        player = ArrangementPlayer(send or (lambda data: sent.append(data) or True), clock.schedule,
                                   clock.cancel, clock=lambda: clock.now)
        return player, clock, sent

    def test_silent_preview_never_sends_even_with_send_callback(self):
        player, clock, sent = self.player()
        player.play(compile_plan(one_track(), end_tick=BAR))
        clock.advance(3)
        self.assertEqual(player.state, 'stopped')
        self.assertEqual(sent, [])
        self.assertFalse(clock.jobs)

    def test_polyphonic_stop_releases_every_active_key_and_cancels_callbacks(self):
        player, clock, sent = self.player()
        player.play(compile_plan(one_track(notes=[Note(pitch=pitch) for pitch in (60, 64, 67)]), True))
        self.assertEqual(len(player.active), 3)
        player.stop()
        self.assertFalse(clock.jobs)
        releases = [data[2] for data in sent if data[1] == 5 and data[4] == 0]
        self.assertEqual(set(releases), {60, 64, 67})
        count = len(sent)
        clock.advance(10)
        self.assertEqual(len(sent), count)

    def test_late_callback_stops_without_bursting_missed_attacks(self):
        player, clock, sent = self.player()
        project = one_track(notes=[Note(0, 120), Note(240, 120, 64), Note(480, 120, 67)])
        player.play(compile_plan(project, True))
        callback = next(iter(clock.jobs.values()))[1]
        clock.now = 1
        callback()
        self.assertEqual(player.state, 'stopped')
        self.assertIn('150ms', player.message)
        self.assertEqual(len([data for data in sent if data[1] == 5 and data[4] == 1]), 1)

    def test_loop_restarts_with_no_stuck_notes(self):
        player, clock, sent = self.player()
        plan = compile_plan(one_track(notes=[Note(0, 120)]), True, 0, PPQ)
        player.play(plan, loop=True)
        clock.advance(1.2)
        self.assertEqual(player.state, 'playing')
        self.assertEqual(len([data for data in sent if data[1] == 5 and data[4] == 1]), 3)
        player.stop()
        self.assertFalse(clock.jobs)

    def test_send_failure_aborts(self):
        player, clock, _ = self.player(lambda data: False)
        self.assertFalse(player.play(compile_plan(one_track(), True)))
        self.assertEqual(player.state, 'stopped')
        self.assertFalse(clock.jobs)

    def test_stale_callback_cannot_send_after_restart(self):
        player, clock, sent = self.player()
        plan = compile_plan(one_track(), True)
        player.play(plan)
        callback = next(iter(clock.jobs.values()))[1]
        player.stop()
        player.play(plan)
        before = len(sent)
        callback()
        self.assertEqual(len(sent), before)
        player.stop()


if __name__ == '__main__':
    unittest.main()
