import hashlib
import json
import unittest

from build_library import ROOT
from demo_library import load_song
from fuji_arrangement import compose_fuji
from fuji_violin_harmony import compose_fuji_violin, fuji_violin_short
from arrangement_model import BAR, PPQ, Project
from arrangement_playback import ArrangementPlayer, compile_plan, score_notes
from test_arrangement import Clock
import test_arrangement_ui as interface_tests


class FujiViolinTests(unittest.TestCase):
    def test_piano_melody_is_identical_to_the_previous_version(self):
        before, after = compose_fuji(), compose_fuji_violin()
        self.assertEqual(before.tracks[0], after.tracks[0])
        self.assertEqual(before.bpm, after.bpm)

    def test_main_harmony_moves_from_piano_to_violin(self):
        before, after = compose_fuji(), compose_fuji_violin()
        self.assertEqual([clip for clip in before.tracks[1].clips if clip.start < 9 * BAR],
                         [clip for clip in after.tracks[1].clips if clip.start < 9 * BAR])
        late = [note for clip in after.tracks[1].clips if clip.start >= 9 * BAR for note in clip.notes]
        self.assertEqual(len(late), 36)
        self.assertTrue(all(note.pitch <= 48 for note in late))
        violin_before = sum(len(clip.notes) for clip in before.tracks[3].clips)
        violin_after = sum(len(clip.notes) for clip in after.tracks[3].clips)
        self.assertGreater(violin_after, violin_before * 5)
        guitar_before = sum(len(clip.notes) for clip in before.tracks[2].clips)
        guitar_after = sum(len(clip.notes) for clip in after.tracks[2].clips)
        self.assertLess(guitar_after, guitar_before / 3)

    def test_bow_line_is_continuous_but_never_polyphonic(self):
        notes = sorted((note for note in score_notes(compose_fuji_violin()) if note.instrument == 'violin'),
                       key=lambda note: note.start)
        self.assertEqual(notes[0].start, 9 * BAR)
        self.assertEqual(notes[-1].end, 45 * BAR)
        self.assertTrue(all(60 <= note.pitch <= 74 for note in notes))
        self.assertTrue(all(left.end == right.start for left, right in zip(notes, notes[1:])))
        self.assertGreater(len({note.pitch for note in notes}), 5)
        self.assertTrue(compile_plan(compose_fuji_violin(), True, ensemble=True))

    def test_violin_is_audible_background_and_bus_sum_has_margin(self):
        project = compose_fuji_violin()
        values = {lane.target: max(point.value for point in lane.points) for lane in project.automation}
        self.assertEqual(values['bus.piano'], 54)
        self.assertEqual(values['bus.violin'], 28)
        self.assertEqual(values['bus.guitar'], 12)
        self.assertLess(sum(values.values()), 127)
        self.assertEqual((values['bus.bass'], values['bus.drums']), (0, 0))

    def test_old_projects_including_the_original_fuji_are_preserved(self):
        proof = json.loads((ROOT / 'fuji_violin_validation.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(proof['previous_projects']), 26)
        for name, expected in proof['previous_projects'].items():
            self.assertEqual(hashlib.sha256((ROOT / 'projects' / name).read_bytes()).hexdigest(), expected)

    def test_full_and_short_play_to_completion_and_clear_active_notes(self):
        full = compose_fuji_violin()
        for variant, expected, duration in (('full', full, 94), ('short', fuji_violin_short(full), 16)):
            saved = Project.load(ROOT / 'projects' / f'p05_fuji_violin_{variant}.tang.json')
            self.assertEqual(saved, expected)
            plan = compile_plan(saved, True, ensemble=True)
            clock = Clock()
            player = ArrangementPlayer(lambda data: True, clock.schedule, clock.cancel, clock=lambda: clock.now,
                                       batch_simultaneous=True)
            player.play(plan)
            clock.advance(duration + plan.preparation_seconds + .1)
            self.assertEqual(player.state, 'stopped')
            self.assertFalse(player.active)
            self.assertFalse(clock.jobs)

    def test_launchers_select_the_new_version(self):
        for name in ('打开富士山下小提琴和声.cmd', '打开富士山下小提琴和声短试听.cmd'):
            self.assertIn('-Song p05_fuji_violin', (ROOT.parent / name).read_text(encoding='ascii'))

    def test_hidden_ui_loads_the_new_harmony_without_autoplay(self):
        harness = interface_tests.ArrangementInterfaceTests()
        with harness.application() as (app, panel):
            port = interface_tests.MemoryPort()
            app.port = port
            self.assertTrue(load_song(app, 'p05_fuji_violin', 'short'))
            self.assertIn('小提琴和声', panel.status.get())
            self.assertFalse(panel.hardware.get())
            self.assertEqual(port.writes, [])


if __name__ == '__main__':
    unittest.main()
