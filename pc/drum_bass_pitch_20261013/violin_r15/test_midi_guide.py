import struct
from pathlib import Path
import tempfile
import unittest
from midi_guide import read_midi, MidiNote, fingering, guide_masks, mask_command


def vlq(n):
    out = [n & 127]
    while n >> 7:
        n >>= 7; out.insert(0, (n & 127) | 128)
    return bytes(out)


def file_bytes(*tracks):
    return b'MThd'+struct.pack('>IHHH',6, int(len(tracks)>1),len(tracks),480)+b''.join(
        b'MTrk'+struct.pack('>I',len(t))+t for t in tracks)


class MidiTests(unittest.TestCase):
    def read(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.mid'; path.write_bytes(data)
            return read_midi(path)

    def test_tempo_track_running_status_velocity_zero_and_sustain(self):
        conductor=b'\x00\xff\x51\x03\x07\xa1\x20'+vlq(480)+b'\xff\x51\x03\x0f\x42\x40'+vlq(960)+b'\xff\x2f\x00'
        notes=b'\x00\x90\x3c\x64'+vlq(240)+b'\xb0\x40\x7f'+vlq(240)+b'\x90\x3c\x00'+vlq(480)+b'\xb0\x40\x00\x00\x90\x40\x64'+vlq(480)+b'\x40\x00\x00\xff\x2f\x00'
        score=self.read(file_bytes(conductor,notes))
        self.assertEqual(len(score.notes),2)
        self.assertEqual((score.notes[0].start,score.notes[0].end),(0,1.5))
        self.assertEqual((score.notes[1].start,score.notes[1].end),(1.5,2.5))

    def test_overlap_pairs_fifo_and_drum_channel_retained_for_filter(self):
        track=b'\x00\x90\x3c\x64'+vlq(120)+b'\x3c\x50'+vlq(120)+b'\x80\x3c\x00'+vlq(120)+b'\x3c\x00\x00\x99\x24\x7f'+vlq(120)+b'\x89\x24\x00\x00\xff\x2f\x00'
        score=self.read(file_bytes(track))
        self.assertEqual([(n.start,n.end) for n in score.notes[:2]],[(0,.25),(.125,.375)])
        self.assertEqual(score.notes[-1].channel,9)

    def test_truncated_unsupported_and_bad_running_status_rejected(self):
        for data in (b'',file_bytes(b'\x00\x40\x64\x00\xff\x2f\x00'),file_bytes(b'\x00\x90\x40'),
                     b'MThd'+struct.pack('>IHHH',6,2,1,480),file_bytes(b'\xff\xff\xff\xff\xff')):
            with self.assertRaises(ValueError): self.read(data)

    def test_physical_mapping_hold_release_polyphony_and_range(self):
        self.assertEqual(fingering(40),(0,6))
        self.assertEqual(fingering(84),(20,1))
        self.assertIsNone(fingering(85))
        notes=[MidiNote(0,1,40,100,0,0),MidiNote(.5,2,84,100,0,0)]
        self.assertEqual(guide_masks(notes,.75)[:2],(0x100001,0x21))
        self.assertEqual(guide_masks(notes,1)[:2],(0x100000,1))
        self.assertEqual(guide_masks(notes,2)[:2],(0,0))
        self.assertEqual(mask_command(0x100001,0x21),b'LED,GUIDE,100001,21\n')

    def test_full_score_is_not_limited_to_256_notes(self):
        track=b''.join(b'\x00\x90\x40\x64\x01\x80\x40\x00' for _ in range(600))+b'\x00\xff\x2f\x00'
        self.assertEqual(len(self.read(file_bytes(track)).notes),600)


if __name__ == '__main__': unittest.main()
