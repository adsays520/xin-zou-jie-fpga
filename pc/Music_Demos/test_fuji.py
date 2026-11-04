import hashlib
import json
import unittest

from build_library import ROOT, neon
from demo_library import load_song, read_catalog
from fuji_score import SYSTEMS, hand_notes, midi
from fuji_arrangement import compose_fuji, fuji_short, normalized_piano
from arrangement_model import BAR, PPQ, Project
from arrangement_playback import ArrangementPlayer, compile_plan, score_notes
from test_arrangement import Clock
import test_arrangement_ui as interface_tests


class FujiTests(unittest.TestCase):
    def test_pdf_systems_cover_all_45_bars_and_both_hands_fit_piano(self):
        self.assertEqual([bar for _, _, first, last in SYSTEMS for bar in range(first, last + 1)], list(range(1, 46)))
        right, left = hand_notes('right'), hand_notes('left')
        self.assertEqual((len(right), len(left)), (288, 229))
        self.assertEqual([note['pitch'] for note in right[:2]], [midi('F5'), midi('F6')])
        self.assertEqual(max(note['pitch'] for note in right), midi('A6'))
        self.assertEqual(min(note['pitch'] for note in left), midi('C2'))
        self.assertTrue(all(21 <= note['pitch'] <= 108 for note in right + left))

    def test_key_signature_and_printed_naturals_are_not_lost(self):
        left = hand_notes('left')
        self.assertTrue(any(note['pitch'] == midi('B3') and note['source_bars'][0] == 25 for note in left))
        self.assertTrue(any(note['pitch'] == midi('B2') and note['source_bars'][0] == 33 for note in left))
        self.assertTrue(any(note['pitch'] == midi('B2') and set(note['source_bars']) == {41, 42} for note in left))
        self.assertTrue(any(note['pitch'] == midi('Bb2') and note['source_bars'][0] == 42 for note in left))
        self.assertEqual({note['pitch'] for note in left if note['start'] == 44 * 16 + 8}, {midi('F3'), midi('A3')})

    def test_cross_bar_ties_remain_held_and_each_source_attack_survives(self):
        self.assertTrue(any(note['pitch'] == midi('F5') and set(note['source_bars']) == {9, 10}
                            for note in hand_notes('right')))
        project = compose_fuji()
        expected = {(round(note['start'] * PPQ / 4), note['pitch'])
                    for hand in ('right', 'left') for note in hand_notes(hand)}
        actual = {(clip.start + note.start, note.pitch) for track in project.tracks[:2]
                  for clip in track.clips for note in clip.notes}
        self.assertEqual(expected, actual)

    def test_same_pitch_unisons_do_not_generate_stale_note_offs(self):
        normalized = normalized_piano()
        groups = {}
        for note in normalized:
            groups.setdefault(note['pitch'], []).append(note)
        for group in groups.values():
            group.sort(key=lambda note: note['start_tick'])
            for left, right in zip(group, group[1:]):
                self.assertLessEqual(left['end_tick'], right['start_tick'])
        # Real overlap in this sheet: LH F4 at bar17 and the RH F4 re-articulation.
        originals = [note for hand in ('right', 'left') for note in hand_notes(hand)]
        self.assertTrue(any(note['end_tick'] < round(note['end'] * PPQ / 4) for note in normalized))
        self.assertEqual(len(normalized), len(originals))

    def test_piano_remains_lead_and_the_other_instruments_are_background(self):
        project = compose_fuji()
        self.assertEqual([track.instrument for track in project.tracks], ['piano', 'piano', 'guitar', 'violin'])
        notes = score_notes(project)
        self.assertGreater(sum(note.instrument == 'piano' for note in notes), sum(note.instrument == 'guitar' for note in notes) * 4)
        self.assertLessEqual(sum(note.instrument == 'violin' for note in notes), 12)
        maxima = {lane.target: max(point.value for point in lane.points) for lane in project.automation}
        self.assertEqual(maxima['bus.piano'], 54)
        self.assertLessEqual(maxima['bus.guitar'], 23)
        self.assertLessEqual(maxima['bus.violin'], 15)
        self.assertLess(sum(maxima.values()), 127)
        self.assertEqual((maxima['bus.drums'], maxima['bus.bass']), (0, 0))
        self.assertEqual(project.parameters['guitar.amp'], 0)
        self.assertLess(project.guitar_sustain, 60)

    def test_source_pdf_and_all_previous_project_bytes_are_preserved(self):
        report = json.loads((ROOT / 'fuji_validation.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256((ROOT / report['source_pdf']).read_bytes()).hexdigest(), report['source_pdf_sha256'])
        self.assertGreaterEqual(len(report['previous_projects']), 24)
        for name, expected in report['previous_projects'].items():
            self.assertEqual(hashlib.sha256((ROOT / 'projects' / name).read_bytes()).hexdigest(), expected)

    def test_both_versions_are_reproducible_compile_and_stop_cleanly(self):
        full = compose_fuji()
        for variant, expected, seconds in (('full', full, 94), ('short', fuji_short(full), 16)):
            actual = Project.load(ROOT / 'projects' / f'p04_fuji_{variant}.tang.json')
            self.assertEqual(actual, expected)
            plan = compile_plan(actual, True, ensemble=True)
            self.assertEqual(plan.duration, seconds)
            self.assertEqual(actual.bpm, 120)
            report = neon.analyze(actual)
            self.assertEqual(report['simultaneous_instrument_types'], 3)
            self.assertLessEqual(report['gated_peak_voices']['piano'], 16)
            self.assertEqual(report['gated_peak_voices']['violin'], 1)
            self.assertLess(report['maximum_bytes_per_100ms'], 400)
            clock = Clock()
            player = ArrangementPlayer(lambda data: True, clock.schedule, clock.cancel, clock=lambda: clock.now,
                                       batch_simultaneous=True)
            player.play(plan)
            clock.advance(seconds + plan.preparation_seconds + .1)
            self.assertEqual(player.state, 'stopped')
            self.assertFalse(player.active)
            self.assertFalse(clock.jobs)

    def test_short_excerpt_has_a_final_f_major_chord_and_tail(self):
        project = fuji_short(compose_fuji())
        ending = [note for track in project.tracks[:2] for clip in track.clips for note in clip.notes if clip.start == 6 * BAR]
        self.assertEqual({note.pitch for note in ending}, {41, 53, 65, 69, 72})
        self.assertFalse(any(note.start >= 7 * BAR for note in score_notes(project)))

    def test_launchers_and_catalog_are_explicit_about_user_score(self):
        entry = next(song for song in read_catalog() if song['id'] == 'p04_fuji')
        self.assertFalse(entry['original'])
        self.assertTrue(entry['piano_lead'])
        self.assertFalse(entry['guitar_lead'])
        for name in ('打开富士山下钢琴合奏.cmd', '打开富士山下短试听.cmd'):
            body = (ROOT.parent / name).read_text(encoding='ascii')
            self.assertIn('%~dp0Music_Demos\\launch_library.ps1', body)
            self.assertIn('-Song p04_fuji', body)

    def test_real_hidden_ui_loads_piano_lead_without_sending(self):
        harness = interface_tests.ArrangementInterfaceTests()
        with harness.application() as (app, panel):
            port = interface_tests.MemoryPort()
            app.port = port
            for variant in ('full', 'short'):
                self.assertTrue(load_song(app, 'p04_fuji', variant))
                self.assertEqual(panel.project.bpm, 120)
                self.assertEqual(panel.guitar_sustain.get(), 48)
                self.assertIn('钢琴主导', panel.status.get())
                self.assertFalse(panel.hardware.get())
                self.assertFalse(port.writes)


if __name__ == '__main__':
    unittest.main()
