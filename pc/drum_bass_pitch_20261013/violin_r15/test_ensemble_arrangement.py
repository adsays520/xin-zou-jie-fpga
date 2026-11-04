import unittest

from arrangement_model import Clip, Note, Project, Track, PPQ
from arrangement_playback import ArrangementPlayer, compile_plan
from ensemble_protocol import CapabilityProbe, targeted_note
from test_arrangement import Clock
import test_arrangement_ui as interface_tests

MemoryPort = interface_tests.MemoryPort


def concurrent_project():
    return Project(tracks=[Track(instrument, instrument, clips=[Clip(notes=[Note(pitch=pitch)])])
                           for instrument, pitch in [('piano', 60), ('guitar', 64), ('bass', 28), ('violin', 67), ('drums', 0)]])


def capability_reply(sequence, flags=7):
    data = bytearray((0xd8, 0x45, sequence, 8, flags))
    checksum = 0
    for value in data:
        checksum ^= value
    return bytes(data) + bytes((checksum,))


class EnsembleCompilerTests(unittest.TestCase):
    def test_same_project_rejected_by_v7_and_compiles_for_v8(self):
        project = concurrent_project()
        with self.assertRaises(ValueError):
            compile_plan(project, True)
        plan = compile_plan(project, True, ensemble=True)
        self.assertTrue(plan.ensemble)
        self.assertEqual({event.data[1] for event in plan.events if event.kind == 'on'}, {0x0a, 0x0b, 0x0c, 0x0d, 0x50})
        self.assertFalse(any(event.kind == 'timbre' for event in plan.events))
        self.assertTrue(any(event.data[:3] == b'\xa5\x0e\x01' for event in plan.events))

    def test_no_global_timbre_switch_per_note(self):
        plan = compile_plan(concurrent_project(), True, ensemble=True)
        self.assertFalse(any(event.data and event.data[1] == 4 for event in plan.events))

    def test_independent_bass_level_emitted_only_for_v8(self):
        project = concurrent_project()
        project.parameters['bus.bass'] = 32
        plan = compile_plan(project, True, ensemble=True)
        data = next(event.data for event in plan.events if event.kind == 'effects')
        self.assertTrue(any(data[offset:offset + 4] == b'\xa5\x70\x04\x20' for offset in range(0, len(data), 6)))

    def test_targeted_release_formats_and_checksums(self):
        self.assertEqual(targeted_note('piano', 60, 1, False)[1:5], bytes((0x0c, 60, 1, 0)))
        self.assertEqual(targeted_note('violin', 67, 100, True)[1:5], bytes((0x0d, 67, 100, 1)))
        self.assertEqual(targeted_note('guitar', 64, 1, False), b'')
        for instrument, pitch in [('piano', 60), ('violin', 67), ('guitar', 40), ('bass', 28)]:
            checksum = 0
            for value in targeted_note(instrument, pitch, 100, True):
                checksum ^= value
            self.assertEqual(checksum, 0)

    def test_stop_clears_ensemble_not_one_selected_timbre(self):
        clock = Clock()
        sent = []
        player = ArrangementPlayer(lambda data: sent.append(data) or True, clock.schedule, clock.cancel,
                                   clock=lambda: clock.now)
        player.play(compile_plan(concurrent_project(), True, ensemble=True))
        self.assertEqual(len(player.active), 5)
        player.stop()
        self.assertEqual(sent[-1][1:5], b'\x0e\x00\x00\x00')
        self.assertTrue(any(data[1] == 0x0c and data[4] == 0 for data in sent))
        self.assertTrue(any(data[1] == 0x0d and data[4] == 0 for data in sent))
        self.assertFalse(clock.jobs)

    def test_each_instrument_voice_limit_still_applies(self):
        project = concurrent_project()
        project.tracks[3].clips[0].notes.append(Note(pitch=70))
        with self.assertRaisesRegex(ValueError, '声部上限'):
            compile_plan(project, True, ensemble=True)

    def test_same_pitch_in_different_instruments_allowed(self):
        project = concurrent_project()
        project.tracks[0].clips[0].notes[0].pitch = 67
        self.assertTrue(compile_plan(project, True, ensemble=True).ensemble)

    def test_old_saved_project_gets_only_new_bass_default(self):
        data = concurrent_project().to_dict()
        del data['parameters']['bus.bass']
        self.assertEqual(Project.from_dict(data).parameters['bus.bass'], 100)


