from copy import deepcopy
import hashlib
import json
import unittest

from build_library import ROOT
from demo_library import load_song
from fuji_arrangement import compose_fuji
from fuji_violin_pad import compose_fuji_pad, fuji_pad_short, PAD_END
from arrangement_model import BAR, PPQ, Clip, Note, Project, Track
from arrangement_playback import ArrangementPlayer, compile_plan, score_notes
from melody_player import command_frame
from test_arrangement import Clock
import test_arrangement_ui as interface_tests


class FujiPadTests(unittest.TestCase):
    def test_both_piano_hands_are_preserved(self):
        before, after = compose_fuji(), compose_fuji_pad()
        self.assertEqual(before.tracks[0], after.tracks[0])
        self.assertEqual(before.tracks[1].clips, after.tracks[1].clips)
        self.assertEqual(before.tracks[1].level, after.tracks[1].level)

    def test_continuous_quiet_bow_has_recognizable_melodic_motion(self):
        project = compose_fuji_pad()
        notes = [note for note in score_notes(project) if note.instrument == 'violin']
        self.assertTrue(project.violin_legato)
        self.assertEqual(notes[0].start, BAR)
        self.assertEqual(notes[-1].end, PAD_END)
        self.assertGreater(len(notes), 150)
        self.assertTrue(all(a.end == b.start for a, b in zip(notes, notes[1:])))
        self.assertGreater(sum(note.end - note.start <= PPQ for note in notes), len(notes) // 2)
        self.assertTrue(all(60 <= note.pitch <= 77 and note.velocity <= 26 for note in notes))
        self.assertEqual([note.pitch for note in notes[:5]], [76, 77, 76, 74, 72])
        self.assertTrue(all(a.pitch != b.pitch for a, b in zip(notes, notes[1:])))
        self.assertEqual({note.instrument for note in score_notes(project)}, {'piano', 'violin'})
        lane = next(lane for lane in project.automation if lane.target == 'bus.violin')
        self.assertEqual(max(point.value for point in lane.points), 14)
        self.assertEqual(lane.value_at(PAD_END, 127), 0)

    def test_saved_full_and_short_chase_held_notes_without_gaps(self):
        full = compose_fuji_pad()
        for variant, expected in (('full', full), ('short', fuji_pad_short(full))):
            saved = Project.load(ROOT / 'projects' / f'p06_fuji_pad_{variant}.tang.json')
            self.assertEqual(saved, expected)
            notes = [note for note in score_notes(saved) if note.instrument == 'violin']
            self.assertTrue(all(a.end == b.start for a, b in zip(notes, notes[1:])))
            if variant == 'short':
                self.assertEqual(notes[0].start, 0)
                self.assertEqual(notes[0].pitch, 74)  # D5 at printed piano bar 28
            plan = compile_plan(saved, True, ensemble=True)
            self.assertEqual(plan.preparation, ())
            self.assertEqual(plan.duration, 16 if variant == 'short' else 94)
            ons = [event for event in plan.events if event.kind == 'on' and event.note.instrument == 'violin']
            offs = [event for event in plan.events if event.kind == 'off' and event.note.instrument == 'violin']
            self.assertEqual([event.data[4] for event in ons], [1] + [3] * (len(ons) - 1))
            self.assertTrue(all(event.data == b'' for event in offs[:-1]))
            self.assertEqual(offs[-1].data[4], 0)

    def test_old_projects_and_default_note_articulation_are_preserved(self):
        proof = json.loads((ROOT / 'fuji_pad_validation.json').read_text(encoding='utf-8'))
        self.assertEqual(len(proof['previous_projects']), 28)
        for name, expected in proof['previous_projects'].items():
            path = ROOT / 'projects' / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
            self.assertFalse(Project.load(path).violin_legato)
        data = compose_fuji().to_dict()
        data.pop('violin_legato')
        self.assertFalse(Project.from_dict(data).violin_legato)
        for invalid in (1, 'true', None):
            data['violin_legato'] = invalid
            with self.assertRaises(ValueError):
                Project.from_dict(data)

    def test_seek_inside_connected_phrase_starts_normally_and_stop_releases_current_pitch(self):
        project = compose_fuji_pad()
        start = 14 * BAR
        plan = compile_plan(project, True, start_tick=start, ensemble=True)
        ons = [event for event in plan.events if event.kind == 'on' and event.note.instrument == 'violin']
        self.assertEqual((ons[0].at, ons[0].data[4]), (0, 1))
        clock, sent = Clock(), []
        player = ArrangementPlayer(lambda data: sent.append(bytes(data)) or True, clock.schedule, clock.cancel,
                                   clock=lambda: clock.now, batch_simultaneous=True)
        player.play(plan)
        clock.advance(3)
        violin = next(event.note for event in player.active.values() if event.note.instrument == 'violin')
        player.stop()
        self.assertIn(command_frame(0x0d, violin.pitch, 1, 0), sent[-1])
        self.assertFalse(player.active)
        self.assertFalse(clock.jobs)

    def test_legato_only_connects_exact_boundaries_and_supports_legacy_violin_opcode(self):
        score = Project(bars=2, loop_end=2 * BAR, violin_legato=True, tracks=[
            Track('violin', clips=[Clip(length=2 * BAR, notes=[
                Note(0, PPQ, 60), Note(PPQ, PPQ, 62), Note(3 * PPQ, PPQ, 65)])])])
        for ensemble, opcode in ((False, 0x08), (True, 0x0d)):
            plan = compile_plan(score, True, ensemble=ensemble)
            ons = [event for event in plan.events if event.kind == 'on']
            offs = [event for event in plan.events if event.kind == 'off']
            self.assertEqual([event.data[4] for event in ons], [1, 3, 1])
            self.assertEqual([event.data[1] for event in ons], [opcode] * 3)
            self.assertEqual([bool(event.data) for event in offs], [False, True, True])
        score.violin_legato = False
        plan = compile_plan(score, True, ensemble=True)
        self.assertTrue(all(event.data[4] == 1 for event in plan.events if event.kind == 'on'))
        self.assertTrue(all(event.data for event in plan.events if event.kind == 'off'))

    def test_full_and_short_finish_with_one_physical_violin_release(self):
        full = compose_fuji_pad()
        for score in (full, fuji_pad_short(full)):
            clock, sent = Clock(), []
            player = ArrangementPlayer(lambda data: sent.append(bytes(data)) or True, clock.schedule, clock.cancel,
                                       clock=lambda: clock.now)
            plan = compile_plan(score, True, ensemble=True)
            player.play(plan)
            clock.advance(plan.duration + .1)
            releases = [packet for packet in sent if len(packet) == 6 and packet[1] == 0x0d and packet[4] == 0]
            self.assertEqual(len(releases), 1)
            self.assertEqual(player.state, 'stopped')
            self.assertFalse(player.active)
            self.assertFalse(clock.jobs)

    def test_hidden_ui_loads_and_retains_legato_without_autoplay(self):
        harness = interface_tests.ArrangementInterfaceTests()
        with harness.application() as (app, panel):
            port = interface_tests.MemoryPort()
            app.port = port
            self.assertTrue(load_song(app, 'p06_fuji_pad', 'short'))
            self.assertTrue(panel.violin_legato.get())
            self.assertFalse(panel.hardware.get())
            self.assertIn('提琴旋律衬底', panel.status.get())
            panel.apply_project()
            self.assertTrue(panel.project.violin_legato)
            self.assertFalse(port.writes)

    def test_supplied_violin_phrase_is_aligned_by_pickup_and_keeps_triplets(self):
        notes = [note for note in score_notes(compose_fuji_pad()) if note.instrument == 'violin']
        pickup = 9 * BAR + 7 * PPQ // 2
        phrase = [note for note in notes if pickup <= note.start < pickup + 5 * PPQ // 2]
        self.assertEqual([note.pitch for note in phrase], [60, 62, 65, 67, 65])
        self.assertEqual([note.end - note.start for note in phrase], [PPQ // 2] * 5)
        # Page 2 printed bar 62: D4, F4, G4 quarter-note triplet over two beats.
        triplet = [note for note in notes if 43 * BAR <= note.start < 43 * BAR + 2 * PPQ]
        self.assertEqual([note.pitch for note in triplet], [62, 65, 67])
        self.assertEqual([note.end - note.start for note in triplet], [320] * 3)


if __name__ == '__main__':
    unittest.main()
