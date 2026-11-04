import ctypes
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LinkRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = ROOT / 'tests/build'
        build.mkdir(exist_ok=True)
        shared = ROOT.parent.parent / 'esp32C3/Bluedroid_Connection/main'
        library = build / f'link_sim_{os.getpid()}.dll'
        command = [os.environ.get('TOUCH_TEST_TCC', str(ROOT / 'tests/tools/tcc/tcc.exe')), '-shared', '-o', str(library),
                   '-include', str(ROOT / 'tests/include/idf_test.h'), '-I', str(ROOT / 'tests/include'),
                   '-I', str(ROOT / 'main'), '-I', str(shared), str(ROOT / 'tests/link_sim.c'),
                   str(ROOT / 'main/fpga_protocol.c'), str(ROOT / 'main/fpga_scheduler.c'),
                   str(ROOT / 'main/note_trace.c'), str(shared / 'touch_layout.c')]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        cls.sim = ctypes.CDLL(str(library))
        cls.sim.sim_link_status.restype = ctypes.c_char_p
        cls.sim.sim_link_host.restype = ctypes.c_char_p
        cls.sim.sim_link_accepted_tick.restype = ctypes.c_uint
        cls.sim.sim_link_bulk_error.restype = ctypes.c_char_p

    def setUp(self):
        self.assertEqual(self.sim.sim_link_reset(), 0)
        self.sim.sim_link_online(1)

    def run_link(self, iterations):
        self.sim.sim_link_run(iterations)
        self.assertEqual(self.sim.sim_link_crc_errors(), 0)

    def accepted(self, kind=None):
        frames = [bytes(self.sim.sim_link_accepted_byte(index, offset) for offset in range(64))
                  for index in range(self.sim.sim_link_accepted_count())]
        return frames if kind is None else [frame for frame in frames if frame[3] == kind]

    def bulk(self, payload, mode=1):
        data = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
        return self.sim.sim_link_bulk(data, len(payload), mode)

    def test_bulk_fragments_reassemble_without_duplicate_replay(self):
        for length in (6, 36, 38, 266):
            with self.subTest(length=length):
                self.setUp()
                payload = bytes((index * 13) & 255 for index in range(length))
                self.assertTrue(self.bulk(payload))
                frames = self.accepted(3)
                self.assertEqual(b''.join(frame[8:8+frame[7]] for frame in frames), payload)
                self.assertEqual(len(frames), (length + 47) // 48)
                self.assertEqual([frame[6] for frame in frames],
                                 [int(i == 0) | (2 if i == len(frames)-1 else 0)
                                  for i in range(len(frames))])
                self.assertEqual([int.from_bytes(frame[4:6], 'little') for frame in frames],
                                 list(range(1, len(frames)+1)))
                self.assertEqual(self.sim.sim_link_crc_errors(), 0)
                self.assertEqual(self.sim.sim_link_bulk_error(), b'OK')

    def test_bulk_missing_capability_is_explicit(self):
        self.assertFalse(self.bulk(bytes(6), 0))
        self.assertEqual(self.sim.sim_link_bulk_error(), b'NO_CAPABILITY')
        self.assertEqual(self.sim.sim_link_transfer_count(), 0)

    def test_bulk_fpga_packet_rejection_is_explicit(self):
        self.assertFalse(self.bulk(bytes(6), 2))
        self.assertEqual(self.sim.sim_link_bulk_error(), b'FPGA_PACKET_ERROR')

    def test_bulk_uncertain_ack_times_out_without_replacing_packet(self):
        self.assertFalse(self.bulk(bytes(range(36)), 3))
        self.assertEqual(self.sim.sim_link_bulk_error(), b'FRAGMENT_ACK_TIMEOUT')
        frames = [bytes(self.sim.sim_link_transmitted_byte(i, k) for k in range(64))
                  for i in range(self.sim.sim_link_transfer_count())]
        self.assertGreater(len(frames), 2)
        self.assertTrue(all(frame == frames[0] for frame in frames))

    def test_bulk_busy_replay_has_bounded_deadline(self):
        self.assertFalse(self.bulk(bytes(6), 4))
        self.assertEqual(self.sim.sim_link_bulk_error(), b'REPLAY_TIMEOUT')

    @staticmethod
    def pick_string(frame):
        return 7 - frame[31].bit_length()

    @staticmethod
    def pick_velocity(frame):
        return frame[32 + frame[31].bit_length() - 1]

    def test_panel_requires_all_crc_valid_banks(self):
        self.sim.sim_link_panel(1)
        self.run_link(5)
        self.assertEqual(self.sim.sim_link_host(b'FPGA,PANEL'),b'PANEL,WAIT\r\n')
        self.run_link(8)
        expected='PANEL,8,3,34,'+','.join(map(str,range(32)))+'\r\n'
        self.assertEqual(self.sim.sim_link_host(b'FPGA,PANEL'),expected.encode())

    def test_panel_rejects_corrupt_replies(self):
        self.sim.sim_link_panel(1)
        self.sim.sim_link_bad_replies(20)
        self.run_link(8)
        self.assertEqual(self.sim.sim_link_host(b'FPGA,PANEL'),b'PANEL,WAIT\r\n')

    def test_panel_rejects_wrong_session(self):
        self.sim.sim_link_panel(2)
        self.run_link(12)
        self.assertEqual(self.sim.sim_link_host(b'FPGA,PANEL'),b'PANEL,WAIT\r\n')

    def test_pick_captures_touch_at_enqueue_not_transmit(self):
        self.sim.sim_link_key(25)
        self.assertTrue(self.sim.sim_link_pick(6, 99))
        self.sim.sim_link_key(49)
        self.run_link(8)
        frames = self.accepted(2)
        self.assertEqual(len(frames), 1)
        frame = frames[0]
        self.assertEqual(frame[31:33], bytes([1, 99]))
        self.assertEqual(frame[38], 0xC1)
        self.assertEqual(int.from_bytes(frame[8:24], 'little'), 1 << 48)
        self.assertEqual(int.from_bytes(frame[40:56], 'little'), 1 << 24)

    def test_continuous_controls_do_not_starve_hall(self):
        for unused in range(32):
            self.assertTrue(self.sim.sim_link_control(80))
        for velocity in range(90, 98):
            self.assertTrue(self.sim.sim_link_pick(6, velocity))
        self.sim.sim_link_continuous_controls(1)
        self.run_link(80)
        frames = self.accepted()
        self.assertEqual([frame[3] for frame in frames[:16]], [1, 2] * 8)
        self.assertEqual([frame[32] for frame in self.accepted(2)], list(range(90, 98)))

    def test_hall_backlog_does_not_starve_controls(self):
        for velocity in range(60, 92):
            self.assertTrue(self.sim.sim_link_pick(6, velocity))
        for level in (70, 71, 72):
            self.assertTrue(self.sim.sim_link_control(level))
        self.run_link(24)
        self.assertEqual([frame[3] for frame in self.accepted()[:6]], [1, 2] * 3)
        self.assertEqual([frame[27] for frame in self.accepted(1)], [70, 71, 72])

    def test_busy_control_slot_does_not_block_hall_or_touch_heartbeats(self):
        self.sim.sim_link_hold_command(1)
        for unused in range(4):
            self.assertTrue(self.sim.sim_link_control(80))
        for velocity in range(90, 96):
            self.assertTrue(self.sim.sim_link_pick(6, velocity))
        self.sim.sim_link_mutation(10, 49)
        self.run_link(48)
        self.assertEqual(len(self.accepted(1)), 1)
        self.assertEqual(len(self.accepted(2)), 6)
        self.assertEqual(self.sim.sim_link_queue_count(1), 3)
        self.assertEqual(int.from_bytes(self.accepted(0)[-1][8:24], 'little'), 1 << 48)

    def test_busy_hall_slot_does_not_block_controls(self):
        self.sim.sim_link_hold_hall(1)
        for unused in range(3):
            self.assertTrue(self.sim.sim_link_pick(6, 99))
            self.assertTrue(self.sim.sim_link_control(80))
        self.run_link(30)
        self.assertEqual(len(self.accepted(2)), 1)
        self.assertEqual(len(self.accepted(1)), 3)
        self.assertEqual(self.sim.sim_link_queue_count(2), 2)
        self.assertTrue(self.accepted(0))

    def test_uncertain_ack_retries_identical_frame_without_duplicate(self):
        self.sim.sim_link_key(25)
        self.assertTrue(self.sim.sim_link_pick(6, 99))
        self.sim.sim_link_bad_replies(4)
        self.sim.sim_link_mutation(1, 49)
        self.run_link(14)
        transmitted = [bytes(self.sim.sim_link_transmitted_byte(index, offset) for offset in range(64))
                       for index in range(5)]
        self.assertTrue(all(frame == transmitted[0] for frame in transmitted))
        self.assertEqual(len(self.accepted(2)), 1)
        self.assertEqual(int.from_bytes(self.accepted(2)[0][40:56], 'little'), 1 << 24)
        self.assertEqual(self.sim.sim_link_led_picks(), 1)
        self.assertEqual(self.sim.sim_link_led_string(), 6)

    def test_snapshot_fifo_keeps_order_and_explicitly_rejects_overflow(self):
        for index in range(32):
            self.sim.sim_link_key(index + 1)
            self.assertTrue(self.sim.sim_link_pick(6, 40 + index))
        self.assertFalse(self.sim.sim_link_pick(6, 100))
        self.sim.sim_link_key(100)
        self.run_link(80)
        frames = self.accepted(2)
        self.assertEqual(len(frames), 32)
        for index, frame in enumerate(frames):
            self.assertEqual(frame[32], 40 + index)
            self.assertEqual(int.from_bytes(frame[40:56], 'little'), 1 << index)

    def test_offline_and_bad_parameters_do_not_enter_queue(self):
        self.sim.sim_link_online(0)
        self.assertFalse(self.sim.sim_link_pick(6, 99))
        self.sim.sim_link_online(1)
        for string_number, velocity in ((0, 99), (7, 99), (6, 0), (6, 128)):
            self.assertFalse(self.sim.sim_link_pick(string_number, velocity))
        self.assertEqual(self.sim.sim_link_queue_count(2), 0)

    def test_legacy_fpga_reply_remains_usable_without_snapshot_guarantee(self):
        self.sim.sim_link_legacy_reply()
        self.assertTrue(self.sim.sim_link_pick(6, 99))
        self.run_link(8)
        self.assertEqual(len(self.accepted(2)), 1)
        self.assertIn(b'SNAPSHOT_CAP,0', self.sim.sim_link_status())

    def test_offline_chip_keys_are_excluded_from_captured_event(self):
        key = next(index for index in range(1, 127) if self.sim.sim_link_key_chip(index) == 2)
        self.sim.sim_link_online_mask(0xFB)
        self.sim.sim_link_key(key)
        self.assertTrue(self.sim.sim_link_pick(6, 99))
        self.run_link(8)
        self.assertEqual(int.from_bytes(self.accepted(2)[0][40:56], 'little'), 0)

    def test_status_exposes_capability_credits_and_queue_depth(self):
        self.sim.sim_link_hold_command(1)
        for unused in range(3):
            self.assertTrue(self.sim.sim_link_control(80))
        self.run_link(10)
        status = self.sim.sim_link_status()
        self.assertIn(b'SNAPSHOT_CAP,1,CTRL_READY,0,HALL_READY,1,CTRL_QUEUE,2,PICK_QUEUE,0,TOUCH_ENABLED,1', status)
        self.assertLess(len(status), 384)
        self.assertTrue(status.endswith(b'\r\n'))

    def test_strum_six_strings_share_enqueue_snapshot_and_velocity(self):
        self.sim.sim_link_key(25)
        self.assertTrue(self.sim.sim_link_strum(103))
        self.sim.sim_link_key(49)
        self.sim.sim_link_mutation(12, 73)
        self.run_link(80)
        frames = self.accepted(2)
        self.assertEqual([self.pick_string(frame) for frame in frames], [6, 5, 4, 3, 2, 1])
        for frame in frames:
            self.assertEqual(self.pick_velocity(frame), 103)
            self.assertEqual(int.from_bytes(frame[40:56], 'little'), 1 << 24)
        self.assertEqual(int.from_bytes(frames[-1][8:24], 'little'), 1 << 72)

    def test_strum_spacing_controls_and_live_touch_continue(self):
        self.assertTrue(self.sim.sim_link_strum(103))
        self.sim.sim_link_continuous_controls(1)
        self.sim.sim_link_mutation(8, 49)
        self.run_link(100)
        pick_indices = [index for index, frame in enumerate(self.accepted()) if frame[3] == 2]
        self.assertEqual(len(pick_indices), 6)
        ticks = [self.sim.sim_link_accepted_tick(index) for index in pick_indices]
        self.assertTrue(all(8 <= later - earlier <= 20 for earlier, later in zip(ticks, ticks[1:])))
        self.assertGreater(len(self.accepted(1)), 6)
        self.assertTrue(any(int.from_bytes(frame[8:24], 'little') == 1 << 48 for frame in self.accepted(1)))

    def test_single_pick_interleaves_with_active_strum(self):
        self.sim.sim_link_key(25)
        self.assertTrue(self.sim.sim_link_strum(103))
        for velocity in range(70, 82):
            self.assertTrue(self.sim.sim_link_pick(2, velocity))
        self.run_link(100)
        frames = self.accepted(2)
        self.assertEqual(self.pick_velocity(frames[0]), 103)
        self.assertEqual(self.pick_velocity(frames[1]), 70)
        self.assertEqual([self.pick_string(frame) for frame in frames if self.pick_velocity(frame) == 103], [6, 5, 4, 3, 2, 1])
        self.assertEqual([self.pick_velocity(frame) for frame in frames if self.pick_velocity(frame) != 103], list(range(70, 82)))

    def test_strum_admission_is_one_atomic_queue_job(self):
        for unused in range(31):
            self.assertTrue(self.sim.sim_link_pick(6, 80))
        self.assertTrue(self.sim.sim_link_strum(103))
        self.assertFalse(self.sim.sim_link_strum(104))
        self.run_link(120)
        frames = self.accepted(2)
        self.assertEqual(len(frames), 37)
        self.assertEqual([self.pick_string(frame) for frame in frames[-6:]], [6, 5, 4, 3, 2, 1])
        self.assertEqual([self.pick_velocity(frame) for frame in frames[-6:]], [103] * 6)

    def test_two_strums_do_not_merge_or_replace_snapshots(self):
        self.sim.sim_link_key(25)
        self.assertTrue(self.sim.sim_link_strum(103))
        self.sim.sim_link_key(49)
        self.assertTrue(self.sim.sim_link_strum(104))
        self.run_link(120)
        frames = self.accepted(2)
        self.assertEqual([self.pick_string(frame) for frame in frames], [6, 5, 4, 3, 2, 1] * 2)
        self.assertEqual([self.pick_velocity(frame) for frame in frames], [103] * 6 + [104] * 6)
        self.assertTrue(all(int.from_bytes(frame[40:56], 'little') == 1 << 24 for frame in frames[:6]))
        self.assertTrue(all(int.from_bytes(frame[40:56], 'little') == 1 << 48 for frame in frames[6:]))

    def test_strum_retry_does_not_repeat_first_string(self):
        self.assertTrue(self.sim.sim_link_strum(103))
        self.sim.sim_link_bad_replies(5)
        self.run_link(100)
        self.assertEqual([self.pick_string(frame) for frame in self.accepted(2)], [6, 5, 4, 3, 2, 1])
        self.assertEqual(self.sim.sim_link_led_picks(), 6)
        self.assertEqual(self.sim.sim_link_led_string(), 1)
        first = bytes(self.sim.sim_link_transmitted_byte(0, offset) for offset in range(64))
        for index in range(1, 6):
            self.assertEqual(bytes(self.sim.sim_link_transmitted_byte(index, offset) for offset in range(64)), first)

    def test_cancel_drops_queued_and_active_strum_tails(self):
        self.assertTrue(self.sim.sim_link_strum(103))
        self.sim.sim_link_cancel_strums()
        self.assertTrue(self.sim.sim_link_pick(2, 80))
        self.assertTrue(self.sim.sim_link_strum(104))
        self.sim.sim_link_cancel_at(3)
        self.run_link(80)
        frames = self.accepted(2)
        self.assertEqual([self.pick_velocity(frame) for frame in frames], [80, 104])
        self.assertEqual(self.pick_string(frames[-1]), 6)

    def test_strum_deadline_survives_tick_wrap(self):
        self.sim.sim_link_ticks(0xfffffff0)
        self.assertTrue(self.sim.sim_link_strum(103))
        self.run_link(80)
        self.assertEqual([self.pick_string(frame) for frame in self.accepted(2)], [6, 5, 4, 3, 2, 1])

    def test_strum_validation_and_host_command(self):
        for velocity in (0, 128):
            self.assertFalse(self.sim.sim_link_strum(velocity))
        self.sim.sim_link_online(0)
        self.assertFalse(self.sim.sim_link_strum(103))
        self.sim.sim_link_online(1)
        for line in (b'FPGA,STRUM,0', b'FPGA,STRUM,128', b'FPGA,STRUM,100junk', b'FPGA,STRUM,100,1'):
            self.assertTrue(self.sim.sim_link_host(line).startswith(b'ERROR,'))
        self.assertEqual(self.sim.sim_link_queue_count(2), 0)
        self.assertEqual(self.sim.sim_link_host(b'FPGA,STRUM,100'), b'OK,FPGA,QUEUED\r\n')
        self.run_link(80)
        self.assertEqual(len(self.accepted(2)), 6)


if __name__ == '__main__':
    unittest.main()
