import hashlib
import json
from pathlib import Path
import unittest

from build_library import ROOT, neon
from demo_library import load_song, read_catalog
from arrangement_model import BAR, PPQ, Project
from arrangement_playback import ArrangementPlayer, compile_plan, score_notes
from shanhai_arrangement import PROFILE, compose_shanhai, shanhai_short, VOICINGS
from shanhai_score import CHORDS, MELODY, SHEET_ROWS, degree_pitch, melody_notes
from test_arrangement import Clock
import test_arrangement_ui as interface_tests


class ShanhaiTests(unittest.TestCase):
    def test_printed_page_bar_ranges_and_capo_pitch_are_retained(self):
        bars = [bar for page, row, first, last in SHEET_ROWS for bar in range(first, last + 1)]
        self.assertEqual(bars, list(range(1, 71)))
        self.assertEqual((len(CHORDS), len(MELODY)), (70, 70))
        self.assertEqual(CHORDS[:5], ['F/C+G', 'Am', 'F/C+G', 'Am', 'F'])
        self.assertEqual((degree_pitch('1'), degree_pitch('l5'), degree_pitch('h5')), (64, 59, 83))
        self.assertEqual(degree_pitch('7'), 75)  # Page 3's 7 is not upper-octave 7.
        self.assertEqual(VOICINGS['Am'], (49, 56, 61, 64))  # C#m after capo +4.

    def test_actual_uploaded_page_hashes_and_previous_projects_are_preserved(self):
        proof = json.loads((ROOT / 'shanhai_validation.json').read_text(encoding='utf-8'))
        self.assertEqual(len(proof['score_pages']), 3)
        for name, expected in proof['score_pages'].items():
            path = ROOT / 'source_scores/shanhai_user_pages' / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
        self.assertGreaterEqual(len(proof['previous_projects']), 22)
        for name, expected in proof['previous_projects'].items():
            self.assertEqual(hashlib.sha256((ROOT / 'projects' / name).read_bytes()).hexdigest(), expected)

    def test_melody_first_phrase_and_high_climax_fit_existing_guitar(self):
        notes = melody_notes()
        self.assertEqual([note['pitch'] for note in notes[:3]], [59, 68, 66])
        self.assertEqual(notes[0]['start'], 4 * 16 + 6)
        self.assertEqual(notes[0]['end'], 4 * 16 + 10)  # Tied B3 eighths.
        self.assertTrue(any(note['end'] - note['start'] >= 32 for note in notes))
        self.assertTrue(all(40 <= note['pitch'] <= 84 for note in notes))
        self.assertEqual(max(note['pitch'] for note in notes), 83)
        self.assertTrue(all(left['end'] <= right['start'] for left, right in zip(notes, notes[1:])))

    def test_every_transcribed_melody_attack_remains_in_guitar_lead(self):
        project = compose_shanhai()
        attacks = {(clip.start + note.start, note.pitch) for clip in project.tracks[0].clips for note in clip.notes}
        for source in melody_notes():
            self.assertIn((round(source['start'] * PPQ / 4), source['pitch']), attacks)
        self.assertEqual(project.tracks[0].instrument, 'guitar')
        self.assertLess(project.guitar_sustain, 60)
        # Re-picking sustains the printed eight-beat tie through a short envelope.
        held = next(source for source in melody_notes() if source['end'] - source['start'] >= 32)
        times = sorted(tick for tick, pitch in attacks if pitch == held['pitch'] and
                       held['start'] * PPQ / 4 <= tick < held['end'] * PPQ / 4)
        self.assertGreater(len(times), 5)
        self.assertLessEqual(max(right - left for left, right in zip(times, times[1:])), PPQ * .875)

    def test_drum_bus_and_backbeat_are_stronger_without_boosting_all_buses(self):
        project = compose_shanhai()
        old = Project.load(ROOT / 'projects/g02_spark_switch_full.tang.json')
        lane = next(lane for lane in project.automation if lane.target == 'bus.drums')
        self.assertEqual(lane.value_at(5 * BAR, 0), 62)
        self.assertEqual(lane.value_at(53 * BAR, 0), 76)
        self.assertGreater(lane.value_at(53 * BAR, 0), old.parameters['bus.drums'] * 2)
        self.assertLessEqual(project.parameters['bus.guitar'], old.parameters['bus.guitar'])
        drums = [note for clip in project.tracks[6].clips for note in clip.notes]
        self.assertGreaterEqual(max(note.velocity for note in drums if note.pitch == 0), 116)
        self.assertGreaterEqual(max(note.velocity for note in drums if note.pitch == 1), 118)

    def test_piano_violin_stay_background_and_all_five_engines_overlap(self):
        project = compose_shanhai()
        lead = sum(len(clip.notes) for clip in project.tracks[0].clips)
        violin = sum(len(clip.notes) for clip in project.tracks[5].clips)
        self.assertGreater(lead, violin * 10)
        for target, maximum in (('bus.piano', 18), ('bus.violin', 12)):
            lane = next(lane for lane in project.automation if lane.target == target)
            self.assertLessEqual(max(point.value for point in lane.points), maximum)
        report = neon.analyze(project)
        self.assertEqual(report['simultaneous_instrument_types'], 5)
        self.assertLessEqual(report['gated_peak_voices']['violin'], 1)
        self.assertLessEqual(report['tail_load_estimate_not_measured']['guitar']['peak_attacks_in_window'], 26)

    def test_full_and_short_are_reproducible_with_finite_stopped_playback(self):
        project = compose_shanhai()
        for variant, expected in (('full', project), ('short', shanhai_short(project))):
            actual = Project.load(ROOT / 'projects' / f'g03_shanhai_{variant}.tang.json')
            self.assertEqual(actual, expected)
            plan = compile_plan(actual, True, ensemble=True)
            self.assertEqual(plan.duration, 180 if variant == 'full' else 20)
            self.assertTrue(plan.preparation)
            clock, sent = Clock(), []
            player = ArrangementPlayer(lambda data: sent.append(data) or True, clock.schedule, clock.cancel,
                                       clock=lambda: clock.now, batch_simultaneous=True)
            player.play(plan)
            clock.advance(plan.duration + plan.preparation_seconds + .1)
            self.assertEqual(player.state, 'stopped')
            self.assertFalse(player.active)
            self.assertFalse(clock.jobs)
        self.assertEqual(project, compose_shanhai())

    def test_short_version_quotes_six_chorus_bars_then_resolves(self):
        project = compose_shanhai()
        short = shanhai_short(project)
        original = {(clip.start + note.start - 51 * BAR, note.pitch, note.velocity)
                    for clip in project.tracks[0].clips if 51 * BAR <= clip.start < 57 * BAR for note in clip.notes}
        excerpt = {(clip.start + note.start, note.pitch, note.velocity)
                   for clip in short.tracks[0].clips if clip.start < 6 * BAR for note in clip.notes}
        self.assertEqual(original, excerpt)
        self.assertEqual(short.tracks[0].clips[-1].notes[0].pitch, 73)
        self.assertFalse(any(note.start >= 7 * BAR for note in score_notes(short)))

    def test_working_score_is_credited_and_launchers_use_current_workspace(self):
        entry = next(song for song in read_catalog() if song['id'] == PROFILE['id'])
        self.assertFalse(entry['original'])
        self.assertIn('草东没有派对', entry['attribution'])
        self.assertIn('无限延音', entry['attribution'])
        for name in ('打开山海吉他鼓组Demo.cmd', '打开山海短试听.cmd'):
            contents = (ROOT.parent / name).read_text(encoding='ascii')
            self.assertIn('%~dp0Music_Demos\\launch_library.ps1', contents)
            self.assertIn('-Song g03_shanhai', contents)

    def test_real_hidden_ui_loads_both_versions_and_reports_custom_drum_mix(self):
        harness = interface_tests.ArrangementInterfaceTests()
        with harness.application() as (app, panel):
            port = interface_tests.MemoryPort()
            app.port = port
            for variant in ('full', 'short'):
                self.assertTrue(load_song(app, PROFILE['id'], variant))
                self.assertIn('鼓组增强', panel.status.get())
                self.assertNotIn('50%', panel.status.get())
                self.assertEqual(panel.guitar_sustain.get(), 52)
                self.assertFalse(panel.hardware.get())
                self.assertEqual(panel.player.state, 'stopped')
                self.assertFalse(port.writes)


if __name__ == '__main__':
    unittest.main()
