import ctypes
import os
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CompositeFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dll=ROOT/f'tests/build/frame_encoder_{os.getpid()}.dll'
        result=subprocess.run([os.environ.get('TOUCH_TEST_TCC',str(ROOT/'tests/tools/tcc/tcc.exe')),'-shared','-o',str(dll),
            '-include',str(ROOT/'tests/include/idf_test.h'),'-I',str(ROOT/'tests/include'),
            '-I',str(ROOT/'main'),str(ROOT/'tests/frame_encoder_sim.c')],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        cls.sim=ctypes.CDLL(str(dll))
        cls.sim.sim_frame_word.restype=ctypes.c_uint

    def expected(self,profile):
        # Golden stream from protocol bytes, independent of encoder phase code.
        zero,one,period=(5,17,25) if profile==0 else (7,18,28 if profile==2 else 25)
        low_reset=3000|(3000<<16)
        words=[low_reset]
        for byte in (0x80,0x01,0xa5,0x5a,0x00,0xff):
            for bit in range(7,-1,-1):
                high=one if byte&(1<<bit) else zero
                words.append(high|(1<<15)|((period-high)<<16))
        return words+[low_reset]

    def test_full_grb_frame_has_msb_first_data_and_one_reset_at_each_end(self):
        for profile in range(3):
            self.assertEqual(self.sim.sim_frame_run(profile,384,0,0),0)
            self.assertEqual(self.sim.sim_frame_count(),50)
            self.assertEqual([self.sim.sim_frame_word(i) for i in range(50)],self.expected(profile))
            self.assertEqual(self.sim.sim_frame_children(),0)

    def test_buffer_boundaries_do_not_insert_resets_between_led_bytes(self):
        for capacity in (1,2,7,13,25,49,50):
            self.assertEqual(self.sim.sim_frame_run(0,capacity,0,0),0)
            self.assertEqual(self.sim.sim_frame_count(),50)
            self.assertEqual([self.sim.sim_frame_word(i) for i in range(50)],self.expected(0))

    def test_resetting_partial_encoder_restarts_at_head_of_frame(self):
        self.assertEqual(self.sim.sim_frame_run(1,7,1,0),0)
        self.assertEqual([self.sim.sim_frame_word(i) for i in range(50)],self.expected(1))

    def test_failed_allocations_release_children(self):
        for stage in (1,2,3):
            self.assertEqual(self.sim.sim_frame_run(0,384,0,stage),0x101)
            self.assertEqual(self.sim.sim_frame_children(),0)
        self.assertEqual(self.sim.sim_frame_run(3,384,0,0),0x102)


if __name__=='__main__':unittest.main()