class ProbeTests(unittest.TestCase):
    def test_capability_expires_on_same_port(self):
        port = type('Port', (), {'is_open': True})()
        clock = [0]
        probe = CapabilityProbe(clock=lambda: clock[0])
        query = probe.begin(port)
        probe.feed(capability_reply(query[2]), port)
        clock[0] = 31
        self.assertFalse(probe.usable(port))

    def test_matching_fragmented_reply_only(self):
        port = type('Port', (), {'is_open': True})()
        probe = CapabilityProbe(clock=lambda: 0)
        query = probe.begin(port)
        reply = capability_reply(query[2])
        self.assertFalse(probe.feed(b'noise' + reply[:3], port))
        self.assertTrue(probe.feed(reply[3:], port))
        self.assertTrue(probe.usable(port))
        self.assertEqual(probe.flags, 7)

    def test_corrupt_stale_wrong_port_and_timeout_do_not_authorize(self):
        port = type('Port', (), {'is_open': True})()
        clock = [0]
        probe = CapabilityProbe(clock=lambda: clock[0])
        query = probe.begin(port)
        reply = capability_reply(query[2])
        self.assertFalse(probe.feed(reply[:-1] + bytes((reply[-1] ^ 1,)), port))
        self.assertFalse(probe.feed(capability_reply((query[2] - 1) & 255), port))
        self.assertFalse(probe.feed(reply, object()))
        clock[0] = 2
        self.assertFalse(probe.feed(reply, port))
        self.assertFalse(probe.usable(port))

    def test_disconnect_invalidates_capability(self):
        port = type('Port', (), {'is_open': True})()
        probe = CapabilityProbe(clock=lambda: 0)
        query = probe.begin(port)
        probe.feed(capability_reply(query[2]), port)
        port.is_open = False
        self.assertFalse(probe.usable(port))
        probe.invalidate()
        self.assertFalse(probe.confirmed)


class EnsembleInterfaceTests(unittest.TestCase):
    application = interface_tests.ArrangementInterfaceTests.application

    def test_ensemble_requires_live_capability_and_stops_with_mode_exit(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            panel.demo_ensemble()
            panel.hardware.set(True)
            panel.play()
            self.assertEqual(port.packets, [])
            self.assertIn('确认能力', panel.status.get())
            panel.probe_capabilities()
            port.incoming.extend(capability_reply(panel.probe.sequence))
            panel._poll_capabilities()
            panel.play()
            self.assertEqual(panel.player.state, 'playing')
            self.assertTrue(any(packet[1] == 0x0e and packet[2] == 1 for packet in port.packets))
            self.assertEqual({packet[1] for packet in port.packets if packet[1] in (0x0a, 0x0b, 0x0c, 0x0d)}, {0x0a, 0x0b, 0x0c, 0x0d})
            panel.stop()
            self.assertEqual(port.packets[-1][1:5], b'\x0e\0\0\0')
            app.show_page('guitar')
            self.assertFalse(panel.probe.confirmed)

    def test_missing_piano_bank_blocks_notes_after_valid_probe(self):
        with self.application() as (app, panel):
            port = MemoryPort()
            app.port = port
            panel.demo_ensemble()
            panel.probe_capabilities()
            port.incoming.extend(capability_reply(panel.probe.sequence, 3))
            panel._poll_capabilities()
            panel.hardware.set(True)
            panel.play()
            self.assertIn('钢琴参数就绪', panel.status.get())
            self.assertFalse(any(packet[1] in (0x0a, 0x0b, 0x0c, 0x0d) for packet in port.packets))


if __name__ == '__main__':
    unittest.main()
