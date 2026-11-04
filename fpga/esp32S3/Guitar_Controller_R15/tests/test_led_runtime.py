import ctypes
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LedRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        library = ROOT / f'tests/build/led_sim_{os.getpid()}.dll'
        shared = ROOT.parent.parent / 'esp32C3/Bluedroid_Connection/main'
        result = subprocess.run([os.environ.get('TOUCH_TEST_TCC', str(ROOT / 'tests/tools/tcc/tcc.exe')), '-shared', '-o', str(library),
            '-include', str(ROOT / 'tests/include/idf_test.h'), '-I', str(ROOT / 'tests/include'),
            '-I', str(ROOT / 'main'), '-I', str(shared), str(ROOT / 'tests/led_sim.c'),
            str(ROOT / 'main/led_logic.c'), str(shared / 'touch_layout.c')], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        cls.sim = ctypes.CDLL(str(library))
        cls.sim.sim_led_command.restype = ctypes.c_char_p
        cls.sim.sim_led_trace.restype = ctypes.c_char_p

    def setUp(self):
        self.sim.sim_led_reset()

    def start(self):
        self.assertEqual(self.sim.sim_led_start(), 0)
        self.command('LED,MODE,LIVE')
        self.command('LED,BRIGHT,16')
        self.command('LED,TIMING,XL')

    def command(self, line):
        return self.sim.sim_led_command(line.encode())

    def pixel(self, i):
        return tuple(self.sim.sim_led_byte(i, c) for c in range(3))

    def test_stream_maps_both_banks_expires_and_supports_many_updates(self):
        self.start()
        self.assertIn(b'CAP,1', self.command('LED,GUIDE,STATUS'))
        for i in range(300):
            self.sim.sim_led_time(i*20)
            self.assertEqual(self.command('LED,GUIDE,100001,21'), b'OK,LED,GUIDE\r\n')
        self.sim.sim_led_run(1)
        for pixel in (0,20,21,26): self.assertEqual(self.pixel(pixel), (0,0,16))
        self.sim.sim_led_time(7100)
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i)==(0,0,0) for i in range(27)))

    def test_stream_clear_demo_and_invalid_mask(self):
        self.start()
        for text in ('LED,GUIDE,200000,0','LED,GUIDE,0,40','LED,GUIDE,1,1x','LED,GUIDE,-1,0'):
            self.assertIn(b'ERROR',self.command(text))
        self.command('LED,GUIDE,1,1')
        self.command('LED,STOP')
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i)==(0,0,0) for i in range(27)))
        self.command('LED,MODE,DEMO')
        self.sim.sim_led_run(1)
        self.assertTrue(all(max(self.pixel(i))>0 for i in range(27)))

    def test_demo_boot_animates_both_complete_banks_without_host_commands(self):
        self.assertEqual(self.sim.sim_led_start(), 0)
        self.assertIn(b'MODE,4,BRIGHT,32', self.command('LED,STATUS'))
        self.assertIn(b'TIMING,LEGACY', self.command('LED,STATUS'))
        self.sim.sim_led_run(1)
        initial = [self.pixel(i) for i in range(27)]
        self.assertTrue(all(max(p) > 0 for p in initial))
        self.assertGreater(len(set(initial)), 8)
        for ms in (20, 400, 2700, 20000, 1000000):
            self.sim.sim_led_time(ms)
            self.sim.sim_led_run(1)
            frame = [self.pixel(i) for i in range(27)]
            self.assertTrue(all(0 < max(p) <= 32 for p in frame))
            self.assertNotEqual(initial[:13], frame[:13])
            self.assertNotEqual(initial[13:], frame[13:])
        self.assertEqual(self.sim.sim_led_gpio_errors(), 0)
        self.assertEqual(self.sim.sim_led_waits(), self.sim.sim_led_transmits())

    def test_demo_feedback_release_returns_to_background_and_off_is_black(self):
        self.assertEqual(self.sim.sim_led_start(), 0)
        self.sim.sim_led_key(1, 1)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20), (32, 8, 32))
        self.assertEqual(self.pixel(21), (32, 8, 32))
        self.sim.sim_led_pick(6)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(21), (8, 32, 32))
        self.sim.sim_led_key(1, 0)
        self.sim.sim_led_time(200)
        self.sim.sim_led_run(1)
        self.assertNotEqual(self.pixel(20), (32, 8, 32))
        self.assertGreater(max(self.pixel(20)), 0)
        self.command('LED,MODE,OFF')
        self.sim.sim_led_run(2)
        self.assertTrue(all(self.pixel(i) == (0, 0, 0) for i in range(27)))

    def test_demo_restores_both_banks_from_manual_and_scope_and_honors_level(self):
        self.assertEqual(self.sim.sim_led_start(), 0)
        self.command('LED,OUTPUT,7,16,0,0,1000,500')
        self.sim.sim_led_run(1)
        self.command('LED,SCOPE,PIN,7')
        self.command('LED,SCOPE,BLUE')
        self.sim.sim_led_run(1)
        self.assertEqual(self.command('LED,MODE,DEMO'), b'OK,LED\r\n')
        self.assertIn(b'ENABLED,0', self.command('LED,OUTPUT,STATUS'))
        self.assertIn(b'SCOPE,0', self.command('LED,STATUS'))
        for level in (0, 1, 32, 255):
            self.command(f'LED,BRIGHT,{level}')
            self.sim.sim_led_run(3)
            self.assertTrue(all(0 <= v <= level for i in range(27) for v in self.pixel(i)))
        self.command('LED,MODE,LIVE')
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i) == (0, 0, 0) for i in range(27)))

    def test_two_gpio_banks_800k_symbols_and_low_priority_worker(self):
        self.start()
        self.assertEqual(self.sim.sim_led_priority(), 2)
        self.assertEqual(self.sim.sim_led_resolution(0), 20000000)
        self.assertEqual(self.sim.sim_led_dma(), 1)
        self.assertGreater(self.sim.sim_led_memory() // 2, 14 * 24 + 2)
        self.sim.sim_led_run(2)
        self.assertEqual([self.sim.sim_led_pin(b) for b in range(2)], [3, 7])
        self.assertEqual(self.sim.sim_led_transmits(), 2)
        self.assertEqual(self.sim.sim_led_waits(), 2)
        self.assertEqual(self.sim.sim_led_bad_timing(), 0)

    def test_shared_position_stays_lit_until_both_keys_release(self):
        self.start()
        self.sim.sim_led_key(1, 1)
        self.sim.sim_led_key(2, 1)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20), (16, 0, 0))
        self.sim.sim_led_key(1, 0)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20), (16, 0, 0))
        self.assertEqual(self.pixel(21), (0, 0, 0))
        self.sim.sim_led_key(2, 0)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20), (0, 0, 0))

    def test_gpio_pushpull_route_and_low_idle_survive_repeated_switches(self):
        self.start()
        self.command('LED,SCOPE,MARK')
        self.sim.sim_led_run(25)
        self.assertGreater(self.sim.sim_led_transmits(), 10)
        self.assertEqual(self.sim.sim_led_gpio_errors(), 0)
        self.assertEqual(self.sim.sim_led_gpio_resets(), 2)  # startup only

    def test_gpio_report_queued_in_output_worker_without_changing_mode(self):
        self.start()
        self.command('LED,MODE,OFF')
        self.assertEqual(self.command('LED,GPIO'), b'OK,LED,GPIO,QUEUED\r\n')
        self.sim.sim_led_run(1)
        self.assertEqual(self.sim.sim_led_gpio_dumps(), 1)
        self.assertIn(b'MODE,0',self.command('LED,STATUS'))
        self.assertEqual(self.sim.sim_led_gpio_errors(), 0)

    def test_offline_touch_is_not_displayed(self):
        self.start()
        self.sim.sim_led_key(1, 1)
        self.sim.sim_led_online(0)
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i) == (0, 0, 0) for i in range(27)))

    def test_ack_pick_is_amber_and_expires(self):
        self.start()
        self.sim.sim_led_pick(6)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(21), (16, 16, 0))
        self.sim.sim_led_time(160)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(21), (0, 0, 0))

    def test_local_guide_overlaps_live_then_ends(self):
        self.start()
        self.sim.sim_led_key(1, 1)
        for line in ('LED,ADD,0,1,6,200', 'LED,MODE,BOTH', 'LED,PLAY'):
            self.assertEqual(self.command(line), b'OK,LED\r\n')
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20), (16, 0, 16))
        self.sim.sim_led_time(200)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20), (16, 0, 0))
        self.assertIn(b'PLAYING,0', self.command('LED,STATUS'))
        self.command('LED,MODE,OFF')
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i) == (0, 0, 0) for i in range(27)))

    def test_cue_capacity_invalid_commands_and_edit_while_playing(self):
        self.start()
        for line in ('LED,BRIGHT,256', 'LED,ADD,0,22,1,10', 'LED,ADD,0,1,7,10', 'LED,ADD,0,0,0,10', 'LED,ADD,3599999,1,1,2'):
            self.assertTrue(self.command(line).startswith(b'ERROR,LED'))
        for _ in range(256):
            self.assertEqual(self.command('LED,ADD,0,1,1,50'), b'OK,LED\r\n')
        self.assertTrue(self.command('LED,ADD,0,1,1,50').startswith(b'ERROR,LED'))
        self.assertEqual(self.command('LED,PLAY'), b'OK,LED\r\n')
        self.assertTrue(self.command('LED,ADD,0,1,1,50').startswith(b'ERROR,LED'))

    def test_partial_initialization_and_task_failure_release_rmt(self):
        for kind in (1, 2, 3):
            self.sim.sim_led_reset()
            self.sim.sim_led_fail(kind, 0)
            self.assertEqual(self.sim.sim_led_start(), 0x101)
            self.assertEqual(self.sim.sim_led_deletes(), 0 if kind == 1 else 1)
            self.assertIn(b'NOT_READY', self.command('LED,STATUS'))
        self.sim.sim_led_reset()
        self.sim.sim_led_fail_task()
        self.assertEqual(self.sim.sim_led_start(), 0x101)
        self.assertEqual(self.sim.sim_led_deletes(), 1)
        self.assertEqual(self.sim.sim_led_encoder_deletes(), 4)

    def test_output_failure_stops_led_worker_and_reports_not_ready(self):
        self.start()
        self.sim.sim_led_fail_tx()
        self.sim.sim_led_run(1)
        self.assertIn(b'NOT_READY', self.command('LED,STATUS'))

    def test_complete_byte_frames_are_default_and_legacy_copy_is_selectable(self):
        self.start()
        self.command('LED,OUTPUT,7,128,1,255,0,0')
        self.sim.sim_led_run(3)
        self.assertEqual(self.sim.sim_led_byte_transmits(),self.sim.sim_led_transmits())
        self.assertEqual(self.pixel(13),(1,128,255))
        self.assertIn(b'ENCODER,BYTES',self.command('LED,STATUS'))
        before=self.sim.sim_led_byte_transmits()
        self.command('LED,ENCODER,COPY');self.sim.sim_led_run(1)
        self.assertEqual(self.sim.sim_led_byte_transmits(),before)
        self.assertEqual(self.pixel(13),(1,128,255))
        self.assertIn(b'ENCODER,COPY',self.command('LED,STATUS'))

    def test_byte_encoder_creation_failure_cleans_partial_resources(self):
        for profile in (0,1,2):
            self.sim.sim_led_reset();self.sim.sim_led_fail(4,profile)
            self.assertEqual(self.sim.sim_led_start(),0x101)
            self.assertEqual(self.sim.sim_led_deletes(),1)
            self.assertEqual(self.sim.sim_led_encoder_deletes(),profile+1)

    def test_pad_probe_checks_both_full_frames_and_restores_off(self):
        self.start()
        self.command('LED,MODE,OFF')
        self.assertIn(b'QUEUED', self.command('LED,CHECK'))
        self.assertIn(b'BUSY', self.command('LED,CHECK'))
        self.sim.sim_led_run(2)
        trace = self.sim.sim_led_trace()
        self.assertIn(b'GPIO,3,RESULT,PASS,BITS,312,EXPECTED,312', trace)
        self.assertIn(b'GPIO,7,RESULT,PASS,BITS,336,EXPECTED,336', trace)
        self.assertIn(b'T0H_NS,250,250,T1H_NS,850,850', trace)
        self.assertIn(b'SCOPE,FIRST_FRAME_S3_PAD', trace)
        self.assertIn(b'RESET_OK,1', trace)
        self.assertEqual(self.sim.sim_led_transmits(), 4)  # captured first frame + restore, no second probe TX
        self.assertTrue(all(self.pixel(i) == (0, 0, 0) for i in range(27)))
        self.assertIn(b'MODE,0,', self.command('LED,STATUS'))

    def test_pad_probe_rejects_short_frame_corrupt_data_gap_and_invalid_width(self):
        for fault, marker in ((1, b'BITS,24,EXPECTED,336'), (2, b'DATA_ERRORS,1'),
                              (3, b'PERIOD_ERRORS,1'), (4, b'WIDTH_ERRORS,1')):
            with self.subTest(fault=fault):
                self.sim.sim_led_reset()
                self.start()
                self.sim.sim_led_probe_fault(fault)
                self.command('LED,CHECK')
                self.sim.sim_led_run(2)
                trace = self.sim.sim_led_trace()
                self.assertIn(b'GPIO,7,RESULT,FAIL', trace)
                self.assertIn(marker, trace)
                self.assertNotIn(b'NOT_READY', self.command('LED,STATUS'))

    def test_pad_probe_resource_failure_does_not_stop_normal_leds(self):
        for fault in (5, 6):
            self.sim.sim_led_reset()
            self.start()
            self.sim.sim_led_probe_fault(fault)
            self.command('LED,CHECK')
            self.sim.sim_led_run(2)
            self.assertIn(b'RESULT,FAIL', self.sim.sim_led_trace())
            self.assertNotIn(b'NOT_READY', self.command('LED,STATUS'))

    def test_probe_rejects_insufficient_head_or_tail_reset(self):
        for fault in (7, 8):
            self.sim.sim_led_reset()
            self.start()
            self.sim.sim_led_probe_fault(fault)
            self.command('LED,CHECK')
            self.sim.sim_led_run(2)
            self.assertIn(b'RESULT,FAIL', self.sim.sim_led_trace())
            self.assertIn(b'RESET_OK,0', self.sim.sim_led_trace())

    def test_legacy_profile_can_be_measured_without_reflash(self):
        self.start()
        self.command('LED,TIMING,LEGACY')
        self.command('LED,CHECK')
        self.sim.sim_led_run(2)
        self.assertIn(b'T0H_NS,350,350,T1H_NS,900,900', self.sim.sim_led_trace())
        self.assertIn(b'RESULT,PASS', self.sim.sim_led_trace())
        self.assertIn(b'TIMING,LEGACY', self.command('LED,STATUS'))

    def test_scope_marker_repeats_then_off_cancels_it(self):
        self.start()
        self.command('LED,MODE,OFF')
        self.command('LED,SCOPE,MARK')
        self.sim.sim_led_run(5)
        self.assertEqual(self.sim.sim_led_transmits(), 6)
        self.assertTrue(all(self.pixel(i)==((1,1,1) if i<13 else (2,2,2)) for i in range(27)))
        self.command('LED,MODE,OFF')
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i)==(0,0,0) for i in range(27)))

    def test_scope_zero_has_a_bounded_duration_and_restores_live(self):
        self.start()
        self.sim.sim_led_key(1,1)
        self.command('LED,SCOPE,ZERO')
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i)==(0,0,0) for i in range(27)))
        self.sim.sim_led_time(90000)
        self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20),(16,0,0))
        self.assertIn(b'SCOPE,0',self.command('LED,STATUS'))

    def test_single_pin_green_stream_has_no_repeated_matrix_switch(self):
        for pin,bank in ((3,0),(7,1)):
            self.sim.sim_led_reset()
            self.start()
            self.command(f'LED,SCOPE,PIN,{pin}')
            self.command('LED,SCOPE,GREEN')
            self.sim.sim_led_run(1)
            switches=self.sim.sim_led_switches()
            self.sim.sim_led_run(20)
            self.assertEqual(self.sim.sim_led_switches(),switches)
            self.assertGreater(self.sim.sim_led_bank_frames(bank),5)
            self.assertEqual(self.sim.sim_led_bank_frames(1-bank),0)
            pixels=range(13) if bank==0 else range(13,27)
            self.assertTrue(all(self.pixel(i)==(16,0,0) for i in pixels))
            self.assertEqual(self.sim.sim_led_gpio_errors(),0)

    def test_live_probe_captures_normal_color_without_replacing_payload(self):
        self.start()
        self.command('LED,SCOPE,BLUE')
        self.command('LED,CHECK,LIVE')
        self.sim.sim_led_run(2)
        self.assertTrue(all(self.pixel(i)==(0,0,16) for i in range(27)))
        self.assertIn(b'GPIO,3,RESULT,PASS',self.sim.sim_led_trace())
        self.assertIn(b'GPIO,7,RESULT,PASS',self.sim.sim_led_trace())

    def test_missing_rx_idle_is_reported_as_unmeasured_not_full_timing_pass(self):
        self.start()
        self.sim.sim_led_probe_fault(9)
        self.command('LED,CHECK,LIVE')
        self.sim.sim_led_run(2)
        trace=self.sim.sim_led_trace()
        self.assertIn(b'RESULT,DATA_ONLY',trace)
        self.assertIn(b'RESET_MEASURED,0',trace)
        self.assertNotIn(b'RESULT,PASS',trace)

    def test_tx_status_and_scope_selector_validate_pin_and_color(self):
        self.start()
        self.assertIn(b'ERROR',self.command('LED,SCOPE,PIN,8'))
        self.command('LED,SCOPE,RED')
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i)==(0,16,0) for i in range(27)))
        self.command('LED,TX,STATUS')
        trace=self.sim.sim_led_trace()
        self.assertIn(b'LED,TX,GPIO,3,FRAMES,1,BITS,312',trace)
        self.assertIn(b'LED,TX,GPIO,7,FRAMES,1,BITS,336',trace)

    def test_slow714_extends_only_low_and_probe_checks_1400ns_period(self):
        self.start()
        self.command('LED,SCOPE,PIN,7')
        self.command('LED,SCOPE,GREEN')
        self.command('LED,TIMING,SLOW714')
        self.command('LED,CHECK,LIVE')
        self.sim.sim_led_run(2)
        self.assertEqual((self.sim.sim_led_zero_high(),self.sim.sim_led_zero_low()),(7,21))
        self.assertEqual((self.sim.sim_led_one_high(),self.sim.sim_led_one_low()),(18,10))
        self.assertEqual(self.sim.sim_led_bad_timing(),0)
        self.assertIn(b'PERIOD_NS,1400,1400',self.sim.sim_led_trace())
        self.assertIn(b'PERIOD_ERRORS,0',self.sim.sim_led_trace())
        self.assertIn(b'TIMING,SLOW714',self.command('LED,STATUS'))
        self.assertEqual(self.sim.sim_led_bank_frames(0),0)
        self.command('LED,TIMING,LEGACY')
        self.sim.sim_led_run(1)
        self.assertEqual((self.sim.sim_led_zero_high(),self.sim.sim_led_zero_low()),(7,18))
        self.assertEqual((self.sim.sim_led_one_high(),self.sim.sim_led_one_low()),(18,7))

    def test_manual_rgb_uses_grb_and_clears_inactive_bank_once(self):
        self.start()
        self.assertEqual(self.command('LED,OUTPUT,7,30,20,10,0,0'),b'OK,LED\r\n')
        self.sim.sim_led_run(20)
        self.assertTrue(all(self.pixel(i)==(20,30,10) for i in range(13,27)))
        self.assertTrue(all(self.pixel(i)==(0,0,0) for i in range(13)))
        self.assertEqual(self.sim.sim_led_switches(),1)
        self.assertEqual(self.sim.sim_led_bank_frames(0),1)

    def test_manual_blink_uses_board_time_and_configurable_duty(self):
        self.start()
        self.command('LED,OUTPUT,0,40,0,0,1000,250')
        self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i)==(0,40,0) for i in range(27)))
        self.sim.sim_led_time(249);self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(0),(0,40,0))
        self.sim.sim_led_time(250);self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(0),(0,0,0))
        self.sim.sim_led_time(1000);self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(0),(0,40,0))

    def test_manual_pin_change_clears_previous_latched_color(self):
        self.start()
        self.command('LED,OUTPUT,3,0,40,0,0,0');self.sim.sim_led_run(2)
        self.command('LED,OUTPUT,7,0,0,40,0,0');self.sim.sim_led_run(2)
        self.assertEqual(self.pixel(0),(0,0,0))
        self.assertEqual(self.pixel(13),(0,0,40))
        self.command('LED,MODE,OFF');self.sim.sim_led_run(1)
        self.assertTrue(all(self.pixel(i)==(0,0,0) for i in range(27)))
        self.assertIn(b'ENABLED,0',self.command('LED,OUTPUT,STATUS'))

    def test_manual_output_rejects_bad_pin_rgb_and_blink_ranges(self):
        self.start()
        for args in ['8,1,2,3,0,0','3,256,2,3,0,0','3,1,2,3,0,1',
                     '3,1,2,3,50,25','3,1,2,3,1000,0','3,1,2,3,1000,995',
                     '3,1,2,3,60001,100','3,1,2,3,1000,500,trailing']:
            self.assertIn(b'ERROR,LED,OUTPUT_ARG',self.command('LED,OUTPUT,'+args))
        self.assertIn(b'ENABLED,0',self.command('LED,OUTPUT,STATUS'))

    def test_manual_to_live_restores_key_lights_and_scope_can_replace_manual(self):
        self.start()
        self.sim.sim_led_key(1,1)
        self.command('LED,OUTPUT,0,40,0,0,0,0');self.sim.sim_led_run(1)
        self.command('LED,MODE,LIVE');self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(20),(16,0,0))
        self.command('LED,OUTPUT,0,40,0,0,0,0')
        self.command('LED,SCOPE,BLUE');self.sim.sim_led_run(1)
        self.assertEqual(self.pixel(0),(0,0,16))
        self.assertIn(b'ENABLED,0',self.command('LED,OUTPUT,STATUS'))

    def test_full_frame_capture_queues_unmodified_frames_and_measures_middle_idles(self):
        for encoder in ('BYTES','COPY'):
            self.sim.sim_led_reset();self.start()
            self.command('LED,ENCODER,'+encoder)
            self.command('LED,OUTPUT,7,128,1,255,0,0')
            self.command('LED,CHECK,FRAME');self.sim.sim_led_run(2)
            trace=self.sim.sim_led_trace()
            self.assertIn(b'LED,FRAME,GPIO,7,RESULT,PASS,FRAMES,3,BITS,1008,EXPECTED,1008',trace)
            self.assertIn(b'F0_BITS,336,F1_BITS,336,F2_BITS,336,DATA_ERRORS,0',trace)
            self.assertIn(b'TX_GRB,01,80,FF,RX_GRB,01,80,FF',trace)
            self.assertIn(b'HEAD_LOW_NS,600000,TAIL_LOW_NS,600000,RESET_OK,1',trace)
            self.assertTrue(all(self.pixel(i)==(1,128,255) for i in range(13,27)))
            self.assertEqual(self.sim.sim_led_bad_timing(),0)
            self.assertEqual(self.sim.sim_led_gpio_errors(),0)

    def test_full_frame_probe_cannot_pass_short_capture_wrong_color_or_missing_reset(self):
        for fault in (10,11,12,13):
            with self.subTest(fault=fault):
                self.sim.sim_led_reset();self.start()
                self.sim.sim_led_probe_fault(fault)
                self.command('LED,OUTPUT,7,0,16,0,0,0')
                self.command('LED,CHECK,FRAME');self.sim.sim_led_run(2)
                self.assertIn(b'LED,FRAME,GPIO,7,RESULT,FAIL',self.sim.sim_led_trace())
                self.assertNotIn(b'LED,FRAME,GPIO,7,RESULT,PASS',self.sim.sim_led_trace())
                self.assertNotIn(b'NOT_READY',self.command('LED,STATUS'))


if __name__ == '__main__':
    unittest.main()
