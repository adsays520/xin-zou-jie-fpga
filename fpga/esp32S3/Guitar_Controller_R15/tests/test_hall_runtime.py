import ctypes
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HallRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = ROOT / 'tests/build'
        build.mkdir(exist_ok=True)
        library = build / f'hall_sim_{os.getpid()}.dll'
        shared = ROOT.parent.parent / 'esp32C3/Bluedroid_Connection/main'
        command = [os.environ.get('TOUCH_TEST_TCC', str(ROOT / 'tests/tools/tcc/tcc.exe')), '-shared', '-o', str(library),
                   '-include', str(ROOT / 'tests/include/idf_test.h'), '-I', str(ROOT / 'tests/include'),
                   '-I', str(ROOT / 'main'), '-I', str(shared), str(ROOT / 'tests/hall_sim.c'),
                   str(ROOT / 'main/hall_detector.c'), str(ROOT / 'main/control_line.c'), str(ROOT / 'main/fpga_protocol.c')]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        cls.sim = ctypes.CDLL(str(library))
        cls.sim.sim_hall_reply.restype = ctypes.c_char_p
        cls.sim.sim_hall_status.restype = ctypes.c_char_p
        cls.sim.sim_line_text.restype = ctypes.c_char_p

    def setUp(self):
        self.assertEqual(self.sim.sim_hall_reset(), 0)

    def command(self, line):
        self.assertTrue(self.sim.sim_hall_command(line.encode()))
        return self.sim.sim_hall_reply().decode()

    def arm(self):
        self.command('HALL,ARM,ON')
        self.sim.sim_hall_step(128)

    def test_sampling_enabled_but_boot_disarmed(self):
        self.sim.sim_hall_step(128)
        self.assertEqual(self.sim.sim_hall_valid(), 0x3f)
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_step(50)
        self.assertEqual(self.sim.sim_hall_picks(), 0)
        self.assertEqual(self.sim.sim_hall_reads(6), 0)

    def test_single_pick_velocity_and_hysteresis(self):
        self.arm()
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_step(100)
        self.assertEqual(self.sim.sim_hall_picks(), 1)
        self.assertEqual(self.sim.sim_hall_strums(), 1)
        self.assertEqual(self.sim.sim_hall_string(), 0)
        self.assertEqual(self.sim.sim_hall_velocity(), 127)
        self.sim.sim_hall_raw(0, 1500)
        self.sim.sim_hall_step(40)
        self.sim.sim_hall_raw(0, 1300)
        self.sim.sim_hall_step(10)
        self.assertEqual(self.sim.sim_hall_picks(), 2)

    def test_each_channel_routes_to_its_string(self):
        self.command('HALL,MASK,0x7f')
        self.arm()
        for channel in range(1, 7):
            self.sim.sim_hall_raw(channel, 2000)
            self.sim.sim_hall_step(10)
            self.assertEqual(self.sim.sim_hall_string(), 7 - channel)
        self.assertEqual(self.sim.sim_hall_picks(), 6)
        self.assertEqual(self.sim.sim_hall_strums(), 0)

    def test_mask_change_disarms_and_skips_unconnected_inputs(self):
        self.arm()
        self.command('HALL,MASK,0x01')
        self.sim.sim_hall_step(128)
        before = self.sim.sim_hall_reads(1)
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_raw(1, 2200)
        self.sim.sim_hall_step(50)
        self.assertEqual(self.sim.sim_hall_picks(), 0)
        self.assertEqual(self.sim.sim_hall_reads(1), before)
        self.assertEqual(self.sim.sim_hall_valid(), 1)

    def test_adc_failure_not_fabricated_as_zero(self):
        self.arm()
        self.sim.sim_hall_error(0, 1)
        self.sim.sim_hall_step(50)
        self.assertEqual(self.sim.sim_hall_picks(), 0)
        self.assertEqual(self.sim.sim_hall_errors(0), 50)
        self.sim.sim_hall_error(0, 0)
        self.sim.sim_hall_step(10)
        self.assertEqual(self.sim.sim_hall_picks(), 0)

    def test_rail_calibration_cannot_strum_but_h7_triggers_string_one(self):
        self.command('HALL,MASK,0x7f')
        self.sim.sim_hall_raw(0, 0)
        self.arm()
        self.assertEqual(self.sim.sim_hall_valid(), 0x7e)
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_raw(6, 2200)
        self.sim.sim_hall_step(50)
        self.assertEqual(self.sim.sim_hall_picks(), 1)
        self.assertEqual(self.sim.sim_hall_string(), 1)
        self.assertEqual(self.sim.sim_hall_strums(), 0)

    def test_stop_calibration_and_mask_cancel_remaining_strum(self):
        self.arm()
        for command in ('HALL,ARM,OFF', 'HALL,CAL', 'HALL,MASK,0x7f', 'HALL,ARM,ON'):
            before = self.sim.sim_hall_cancellations()
            self.assertTrue(self.command(command).startswith('OK,'))
            self.assertEqual(self.sim.sim_hall_cancellations(), before + 1)

    def test_read_error_cancels_pending_peak_instead_of_late_note(self):
        self.arm()
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_step(2)
        self.sim.sim_hall_error(0, 1)
        self.sim.sim_hall_step(100)
        self.assertEqual(self.sim.sim_hall_valid(), 0x3e)
        self.sim.sim_hall_error(0, 0)
        self.sim.sim_hall_raw(0, 1500)
        self.sim.sim_hall_step(140)
        self.assertEqual(self.sim.sim_hall_valid(), 0x3f)
        self.assertEqual(self.sim.sim_hall_picks(), 0)

    def test_calibration_and_disarm_do_not_emit_picks(self):
        self.arm()
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_step(2)
        self.command('HALL,CAL')
        self.sim.sim_hall_step(128)
        self.assertEqual(self.sim.sim_hall_picks(), 0)
        self.command('HALL,ARM,OFF')
        self.sim.sim_hall_raw(0, 1500)
        self.sim.sim_hall_step(20)
        self.assertEqual(self.sim.sim_hall_picks(), 0)

    def test_offline_queue_rejection_counted_not_replayed(self):
        self.arm()
        self.sim.sim_hall_online(0)
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_step(50)
        self.assertEqual(self.sim.sim_hall_rejected(0), 1)
        self.sim.sim_hall_online(1)
        self.sim.sim_hall_step(50)
        self.assertEqual(self.sim.sim_hall_picks(), 1)

    def test_bad_masks_and_empty_mask_arm_rejected(self):
        for command in ('HALL,MASK,0x80', 'HALL,MASK,0x01junk', 'HALL,MASK,-1'):
            self.assertTrue(self.command(command).startswith('ERROR,'))
        self.command('HALL,MASK,0')
        self.assertTrue(self.command('HALL,ARM,ON').startswith('ERROR,'))
        self.assertFalse(self.sim.sim_hall_command(b'OTHER'))

    def test_user_stroke_1431_to_1600_after_calibration_outliers(self):
        self.command('HALL,ARM,ON')
        for sample in range(128):
            self.sim.sim_hall_raw(0, 1836 if sample in (7, 8, 90) else 1431 + sample % 5 - 2)
            self.sim.sim_hall_step(1)
        self.assertEqual(self.sim.sim_hall_baseline(0), 1431)
        self.assertEqual(self.sim.sim_hall_threshold(0), 32)
        self.assertEqual(self.sim.sim_hall_noise(0), 4)
        self.assertEqual(self.sim.sim_hall_picks(), 0)
        self.sim.sim_hall_raw(0, 1600)
        self.sim.sim_hall_step(10)
        self.assertEqual(self.sim.sim_hall_picks(), 1)
        self.assertEqual(self.sim.sim_hall_raw_peak(0), 169)
        self.assertEqual(self.sim.sim_hall_filtered_peak(0), 169)

    def test_continuous_calibration_noise_rejected_not_clamped(self):
        self.command('HALL,ARM,ON')
        for sample in range(128):
            self.sim.sim_hall_raw(0, 1300 if sample % 2 else 1700)
            self.sim.sim_hall_step(1)
        self.assertEqual(self.sim.sim_hall_valid(), 0x3e)
        self.assertEqual(self.sim.sim_hall_calibration(0), 3)
        self.assertGreater(self.sim.sim_hall_threshold(0), 128)
        self.sim.sim_hall_raw(0, 2200)
        self.sim.sim_hall_step(50)
        self.assertEqual(self.sim.sim_hall_picks(), 0)
        self.command('HALL,STATUS')
        self.assertIn('HALLDIAG,1,CAL,NOISY,STATE,INVALID', self.sim.sim_hall_status().decode())

    def test_unreachable_calibration_and_rail_reasons(self):
        self.command('HALL,ARM,ON')
        for sample in range(128):
            self.sim.sim_hall_raw(0, 1000 if sample % 2 else 3000)
            self.sim.sim_hall_raw(1, 0)
            self.sim.sim_hall_step(1)
        self.assertEqual(self.sim.sim_hall_calibration(0), 4)
        self.assertEqual(self.sim.sim_hall_calibration(1), 2)
        self.assertEqual(self.sim.sim_hall_valid(), 0x3c)

    def test_bounded_noise_calibration_remains_usable(self):
        self.command('HALL,ARM,ON')
        for sample in range(128):
            self.sim.sim_hall_raw(0, 1431 + (sample % 5 - 2) * 8)
            self.sim.sim_hall_step(1)
        self.assertEqual(self.sim.sim_hall_threshold(0), 104)
        self.assertEqual(self.sim.sim_hall_valid(), 0x3f)
        self.sim.sim_hall_raw(0, 1600)
        self.sim.sim_hall_step(10)
        self.assertEqual(self.sim.sim_hall_picks(), 1)

    def test_isolated_and_paired_runtime_spikes_do_not_trigger(self):
        self.arm()
        for raw in (0, 4095):
            for length in (1, 2):
                self.sim.sim_hall_raw(0, raw)
                self.sim.sim_hall_step(length)
                self.sim.sim_hall_raw(0, 1500)
                self.sim.sim_hall_step(20)
        self.assertEqual(self.sim.sim_hall_picks(), 0)
        self.assertEqual(self.sim.sim_hall_state(0), 1)
        self.assertEqual(self.sim.sim_hall_raw_peak(0), 2595)

    def test_three_direction_changes_cannot_confirm_a_pick(self):
        self.arm()
        for raw in (1600, 1400) * 10:
            self.sim.sim_hall_raw(0, raw)
            self.sim.sim_hall_step(2)
        self.sim.sim_hall_raw(0, 1500)
        self.sim.sim_hall_step(20)
        self.assertEqual(self.sim.sim_hall_picks(), 0)

    def test_return_with_twenty_count_offset_rearms(self):
        self.arm()
        self.sim.sim_hall_raw(0, 1670)
        self.sim.sim_hall_step(50)
        self.sim.sim_hall_raw(0, 1520)
        self.sim.sim_hall_step(40)
        self.assertEqual(self.sim.sim_hall_state(0), 1)
        self.sim.sim_hall_raw(0, 1330)
        self.sim.sim_hall_step(10)
        self.assertEqual(self.sim.sim_hall_picks(), 2)

    def test_sustained_stroke_does_not_repeat_and_diagnostic_peak_persists(self):
        self.arm()
        self.sim.sim_hall_raw(0, 1669)
        self.sim.sim_hall_step(2000)
        self.assertEqual(self.sim.sim_hall_picks(), 1)
        self.sim.sim_hall_raw(0, 1500)
        self.sim.sim_hall_step(2000)
        self.command('HALL,STATUS')
        status = self.sim.sim_hall_status().decode()
        self.assertIn('HALLDIAG,1,CAL,OK,STATE,READY', status)
        self.assertIn('RAW_PEAK,169,FILTERED_PEAK,169', status)
        self.assertIn('HALLDIAG,7,CAL,OFF,STATE,OFF', status)

    def test_adc_error_clears_stale_diagnostics_and_requires_calibration(self):
        self.arm()
        self.sim.sim_hall_raw(0, 1700)
        self.sim.sim_hall_step(2)
        self.sim.sim_hall_error(0, 1)
        self.sim.sim_hall_step(1)
        self.command('HALL,STATUS')
        status = self.sim.sim_hall_status().decode()
        self.assertIn('HALLDIAG,1,CAL,CALIBRATING,STATE,CALIBRATING', status)
        self.assertIn('RAW_PEAK,0,FILTERED_PEAK,0', status)
        self.assertEqual(self.sim.sim_hall_picks(), 0)

    def test_recalibration_clears_peak_without_late_events(self):
        self.arm()
        self.sim.sim_hall_raw(0, 1669)
        self.sim.sim_hall_step(4)
        self.command('HALL,CAL')
        self.sim.sim_hall_raw(0, 1500)
        self.sim.sim_hall_step(128)
        self.assertEqual(self.sim.sim_hall_raw_peak(0), 0)
        self.assertEqual(self.sim.sim_hall_filtered_peak(0), 0)
        self.assertEqual(self.sim.sim_hall_picks(), 0)

    def test_usb_line_framing_discards_entire_bad_line(self):
        frames = []
        for byte in b'PING\r\n' + b'X' * 110 + b'FPGA,PICK,6,100\n' + b'\x00FPGA,PICK,6,100\nHALL,STATUS\n':
            if self.sim.sim_line_byte(byte):
                frames.append(self.sim.sim_line_text().decode())
        self.assertEqual(frames, ['PING', 'HALL,STATUS'])

    def test_fixed_mode_whitelist_excludes_uploads(self):
        self.assertTrue(self.sim.sim_fixed_command(9, 2))
        self.assertFalse(self.sim.sim_fixed_command(0x11, 0))
        self.assertFalse(self.sim.sim_fixed_command(0x21, 0))


if __name__ == '__main__':
    unittest.main()
