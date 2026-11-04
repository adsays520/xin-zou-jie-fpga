from collections import Counter
from copy import deepcopy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from build_library import APP, ROOT, PROFILES, compose, neon, short_version
from piano_scores import PIANO_PROFILES, compose_piano
from rock_scores import FORM as ROCK_FORM, ROCK_PROFILES, compose_rock
from demo_library import attach_library, load_song, project_path, read_catalog
from demo_headroom import with_headroom
from arrangement_model import BAR, Project
from arrangement_playback import ArrangementPlayer, compile_plan, score_notes
from test_arrangement import Clock


class LibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.songs = read_catalog()
        cls.projects = [(song, variant, Project.load(project_path(song, variant)))
                        for song in cls.songs for variant in ('full', 'short')]

    def test_sixteen_demos_with_piano_and_guitar_arrangements(self):
        self.assertEqual(len(self.songs), 16)
        self.assertEqual([song['id'] for song in self.songs[:3]], [profile['id'] for profile in PIANO_PROFILES])
        self.assertEqual(len({song['title'] for song in self.songs}), 16)
        self.assertTrue(all(song['piano_lead'] for song in self.songs[:3]))
        self.assertTrue(next(song for song in self.songs if song['id'] == 'g03_shanhai')['guitar_lead'])
        self.assertTrue(next(song for song in self.songs if song['id'] == 'p04_fuji')['piano_lead'])

    def test_reproducible_scores_and_round_trip(self):
        for profile in [*PIANO_PROFILES, *ROCK_PROFILES, *PROFILES]:
            with self.subTest(song=profile['id']):
                factory = compose_piano if profile.get('piano_lead') else compose_rock if profile.get('guitar_lead') else compose
                project = factory(profile)
                self.assertEqual(project, factory(profile))
                song = next(song for song in self.songs if song['id'] == profile['id'])
                self.assertEqual(Project.load(project_path(song, 'full')), with_headroom(project))
                self.assertEqual(Project.load(project_path(song, 'short')), with_headroom(short_version(project, song['title'])))

    def test_songs_are_not_merely_transpositions(self):
        fingerprints = []
        for song in self.songs:
            project = Project.load(project_path(song, 'full'))
            signature = [(note.start, note.end, note.instrument) for note in score_notes(project)]
            fingerprints.append(hashlib.sha256(repr(signature).encode()).hexdigest())
        self.assertEqual(len(set(fingerprints)), 16)

    def test_neon_copy_only_changes_bus_gain_and_preserves_original(self):
        for variant, name in (('full', 'Neon_Runway_32bars.tang.json'), ('short', 'Neon_Runway_8bars.tang.json')):
            self.assertEqual(Project.load(ROOT / 'projects' / f'06_neon_runway_{variant}.tang.json'),
                             with_headroom(Project.load(APP / 'demos/neon_runway_20261024' / name)))

    def test_pure_piano_contains_no_other_notes_or_bus_gain(self):
        project = compose_piano(PIANO_PROFILES[0])
        self.assertEqual({track.instrument for track in project.tracks}, {'piano'})
        for name in ('violin', 'guitar', 'drums', 'bass'):
            self.assertEqual(project.parameters['bus.' + name], 0)
            lane = next(lane for lane in project.automation if lane.target == 'bus.' + name)
            self.assertTrue(all(point.value == 0 for point in lane.points))

    def test_jazz_piano_has_no_violin(self):
        project = compose_piano(PIANO_PROFILES[1])
        self.assertNotIn('violin', {note.instrument for note in score_notes(project)})
        self.assertEqual(project.parameters['bus.violin'], 0)

    def test_background_violin_never_takes_the_melody(self):
        project = compose_piano(PIANO_PROFILES[2])
        violin = [note for note in score_notes(project) if note.instrument == 'violin']
        lead = project.tracks[0]
        melody = [note for clip in lead.clips for note in clip.notes]
        self.assertLessEqual(len(violin), 10)
        self.assertGreater(len(melody), len(violin) * 10)
        self.assertTrue(all(55 <= note.pitch <= 70 and note.velocity <= 23 for note in violin))
        self.assertTrue(all(note.end - note.start >= 2 * 480 for note in violin))
        violin_lane = next(lane for lane in project.automation if lane.target == 'bus.violin')
        piano_lane = next(lane for lane in project.automation if lane.target == 'bus.piano')
        self.assertLessEqual(max(point.value for point in violin_lane.points), 15)
        self.assertGreaterEqual(max(point.value for point in piano_lane.points), 100)

    def test_piano_lead_is_separate_from_accompaniment_registers(self):
        for profile in PIANO_PROFILES:
            project = compose_piano(profile)
            lead, harmony, left = [{note.pitch for clip in track.clips for note in clip.notes}
                                   for track in project.tracks[:3]]
            self.assertGreater(min(lead), max(harmony))
            self.assertGreater(min(harmony), max(left))
            self.assertEqual(project.tracks[0].level, 100)

    def test_piano_bus_dominates_every_section(self):
        for profile in PIANO_PROFILES:
            project = compose_piano(profile)
            for section_start in (0, 4, 12, 20, 24, 30):
                values = {lane.target: lane.value_at(section_start * BAR, project.parameters[lane.target])
                          for lane in project.automation if lane.target.startswith('bus.')}
                self.assertGreater(values['bus.piano'], 75)
                for name in ('violin', 'guitar', 'drums', 'bass'):
                    self.assertGreater(values['bus.piano'], values['bus.' + name])

    def test_rock_has_only_guitar_bass_and_drums(self):
        project = compose_rock(ROCK_PROFILES[0])
        self.assertEqual({note.instrument for note in score_notes(project)}, {'guitar', 'bass', 'drums'})
        self.assertEqual([track.instrument for track in project.tracks[:3]], ['guitar'] * 3)
        for name in ('piano', 'violin'):
            self.assertEqual(project.parameters['bus.' + name], 0)
            lane = next(lane for lane in project.automation if lane.target == 'bus.' + name)
            self.assertTrue(all(point.value == 0 for point in lane.points))

    def test_rock_uses_full_wet_distortion_cabinet_and_conservative_output(self):
        project = compose_rock(ROCK_PROFILES[0])
        expected = {'guitar.amp': 3, 'guitar.drive': 72, 'guitar.tone': 48, 'guitar.level': 64,
                    'guitar.mix': 127, 'guitar.cabinet': 1, 'guitar.gate': 1,
                    'guitar.threshold': 18, 'guitar.compressor': 0, 'guitar.modulation': 0,
                    'space.chorus_mix': 0}
        for target, value in expected.items():
            self.assertEqual(project.parameters[target], value)
        self.assertFalse(any(lane.target.startswith('guitar.') for lane in project.automation))

    def test_rock_guitar_bus_leads_every_section(self):
        project = compose_rock(ROCK_PROFILES[0])
        for first, last, section in ROCK_FORM:
            values = {lane.target: lane.value_at(first * BAR, project.parameters[lane.target])
                      for lane in project.automation if lane.target.startswith('bus.')}
            self.assertGreater(values['bus.guitar'], values['bus.drums'])
            self.assertGreater(values['bus.guitar'], values['bus.bass'])
            self.assertGreater(values['bus.guitar'], 75)

    def test_rock_power_chords_are_fifths_not_dense_major_or_minor_stacks(self):
        project = compose_rock(ROCK_PROFILES[0])
        count = 0
        for clip in project.tracks[1].clips:
            self.assertEqual(len(clip.notes) % 3, 0)
            for start in range(0, len(clip.notes), 3):
                group = clip.notes[start:start + 3]
                self.assertEqual([note.pitch - group[0].pitch for note in group], [0, 7, 12])
                self.assertEqual([note.start - group[0].start for note in group], [0, 8, 16])
                count += 1
        self.assertGreater(count, 50)

    def test_rock_has_distinct_riff_hook_solo_and_resolving_short_ending(self):
        project = compose_rock(ROCK_PROFILES[0])
        lead = project.tracks[2]
        solos = [clip for clip in lead.clips if 24 * BAR <= clip.start < 32 * BAR]
        self.assertEqual(len(solos), 8)
        self.assertTrue(all(len(clip.notes) == 6 and '吉他独奏' in clip.name for clip in solos))
        self.assertGreater(len({tuple(note.pitch for note in clip.notes) for clip in solos}), 6)
        short = short_version(project, ROCK_PROFILES[0]['title'])
        self.assertIn('副歌再现', short.tracks[0].clips[0].name)
        self.assertTrue(any('尾声' in clip.name for clip in short.tracks[1].clips))
        self.assertEqual((project.bars, project.bpm), (40, 136))

    def test_rock_effect_packets_commit_before_first_guitar_attack_in_both_versions(self):
        project = compose_rock(ROCK_PROFILES[0])
        for score in (project, short_version(project, ROCK_PROFILES[0]['title'])):
            plan = compile_plan(score, hardware=True, ensemble=True)
            initial = next(event for event in plan.events if event.kind == 'effects' and event.at == 0)
            frames = [initial.data[offset:offset + 6] for offset in range(0, len(initial.data), 6)]
            amplifier = next(packet for packet in frames if packet[1] == 0x40)
            output = next(packet for packet in frames if packet[1] == 0x41)
            self.assertEqual(amplifier[2:5], bytes((3, 72, 48)))
            self.assertEqual(output[2:5], bytes((64, 127, 3)))
            self.assertEqual([packet[1] for packet in frames if 0x40 <= packet[1] <= 0x44], list(range(0x40, 0x45)))
            first = next(event for event in plan.events if event.kind == 'on' and event.note.instrument == 'guitar')
            self.assertGreater(first.at, .1)

    def test_all_projects_compile_with_voice_serial_and_checksum_margins(self):
        for song, variant, project in self.projects:
            with self.subTest(song=song['id'], variant=variant):
                report = neon.analyze(project)
                self.assertTrue(report['hardware_compilation_passed'])
                self.assertLess(report['maximum_bytes_per_100ms'], 400)
                for instrument, limit in (('piano', 16), ('guitar', 32), ('bass', 8), ('violin', 1)):
                    self.assertLessEqual(report['gated_peak_voices'].get(instrument, 0), limit)
                self.assertLessEqual(report['tail_load_estimate_not_measured']['guitar']['peak_attacks_in_window'], 26)
                self.assertLessEqual(report['tail_load_estimate_not_measured']['bass']['peak_attacks_in_window'], 8)

    def test_ensemble_targets_instruments_without_timbre_switching(self):
        opcodes = {'piano': 0x0c, 'guitar': 0x0a, 'bass': 0x0b, 'violin': 0x0d, 'drums': 0x50}
        for song, variant, project in self.projects:
            plan = compile_plan(project, hardware=True, ensemble=True)
            self.assertFalse(any(event.kind == 'timbre' for event in plan.events))
            expected = {opcodes[note.instrument] for note in score_notes(project)}
            self.assertEqual({event.data[1] for event in plan.events if event.kind == 'on'}, expected)
            if len(expected - {0x50}) > 1:
                with self.assertRaises(ValueError):
                    compile_plan(project, hardware=True, ensemble=False)

    def test_original_ensemble_songs_really_overlap_engines(self):
        for song in self.songs:
            project = Project.load(project_path(song, 'full'))
            expected = {'p01_window_letter': 1, 'p02_blue_platform': 4, 'g01_iron_highway': 3, 'g02_spark_switch': 3, 'p04_fuji': 3, 'p05_fuji_violin': 3, 'p06_fuji_pad': 2, 'p07_time_machine': 2}.get(song['id'], 5)
            self.assertEqual(neon.analyze(project)['simultaneous_instrument_types'], expected)

    def test_short_versions_keep_ending_and_all_versions_fade(self):
        for song, variant, project in self.projects:
            self.assertEqual(project.bars, 8 if variant == 'short' else song['bars'])
            duration = compile_plan(project, hardware=True, ensemble=True).duration
            self.assertAlmostEqual(duration, song['short_seconds'] if variant == 'short' else song['duration_seconds'])
            self.assertFalse(any(note.start >= (project.bars - 1) * BAR for note in score_notes(project)))
            for lane in project.automation:
                if lane.target.startswith('bus.'):
                    self.assertEqual(lane.value_at(project.length - 1, 127), 0)

    def test_full_fake_clock_playback_releases_every_song(self):
        for song, variant, project in self.projects:
            with self.subTest(song=song['id'], variant=variant):
                clock, sent = Clock(), []
                player = ArrangementPlayer(lambda data: sent.append(bytes(data)) or True,
                                           clock.schedule, clock.cancel, clock=lambda: clock.now)
                plan = compile_plan(project, hardware=True, ensemble=True)
                self.assertTrue(player.play(plan))
                clock.advance(plan.duration + plan.preparation_seconds + .25)
                self.assertEqual(player.state, 'stopped')
                self.assertFalse(player.active)
                self.assertFalse(clock.jobs)
                self.assertEqual(sent[-1][1:5], b'\x0e\x00\x00\x00')
                actual = [packet for packet in sent if len(packet) == 6 and packet[1] in (0x0a, 0x0b, 0x0c, 0x0d, 0x50)
                          and (packet[1] in (0x0a, 0x0b, 0x50) or packet[4] == 1
                               or (packet[1] == 0x0d and packet[4] == 3))]
                self.assertEqual(Counter(actual), Counter(event.data for event in plan.events if event.kind == 'on'))

    def test_offline_walkthrough_never_writes_to_serial(self):
        for song, variant, project in self.projects:
            clock, sent = Clock(), []
            player = ArrangementPlayer(lambda data: sent.append(data) or True,
                                       clock.schedule, clock.cancel, clock=lambda: clock.now)
            plan = compile_plan(project, hardware=False, ensemble=True)
            player.play(plan)
            clock.advance(plan.duration + .25)
            self.assertEqual(sent, [])
            self.assertEqual(player.state, 'stopped')

    def test_stop_mid_piece_leaves_no_jobs(self):
        clock = Clock()
        player = ArrangementPlayer(lambda data: True, clock.schedule, clock.cancel, clock=lambda: clock.now)
        plan = compile_plan(compose_piano(PIANO_PROFILES[2]), hardware=True, ensemble=True, start_tick=13 * BAR + 240)
        player.play(plan)
        clock.advance(1)
        self.assertTrue(player.stop())
        self.assertFalse(clock.jobs)
        self.assertFalse(player.active)

    def test_catalog_paths_and_unknown_selection_are_rejected(self):
        song = deepcopy(self.songs[0])
        for path in ('../outside.tang.json', 'catalog.json'):
            song['full'] = path
            with self.assertRaises(ValueError):
                project_path(song, 'full')
        with self.assertRaises(ValueError):
            project_path(self.songs[0], 'other')
        with self.assertRaises(ValueError):
            load_song(None, 'not-a-song')

    def test_launchers_use_ascii_body_and_workspace_relative_paths(self):
        for name in ('打开音乐Demo.cmd', '打开钢琴Demo.cmd', '打开失真摇滚Demo.cmd', '打开失真摇滚短试听.cmd'):
            contents = (ROOT.parent / name).read_text(encoding='ascii')
            self.assertIn('%~dp0Music_Demos\\launch_library.ps1', contents)
        self.assertIn('-Song p01_window_letter', (ROOT.parent / '打开钢琴Demo.cmd').read_text(encoding='ascii'))
        self.assertIn('-Song g01_iron_highway', (ROOT.parent / '打开失真摇滚Demo.cmd').read_text(encoding='ascii'))
        self.assertIn('-Song g01_iron_highway -Short', (ROOT.parent / '打开失真摇滚短试听.cmd').read_text(encoding='ascii'))

    def test_hidden_real_ui_loads_all_projects_as_copies_without_playing(self):
        from test_arrangement_ui import ArrangementInterfaceTests, MemoryPort
        harness = ArrangementInterfaceTests()
        with harness.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            library = attach_library(app)
            app.update_idletasks()
            self.assertEqual(app.active_page, 'demos')
            self.assertEqual(len(library.tree.get_children()), 16)
            self.assertEqual(library.tree.selection(), ('p01_window_letter',))
            for song, variant, project in self.projects:
                self.assertTrue(load_song(app, song['id'], variant))
                app.update_idletasks()
                self.assertEqual(app.active_page, 'arrangement')
                self.assertEqual(panel.project, project)
                self.assertIsNone(panel.path)
                self.assertTrue(panel.ensemble.get())
                self.assertFalse(panel.hardware.get())
                self.assertFalse(panel.loop.get())
                self.assertEqual(panel.player.state, 'stopped')
                panel.check()
                self.assertIn('通过', panel.status.get())
                self.assertEqual(port.packets, [])
            library.tree.selection_set('p02_blue_platform')
            library.describe()
            self.assertIn('小提琴完全不参与', library.description.get())

    def test_cancel_unsaved_changes_keeps_the_score(self):
        from test_arrangement_ui import ArrangementInterfaceTests, MemoryPort
        harness = ArrangementInterfaceTests()
        with harness.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            original = panel.project
            with patch.object(panel, 'confirm_discard', return_value=False):
                self.assertFalse(load_song(app, self.songs[0]['id']))
            self.assertIs(panel.project, original)
            self.assertEqual(port.packets, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
