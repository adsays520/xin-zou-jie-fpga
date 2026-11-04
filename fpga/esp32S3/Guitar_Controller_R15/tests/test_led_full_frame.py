"""Independently constructed RX streams, including the hardware's omitted idles."""
import ctypes as C
import os
from pathlib import Path
import subprocess
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]


class Result(C.Structure):
    _fields_=[('frames',C.c_uint),('bits',C.c_uint*3),('total_bits',C.c_uint),
        *[(n,C.c_uint) for n in ('data_errors','width_errors','period_errors','structure_errors',
            'head_low_ticks','tail_low_ticks','zero_min','zero_max','one_min','one_max',
            'period_min','period_max')],('middle',C.c_uint8*42),
        ('expected_crc',C.c_uint32),('middle_crc',C.c_uint32),
        ('reset_measured',C.c_bool),('reset_ok',C.c_bool),('passed',C.c_bool)]


def levels(payload,profile=0,frames=3,gap=12000):
    high0,high1,period=(5,17,25) if profile==0 else (7,18,28 if profile==2 else 25)
    pulses=[]
    for frame in range(frames):
        for byte in payload:
            for shift in range(7,-1,-1):
                high=high1 if byte>>shift&1 else high0
                pulses.extend([(1,high),(0,period-high)])
        if frame<frames-1:
            pulses[-1]=(0,pulses[-1][1]+gap)
        else:
            pulses.pop()  # Real RMT can omit the final idle as well as the initial idle.
    return pulses


def pack(pulses):
    # Do not assume a TX word boundary is retained by RX.
    words=[]
    for i in range(0,len(pulses),2):
        a,n=pulses[i];b,m=pulses[i+1] if i+1<len(pulses) else (0,0)
        words.append(n|(a<<15)|(m<<16)|(b<<31))
    return (C.c_uint32*len(words))(*words)


class FullFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dll=ROOT/f'tests/build/frame_check_{os.getpid()}.dll'
        result=subprocess.run([str(ROOT/'tests/tools/tcc/tcc.exe'),'-shared','-o',str(dll),
            '-include',str(ROOT/'tests/include/idf_test.h'),'-I',str(ROOT/'tests/include'),
            '-I',str(ROOT/'main'),str(ROOT/'tests/frame_check_sim.c')],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        cls.sim=C.CDLL(str(dll));cls.sim.sim_check.restype=C.POINTER(Result)

    def check(self,pulses,payload,profile=0):
        words=pack(pulses);raw=(C.c_uint8*len(payload))(*payload)
        return self.sim.sim_check(words,len(words),raw,len(payload),28 if profile==2 else 25).contents

    def test_all_colors_lengths_profiles_and_entire_middle_crc(self):
        for leds in (13,14):
            for rgb in ((16,0,0),(0,16,0),(0,0,16),(128,1,255),(0,0,0)):
                r,g,b=rgb;payload=bytes((g,r,b))*leds
                for profile in range(3):
                    with self.subTest(leds=leds,rgb=rgb,profile=profile):
                        got=self.check(levels(payload,profile),payload,profile)
                        self.assertTrue(got.passed)
                        self.assertEqual(list(got.bits),[leds*24]*3)
                        self.assertEqual(bytes(got.middle[:len(payload)]),payload)
                        self.assertEqual(got.expected_crc,zlib.crc32(payload))
                        self.assertEqual(got.middle_crc,zlib.crc32(payload))
                        self.assertGreaterEqual(got.head_low_ticks,12000)
                        self.assertGreaterEqual(got.tail_low_ticks,12000)

    def test_one_data_only_frame_is_not_a_complete_frame_pass(self):
        payload=b'\x10\x00\x00'*14
        got=self.check(levels(payload,frames=1),payload)
        self.assertFalse(got.passed);self.assertFalse(got.reset_ok)

    def test_reset_gaps_below_80us_are_rejected(self):
        payload=b'\x10\x00\x00'*14
        for boundary in (1,2):
            pulses=levels(payload);index=boundary*len(payload)*16-1
            pulses[index]=(0,1500)
            self.assertFalse(self.check(pulses,payload).passed)

    def test_middle_wrong_color_is_visible_in_grb_and_crc(self):
        expected=b'\x10\x00\x00'*14;wrong=b'\x00\x00\x10'*14
        pulses=levels(expected)
        start=len(expected)*16
        alternate=levels(wrong)
        pulses[start:start+len(expected)*16]=alternate[:len(expected)*16]
        got=self.check(pulses,expected)
        self.assertFalse(got.passed);self.assertGreater(got.data_errors,0)
        self.assertEqual(bytes(got.middle[:3]),wrong[:3])
        self.assertNotEqual(got.middle_crc,got.expected_crc)

    def test_missing_and_extra_bits_anywhere_are_rejected(self):
        payload=b'\x81\x42\x24'*14
        for frame in range(3):
            for delta in (-1,1):
                pulses=levels(payload);index=frame*len(payload)*16+32
                if delta<0:del pulses[index:index+2]
                else:pulses[index:index]=[(1,5),(0,20)]
                got=self.check(pulses,payload)
                self.assertFalse(got.passed);self.assertGreater(got.structure_errors,0)

    def test_pixel_boundary_reset_is_rejected(self):
        payload=b'\x10\x00\x00'*14;pulses=levels(payload)
        pulses[47]=(0,6000)
        self.assertFalse(self.check(pulses,payload).passed)

    def test_bad_high_width_and_within_frame_low_gap_are_rejected(self):
        payload=b'\x10\x00\x00'*14
        for index,value,field in ((0,(1,11),'width_errors'),(1,(0,200),'period_errors')):
            pulses=levels(payload);pulses[index]=value
            got=self.check(pulses,payload)
            self.assertFalse(got.passed);self.assertGreater(getattr(got,field),0)

    def test_split_idle_runs_and_shifted_word_boundaries_are_supported(self):
        payload=bytes(range(42));pulses=levels(payload)
        # Insert an initial LOW and split each RESET across hardware word halves.
        pulses.insert(0,(0,1234))
        split=[]
        for level,ticks in pulses:
            split.extend([(0,3000),(0,ticks-3000)] if not level and ticks>10000 else [(level,ticks)])
        self.assertTrue(self.check(split,payload).passed)

    def test_inverted_signal_and_truncated_frames_fail(self):
        payload=b'\x10\x00\x00'*14;pulses=levels(payload)
        self.assertFalse(self.check([(1-level,n) for level,n in pulses],payload).passed)
        self.assertFalse(self.check(pulses[:-16],payload).passed)


if __name__=='__main__':unittest.main()
