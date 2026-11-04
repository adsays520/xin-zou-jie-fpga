import unittest

from build_demo import APP, HERE, analyze, create_project, excerpt
from arrangement_model import BAR, Project
from arrangement_playback import ArrangementPlayer, compile_plan
from test_arrangement import Clock


class DemoTests(unittest.TestCase):
    def test_score_structure(self):
        project = create_project()
        self.assertEqual((project.bpm, project.bars, len(project.tracks)), (96, 32, 9))
        self.assertEqual(len(project.automation), 7)
        self.assertEqual({track.instrument for track in project.tracks},
                         {'piano', 'guitar', 'bass', 'violin', 'drums'})

    def test_deterministic_composition_and_identifiers(self):
        self.assertEqual(create_project().to_dict(), create_project().to_dict())

    def test_saved_projects_round_trip(self):
        self.assertEqual(Project.load(HERE / 'Neon_Runway_32bars.tang.json'), create_project())
        self.assertEqual(Project.load(HERE / 'Neon_Runway_8bars.tang.json'), excerpt(create_project()))

    def test_compiles_for_targeted_ensemble_not_legacy_switching(self):
        project = create_project()
        with self.assertRaises(ValueError):
            compile_plan(project, hardware=True, ensemble=False)
        plan = compile_plan(project, hardware=True, ensemble=True)
        self.assertFalse(any(event.kind == 'timbre' for event in plan.events))
        self.assertEqual({event.data[1] for event in plan.events if event.kind == 'on'},
                         {0x0a, 0x0b, 0x0c, 0x0d, 0x50})

    def test_voice_and_serial_margins(self):
        for project in (create_project(), excerpt(create_project())):
            report = analyze(project)
            self.assertEqual(report['simultaneous_instrument_types'], 5)
            self.assertLess(report['maximum_bytes_per_100ms'], 300)
            for instrument, limit in (('piano', 16), ('guitar', 32), ('bass', 8), ('violin', 1)):
                self.assertLessEqual(report['gated_peak_voices'][instrument], limit)
            self.assertLessEqual(report['tail_load_estimate_not_measured']['guitar']['peak_attacks_in_window'], 24)
            self.assertLessEqual(report['tail_load_estimate_not_measured']['bass']['peak_attacks_in_window'], 8)

    def test_short_is_return_and_coda_not_a_cut_off_loop(self):
        short = excerpt(create_project())
        self.assertEqual(compile_plan(short, hardware=True, ensemble=True).duration, 20)
        self.assertFalse(any(clip.notes for track in short.tracks for clip in track.clips if clip.start == 7 * BAR))
        for lane in short.automation:
            if lane.target.startswith('bus.'):
                self.assertEqual(lane.value_at(short.length - 1, 127), 0)

    def test_packet_checksums(self):
        report = analyze(create_project())
        self.assertTrue(report['hardware_compilation_passed'])

    def test_full_song_fake_clock_playback_and_release(self):
        for project in (create_project(), excerpt(create_project())):
            clock = Clock()
            sent = []
            player = ArrangementPlayer(lambda data: sent.append(bytes(data)) or True,
                                       clock.schedule, clock.cancel, clock=lambda: clock.now)
            plan = compile_plan(project, hardware=True, ensemble=True)
            self.assertTrue(player.play(plan))
            clock.advance(plan.duration + .25)
            self.assertEqual(player.state, 'stopped')
            self.assertEqual(player.active, {})
            self.assertFalse(clock.jobs)
            self.assertEqual(sent[-1][1:5], b'\x0e\x00\x00\x00')
            self.assertIn('播放完成', player.message)
            attacks = [event.data for event in plan.events if event.kind == 'on']
            actual_attacks = [packet for packet in sent if len(packet) == 6 and packet[1] in (0x0a, 0x0b, 0x0c, 0x0d, 0x50)
                              and (packet[1] in (0x0a, 0x0b, 0x50) or packet[4] == 1)]
            self.assertEqual(len(actual_attacks), len(attacks))

    def test_silent_walkthrough_never_calls_serial(self):
        clock = Clock()
        sent = []
        player = ArrangementPlayer(lambda data: sent.append(data) or True,
                                   clock.schedule, clock.cancel, clock=lambda: clock.now)
        player.play(compile_plan(create_project(), hardware=False, ensemble=True))
        clock.advance(81)
        self.assertEqual(sent, [])
        self.assertEqual(player.state, 'stopped')

    def test_start_mid_score_then_stop_has_no_pending_jobs(self):
        clock = Clock()
        player = ArrangementPlayer(lambda data: True, clock.schedule, clock.cancel, clock=lambda: clock.now)
        plan = compile_plan(create_project(), hardware=True, ensemble=True, start_tick=13 * BAR + 240)
        player.play(plan)
        clock.advance(1)
        self.assertTrue(player.stop())
        self.assertFalse(clock.jobs)
        self.assertFalse(player.active)

    def test_hidden_real_ui_load_does_not_send(self):
        from test_arrangement_ui import ArrangementInterfaceTests, MemoryPort
        harness = ArrangementInterfaceTests()
        with harness.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            panel._replace(Project.load(HERE / 'Neon_Runway_32bars.tang.json'))
            panel.ensemble.set(True)
            panel.hardware.set(False)
            app.update_idletasks()
            self.assertEqual(len(panel.project.tracks), 9)
            self.assertEqual(port.packets, [])
            self.assertEqual(panel.player.state, 'stopped')
            panel.check()
            self.assertIn('通过', panel.status.get())
            self.assertEqual(port.packets, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
