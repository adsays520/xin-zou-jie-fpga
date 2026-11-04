import math
import unittest

from build_library import ROOT, short_version
from demo_headroom import with_headroom
from rock_short_tail import PROFILE, compose_short_rock
from arrangement_model import Project
from arrangement_playback import ArrangementPlayer, compile_plan
from guitar_controller import crc16_ccitt, riff_tail_ms
from guitar_envelope import short_envelope_words
from test_arrangement import Clock


class ShortRockTests(unittest.TestCase):
    def test_new_song_is_reproducible_and_both_versions_keep_short_sustain(self):
        project = compose_short_rock()
        for variant, score in (('full', project), ('short', short_version(project, PROFILE['title']))):
            loaded = Project.load(ROOT / 'projects' / f'{PROFILE["id"]}_{variant}.tang.json')
            self.assertEqual(loaded, with_headroom(score))
            self.assertEqual(loaded.guitar_sustain, 36)
            self.assertLess(loaded.guitar_sustain, 60)
            self.assertEqual(loaded.parameters['guitar.amp'], 3)
            self.assertEqual(loaded.parameters['guitar.mix'], 127)
            self.assertEqual(loaded.parameters['space.delay_mix'], 0)
            self.assertEqual({track.instrument for track in loaded.tracks}, {'guitar', 'bass', 'drums'})
        self.assertEqual(project, compose_short_rock())

    def test_both_strum_directions_use_separated_string_attacks(self):
        project = compose_short_rock()
        directions = set()
        for clip in project.tracks[1].clips:
            self.assertEqual(len(clip.notes) % 4, 0)
            for first in range(0, len(clip.notes), 4):
                notes = clip.notes[first:first + 4]
                self.assertEqual([note.start - notes[0].start for note in notes], [0, 18, 36, 54])
                pitches = [note.pitch for note in notes]
                directions.add('down' if pitches == sorted(pitches) else 'up')
                self.assertEqual(pitches, sorted(pitches, reverse=pitches[0] > pitches[-1]))
        self.assertEqual(directions, {'down', 'up'})

    def test_envelope_crc_addresses_words_and_commit_order(self):
        plan = compile_plan(compose_short_rock(), True, ensemble=True)
        blocks = [data for data, delay in plan.preparation if len(data) == 38]
        self.assertEqual(len(blocks), 256)
        words = []
        for block_index, data in enumerate(blocks):
            self.assertEqual(data[:2], b'\xa5\x11')
            self.assertEqual(int.from_bytes(data[2:4], 'big'), block_index * 16)
            self.assertEqual(crc16_ccitt(data[:-2]), int.from_bytes(data[-2:], 'big'))
            words.extend(int.from_bytes(data[index:index + 2], 'big') for index in range(4, 36, 2))
        self.assertEqual(tuple(words), short_envelope_words(36))
        self.assertEqual([data[1] for data, _ in plan.preparation[-2:]], [0x12, 0x13])
        self.assertAlmostEqual(plan.preparation_seconds, 1.385)

    def test_v14_interpolation_is_zero_after_short_tail_and_has_no_gain_boost(self):
        words = short_envelope_words(36)
        end = math.ceil(riff_tail_ms(3, 36) * 48) + 18
        self.assertLess(end / 48000, .563)
        self.assertGreater(max(words), 30000)
        self.assertLessEqual(max(words), 32768)
        self.assertEqual(words[0], 0)
        for age in range(end, 67200):
            position = age * 3994
            index = min(4095, position >> 16)
            fraction = position & 65535
            gain = words[index] + ((words[min(4095, index + 1)] - words[index]) * fraction >> 16)
            self.assertEqual(gain, 0)

    def test_preparation_finishes_before_music_clock_starts(self):
        clock, sent = Clock(), []
        plan = compile_plan(compose_short_rock(), True, ensemble=True)
        player = ArrangementPlayer(lambda data: sent.append((clock.now, data)) or True,
                                   clock.schedule, clock.cancel, clock=lambda: clock.now)
        player.play(plan)
        clock.advance(plan.preparation_seconds - .002)
        self.assertTrue(player._preparing)
        self.assertEqual(player.position, 0)
        self.assertFalse(any(len(data) == 6 and data[1] in (0x0a, 0x0b, 0x50) for _, data in sent))
        clock.advance(.01)
        self.assertFalse(player._preparing)
        self.assertLess(player.position, .02)
        clock.advance(plan.duration + .25)
        self.assertEqual(player.state, 'stopped')
        self.assertTrue(any(data[1:5] == b'\x13\0\0\0' for _, data in sent[-2:]))

    def test_stop_during_preparation_cancels_notes_and_disables_custom_mode(self):
        clock, sent = Clock(), []
        player = ArrangementPlayer(lambda data: sent.append(data) or True, clock.schedule, clock.cancel,
                                   clock=lambda: clock.now)
        player.play(compile_plan(compose_short_rock(), True, ensemble=True))
        clock.advance(.2)
        player.stop()
        count = len(sent)
        clock.advance(70)
        self.assertEqual(len(sent), count)
        self.assertFalse(clock.jobs)
        self.assertEqual(sent[-2][1:5], b'\x13\0\0\0')
        self.assertEqual(sent[-1][1:5], b'\x0e\0\0\0')

    def test_offline_uses_no_preparation_and_old_files_default_to_natural_tail(self):
        project = compose_short_rock()
        self.assertFalse(compile_plan(project, False, ensemble=True).preparation)
        data = project.to_dict()
        del data['guitar_sustain']
        self.assertEqual(Project.from_dict(data).guitar_sustain, 127)
        for value in (-1, 128, True, '36'):
            project.guitar_sustain = value
            with self.assertRaises(ValueError):
                project.validate()


if __name__ == '__main__':
    unittest.main()
