import hashlib
import json
from pathlib import Path
import unittest

from build_library import ROOT
from demo_headroom import with_headroom
from arrangement_model import Project, demo_project, ensemble_demo_project
from arrangement_playback import compile_plan, score_notes


class DemoHeadroomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt = json.loads((ROOT / 'headroom_baseline.json').read_text(encoding='utf-8'))
        cls.originals = Path(receipt['backup']) / 'Music_Demos/projects'
        cls.hashes = receipt['original_projects']

    def test_all_twenty_projects_only_halve_bus_parameters_and_automation(self):
        self.assertEqual(len(self.hashes), 20)
        for name, expected in self.hashes.items():
            with self.subTest(project=name):
                original_path = self.originals / name
                self.assertEqual(hashlib.sha256(original_path.read_bytes()).hexdigest(), expected)
                original = Project.load(original_path)
                actual = Project.load(ROOT / 'projects' / name)
                self.assertEqual(actual, with_headroom(original))
                self.assertEqual(score_notes(actual), score_notes(original))
                self.assertEqual(actual.tracks, original.tracks)

    def test_bus_zero_fade_and_relative_leads_are_preserved(self):
        for name in self.hashes:
            original = Project.load(self.originals / name)
            actual = Project.load(ROOT / 'projects' / name)
            for target, value in original.parameters.items():
                self.assertEqual(actual.parameters[target], value // 2 if target.startswith('bus.') else value)
            for before, after in zip(original.automation, actual.automation):
                self.assertEqual(before.target, after.target)
                self.assertEqual(before.interpolation, after.interpolation)
                for original_point, actual_point in zip(before.points, after.points):
                    self.assertEqual(original_point.tick, actual_point.tick)
                    self.assertEqual(actual_point.value,
                        original_point.value // 2 if before.target.startswith('bus.') else original_point.value)

    def test_actual_start_and_seek_packets_cannot_restore_loud_bus_presets(self):
        for name in self.hashes:
            project = Project.load(ROOT / 'projects' / name)
            for start_tick in (0, project.length // 2):
                plan = compile_plan(project, hardware=True, ensemble=True, start_tick=start_tick)
                levels = []
                for event in plan.events:
                    if event.kind != 'effects':
                        continue
                    for offset in range(0, len(event.data), 6):
                        packet = event.data[offset:offset + 6]
                        if packet[1] == 0x70:
                            levels.append(packet[3])
                self.assertGreaterEqual(len(levels), 5)
                self.assertLessEqual(max(levels), 63)

    def test_conversion_does_not_modify_the_source_score(self):
        original = Project.load(self.originals / next(iter(self.hashes)))
        snapshot = original.to_dict()
        quiet = with_headroom(original)
        self.assertEqual(original.to_dict(), snapshot)
        self.assertIsNot(quiet, original)
        self.assertIsNot(quiet.automation[0], original.automation[0])

    def test_builtin_demo_presets_are_quiet_but_manual_defaults_are_unchanged(self):
        for factory in (demo_project, ensemble_demo_project):
            demo = factory()
            for target in demo.parameters:
                if target.startswith('bus.'):
                    self.assertEqual(demo.parameters[target], 50)
        self.assertTrue(all(value == 100 for target, value in Project().parameters.items()
                            if target.startswith('bus.')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
