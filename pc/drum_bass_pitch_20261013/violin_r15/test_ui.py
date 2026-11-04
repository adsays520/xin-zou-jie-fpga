import tkinter as tk
from contextlib import contextmanager
import unittest
from unittest.mock import patch

from host_controller import ViolinController, frame, violin_command


class MemoryPort:
    def __init__(self):
        self.is_open = True
        self.packets = []
        self.incoming = bytearray()

    def write(self, data):
        self.packets.append(bytes(data))
        return len(data)

    def flush(self):
        pass

    def read(self, length):
        data = bytes(self.incoming[:length])
        del self.incoming[:length]
        return data

    def close(self):
        self.is_open = False


class InterfaceTests(unittest.TestCase):
    def test_strum_version_mode_snapshot_guards_and_mapping(self):
        with self.hall_application() as (app, panel):
            port = MemoryPort()
            panel.port = port
            panel.handle_line('PONG,R15-HALL-v3.4.4')
            panel.handle_line('FPGA,ONLINE,ACK,1,MODE,PICK,TRIGGER_CAP,1,SNAPSHOT_CAP,1')
            panel.strum()
            self.assertFalse(panel.strum_capable)
            self.assertIn('H7仅测量', panel.mapping.get())
            self.assertNotIn(b'FPGA,STRUM,100\n', port.packets)
            panel.handle_line('PONG,R15-HALL-v3.4.5')
            self.assertTrue(panel.strum_capable)
            self.assertIn('H2～H7', panel.mapping.get())
            panel.handle_line('FPGA,ONLINE,ACK,2,MODE,DIRECT,TRIGGER_CAP,1,SNAPSHOT_CAP,1')
            panel.strum()
            self.assertNotIn(b'FPGA,STRUM,100\n', port.packets)
            panel.handle_line('FPGA,ONLINE,ACK,3,MODE,PICK,TRIGGER_CAP,1,SNAPSHOT_CAP,0')
            panel.strum()
            self.assertNotIn(b'FPGA,STRUM,100\n', port.packets)
            panel.handle_line('FPGA,ONLINE,ACK,4,MODE,PICK,TRIGGER_CAP,1,SNAPSHOT_CAP,1')
            panel.strum()
            self.assertEqual(port.packets[-1], b'FPGA,STRUM,100\n')
            panel.close()
            self.assertFalse(panel.strum_capable)

    @contextmanager
    def hall_application(self):
        original = tk.Tk.__init__
        def hidden_init(instance, *arguments, **keywords):
            original(instance, *arguments, **keywords)
            instance.withdraw()
        with patch.object(tk.Tk, '__init__', hidden_init):
            app = ViolinController()
        try:
            app.show_page('hall')
            yield app, app.hall_panel
        finally:
            app.hall_panel.close()
            app.disconnect()
            for token in app.tk.call('after', 'info'):
                app.tk.call('after', 'cancel', token)
            app.destroy()

    def test_hidden_interface_navigation_and_controls(self):
        original = tk.Tk.__init__

        def hidden_init(instance, *arguments, **keywords):
            original(instance, *arguments, **keywords)
            instance.withdraw()

        with patch.object(tk.Tk, '__init__', hidden_init):
            app = ViolinController()
        port = MemoryPort()
        try:
            app.port = port
            app.open_violin()
            app.update_idletasks()
            self.assertEqual(app.active_page, 'violin')
            self.assertEqual(port.packets[-1], frame(4, 3))
            self.assertTrue(app.send_piano_key_for(69, 100, True))
            self.assertEqual(port.packets[-1], violin_command(69, 100, 1))
            self.assertTrue(app.send_piano_key_for(72, 80, True))
            self.assertEqual(port.packets[-1], violin_command(72, 80, 3))
            app.violin_level.set(73)
            app.send_violin_level()
            self.assertEqual(port.packets[-1], frame(0x70, 3, 73))
            app.show_page('guitar')
            self.assertEqual(port.packets[-1], frame(4, 3))
            self.assertFalse(app.violin_keys.held)
            self.assertTrue(app.send_timbre(1))
            self.assertEqual(app.current_timbre, 1)
        finally:
            app.disconnect()
            for token in app.tk.call('after', 'info'):
                app.tk.call('after', 'cancel', token)
            app.destroy()

    def test_hall_panel_requires_handshake_and_fpga_capability(self):
        original = tk.Tk.__init__
        def hidden_init(instance, *arguments, **keywords):
            original(instance, *arguments, **keywords)
            instance.withdraw()
        with patch.object(tk.Tk, '__init__', hidden_init):
            app = ViolinController()
        panel = app.hall_panel
        port = MemoryPort()
        panel.port = port
        try:
            app.show_page('hall')
            self.assertEqual(app.active_page, 'hall')
            panel.pick(6)
            self.assertEqual(port.packets, [b'PING\n'])
            panel.handle_line('HOST_REPLY: PONG,R15-HALL-v3.4')
            self.assertTrue(panel.compatible)
            panel.set_mode('HALL')
            self.assertNotIn(b'FPGA,TRIGGER,HALL\n', port.packets)
            panel.handle_line('FPGA,ONLINE,ACK,1,MODE,DIRECT,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,0')
            panel.set_mode('HALL')
            self.assertEqual(port.packets[-2:], [b'HALL,ARM,OFF\n', b'FPGA,TRIGGER,HALL\n'])
            panel.handle_line('FPGA,ONLINE,ACK,2,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2')
            panel.pick(6)
            panel.pick(6, direct=True)
            self.assertEqual(port.packets[-2:], [b'FPGA,PICK,6,100\n', b'FPGA,PLUCK,6,0,100\n'])
            for channel in panel.channels:
                channel.set(False)
            panel.channels[0].set(True)
            panel.apply_mask()
            self.assertEqual(port.packets[-1], b'HALL,MASK,0x01\n')
            panel.handle_line('HALL,1,RAW,1500,BASE,1500,THRESHOLD,32,VALID,1,EVENTS,3,REJECTED,0,ERRORS,0')
            self.assertEqual(panel.readings.item('1', 'values')[1:9], ('1500', '1500', '0', '32', '1', '3', '0', '0'))
            with patch('hall_panel.messagebox.askyesno', return_value=False):
                panel.arm()
            self.assertNotIn(b'HALL,ARM,ON\n', port.packets)
            with patch('hall_panel.messagebox.askyesno', return_value=True):
                panel.arm()
            self.assertEqual(port.packets[-1], b'HALL,ARM,ON\n')
            panel.handle_line('FPGA,ONLINE,ACK,3,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,0,OVERRIDE,0')
            self.assertFalse(panel.fpga_capable)
            with patch('hall_panel.messagebox.askyesno', return_value=True):
                panel.arm()
            self.assertEqual(port.packets[-1], b'HALL,ARM,ON\n')
            panel.close()
            self.assertEqual(port.packets[-1], b'HALL,ARM,OFF\n')
        finally:
            panel.close()
            app.disconnect()
            for token in app.tk.call('after', 'info'):
                app.tk.call('after', 'cancel', token)
            app.destroy()

    def test_unconfirmed_handshake_does_not_blame_fpga_version(self):
        with self.hall_application() as (app, panel):
            port = MemoryPort()
            panel.port = port
            panel.set_mode('HALL')
            panel.arm()
            panel.pick(6)
            self.assertIsNone(panel.fpga_capable)
            self.assertEqual(port.packets, [b'PING\n'])
            messages = panel.messages.get('1.0', 'end')
            self.assertIn('FPGA能力未知', messages)
            self.assertNotIn('TRIGGER_CAP=0', messages)
            self.assertNotIn('需配套新位流', messages)

    def test_ping_retries_and_fragmented_minor_version_reply(self):
        with self.hall_application() as (app, panel):
            port = MemoryPort()
            panel.port = port
            panel.request_handshake(now=100.0)
            panel.request_handshake(now=100.5)
            panel.request_handshake(now=101.0)
            self.assertEqual(port.packets, [b'PING\n', b'PING\n'])
            port.incoming.extend(b'I HOST_REPLY: PONG,R15-HALL-v3.')
            with patch('hall_panel.time.monotonic', return_value=101.5):
                panel.poll()
            self.assertFalse(panel.compatible)
            port.incoming.extend(b'4.1\r\n')
            with patch('hall_panel.time.monotonic', return_value=102.0):
                panel.poll()
            self.assertTrue(panel.compatible)
            self.assertIn('v3.4.1', panel.status.get())
            self.assertEqual(port.packets[-1], b'HALL,STATUS\nFPGA,STATUS\n')
            self.assertFalse(any(b'ARM,ON' in packet or b'FPGA,TRIGGER' in packet for packet in port.packets))

    def test_missing_status_fields_are_unknown_not_false_or_disconnect(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.handle_line('PONG,R15-HALL-v3.4.1')
            panel.handle_line('FPGA,ONLINE,ACK,1,MODE,DIRECT,FRETS,0,0,0,0,0,0')
            self.assertIsNone(panel.fpga_capable)
            panel.set_mode('HALL')
            self.assertNotIn(b'FPGA,TRIGGER,HALL\n', panel.port.packets)
            panel.handle_line('FPGA,ONLINE,ACK,2,TRIGGER_CAP,1')
            self.assertTrue(panel.fpga_capable)
            self.assertIsNone(panel.effective_mode)
            panel.arm()
            self.assertNotIn(b'HALL,ARM,ON\n', panel.port.packets)
            self.assertTrue(panel.port.is_open)

    def test_status_timeout_and_spi_offline_are_distinct(self):
        with self.hall_application() as (app, panel):
            port = MemoryPort()
            panel.port = port
            panel.handle_line('PONG,R15-HALL-v3.4.1')
            with patch('hall_panel.time.monotonic', return_value=100.0):
                panel.handle_line('FPGA,ONLINE,ACK,1,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2')
            with patch('hall_panel.time.monotonic', return_value=104.0):
                panel.set_mode('DIRECT')
            self.assertIsNone(panel.fpga_capable)
            self.assertNotIn(b'FPGA,TRIGGER,DIRECT\n', port.packets)
            panel.handle_line('FPGA,OFFLINE,ACK,1,MODE,DIRECT,FRETS,0,0,0,0,0,0,TRIGGER_CAP,0,OVERRIDE,0')
            panel.set_mode('HALL')
            self.assertFalse(panel.fpga_online)
            self.assertIsNone(panel.fpga_capable)
            self.assertIn('SPI没有有效FPGA确认', panel.messages.get('1.0', 'end'))

    def test_old_buffered_status_cannot_enable_controls_before_ping(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.handle_line('FPGA,ONLINE,ACK,1,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2')
            self.assertIsNone(panel.fpga_capable)
            panel.handle_line('PONG,R15-HALL-v3.40')
            self.assertFalse(panel.compatible)
            panel.handle_line('PONG,R15-HALL-v3.4.1')
            self.assertTrue(panel.compatible)
            self.assertIsNone(panel.fpga_capable)

    def test_main_fpga_connection_is_not_hall_s3_connection(self):
        with self.hall_application() as (app, panel):
            app.port = MemoryPort()
            panel.set_mode('HALL')
            self.assertIsNone(panel.port)
            self.assertEqual(app.port.packets, [])
            self.assertIn('主界面的FPGA连接与此独立', panel.messages.get('1.0', 'end'))

    def test_write_error_always_closes_serial_even_if_disarm_fails(self):
        class BrokenPort(MemoryPort):
            def write(self, data):
                raise IOError('Disconnected')
        with self.hall_application() as (app, panel):
            port = BrokenPort()
            panel.port = port
            panel.compatible = True
            self.assertFalse(panel.send(b'FPGA,STATUS\n'))
            self.assertFalse(port.is_open)
            self.assertIsNone(panel.port)

    def test_hall_rows_compare_displacement_not_raw(self):
        with self.hall_application() as (app, panel):
            panel.handle_line('HALL,1,RAW,1809,BASE,1808,THRESHOLD,1596,VALID,1,EVENTS,0,REJECTED,0,ERRORS,0')
            panel.handle_line('HALL,2,RAW,1400,BASE,1411,THRESHOLD,32,VALID,1,EVENTS,2,REJECTED,1,ERRORS,3')
            self.assertEqual(panel.readings.set('1', 'delta'), '1')
            self.assertEqual(panel.readings.set('1', 'threshold'), '1596')
            self.assertEqual(panel.readings.set('2', 'delta'), '11')
            self.assertEqual(panel.readings.set('2', 'events'), '2')
            self.assertEqual(panel.readings.set('2', 'rejected'), '1')
            self.assertEqual(panel.readings.set('2', 'errors'), '3')

    def test_hall_arm_label_uses_board_reply_not_sent_command(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.handle_line('PONG,R15-HALL-v3.4.2')
            panel.handle_line('HALL,STATE,ENABLED,1,ARMED,0,MASK,0x3F')
            self.assertIn('仅采样，实物触发未启用', panel.sensor_state.get())
            panel.send(b'HALL,ARM,ON\n')
            self.assertIn('仅采样，实物触发未启用', panel.sensor_state.get())
            panel.handle_line('HOST_REPLY: HALL,STATE,ENABLED,1,ARMED,1,MASK,0x3F')
            self.assertIn('实物触发已启用', panel.sensor_state.get())
            panel.handle_line('HALL,STATE,ENABLED,0,ARMED,0,MASK,0x3F')
            self.assertIn('采样未启用', panel.sensor_state.get())

    def test_copied_diagnostics_include_hidden_rows_and_do_not_send_commands(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.handle_line('PONG,R15-HALL-v3.4.2')
            panel.handle_line('FPGA,ONLINE,ACK,17,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2')
            panel.handle_line('HALL,STATE,ENABLED,1,ARMED,1,MASK,0x3F')
            for channel in range(1, 8):
                panel.handle_line(f'HALL,{channel},RAW,1500,BASE,1500,THRESHOLD,32,VALID,1,EVENTS,3,REJECTED,0,ERRORS,0')
            panel.handle_line('NOTE_ACK: DOWN note=E2 role=FRET_SELECT')
            self.assertNotIn('HALL,1,RAW', panel.messages.get('1.0', 'end'))
            packets_before = list(panel.port.packets)
            with patch.object(panel, 'clipboard_clear') as clear, patch.object(panel, 'clipboard_append') as append:
                panel.copy_diagnostics()
            clear.assert_called_once_with()
            report = append.call_args[0][0]
            for channel in range(1, 8):
                self.assertIn(f'HALL,{channel},RAW,1500,BASE,1500,THRESHOLD,32,VALID,1,EVENTS,3,REJECTED,0,ERRORS,0', report)
            self.assertIn('ARMED,1', report)
            self.assertIn('MODE,PICK', report)
            self.assertIn('role=FRET_SELECT', report)
            self.assertIn('ACK仅确认传输，不证明已经发声', report)
            self.assertEqual(panel.port.packets, packets_before)

    def test_diagnostics_distinguish_missing_and_stale_values(self):
        with self.hall_application() as (app, panel):
            with patch('hall_panel.time.monotonic', return_value=100.0):
                panel.handle_line('HALL,STATE,ENABLED,1,ARMED,1,MASK,0x01')
                panel.handle_line('HALL,1,RAW,1500,BASE,1500,THRESHOLD,32,VALID,1,EVENTS,3,REJECTED,0,ERRORS,0')
            with patch('hall_panel.time.monotonic', return_value=101.0):
                fresh = panel.diagnostic_text()
            self.assertIn('[1.0秒前] HALL,1,RAW', fresh)
            self.assertIn('FPGA: 未收到', fresh)
            self.assertIn('HALL,2: 未收到', fresh)
            with patch('hall_panel.time.monotonic', return_value=104.0):
                stale = panel.diagnostic_text()
            self.assertIn('[4.0秒前，已过期] HALL,STATE', stale)
            self.assertIn('[4.0秒前，已过期] HALL,1,RAW', stale)

    def test_hall_status_timeout_does_not_keep_claiming_armed(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.compatible = True
            panel.next_query = 200.0
            with patch('hall_panel.time.monotonic', return_value=100.0):
                panel.handle_line('HALL,STATE,ENABLED,1,ARMED,1,MASK,0x01')
            with patch('hall_panel.time.monotonic', return_value=104.0):
                panel.poll()
            self.assertIn('Hall状态已超时，是否启用未知', panel.sensor_state.get())
            self.assertEqual(panel.port.packets, [])

    def test_disconnect_clears_current_diagnostic_snapshot(self):
        with self.hall_application() as (app, panel):
            panel.handle_line('HALL,STATE,ENABLED,1,ARMED,1,MASK,0x01')
            panel.handle_line('HALL,1,RAW,1809,BASE,1808,THRESHOLD,1596,VALID,1,EVENTS,4,REJECTED,0,ERRORS,0')
            panel.close()
            self.assertEqual(panel.diagnostic_status, {})
            self.assertEqual(panel.readings.item('1', 'values')[1:], ('-',) * 11)
            self.assertIn('ADC：未知', panel.sensor_state.get())
            report = panel.diagnostic_text().split('最近日志')[0]
            self.assertIn('HALL,1: 未收到', report)
            self.assertNotIn('EVENTS,4', report)

    def test_snapshot_capability_is_distinct_from_trigger_override(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.handle_line('PONG,R15-HALL-v3.4.3')
            panel.handle_line('FPGA,ONLINE,ACK,1,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2,SNAPSHOT_CAP,0')
            self.assertTrue(panel.fpga_capable)
            self.assertFalse(panel.snapshot_capable)
            self.assertIn('并发修复需配套新位流', panel.snapshot_state.get())
            panel.pick(6)
            self.assertEqual(panel.port.packets[-1], b'FPGA,PICK,6,100\n')
            panel.handle_line('FPGA,ONLINE,ACK,2,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2,SNAPSHOT_CAP,1')
            self.assertTrue(panel.snapshot_capable)
            self.assertIn('事件快照绑定可用', panel.snapshot_state.get())

    def test_v3_4_4_diagnostics_preserved_across_regular_rows_and_copied(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.handle_line('PONG,R15-HALL-v3.4.4')
            self.assertTrue(panel.compatible)
            diagnostic = 'HALLDIAG,1,CAL,OK,STATE,WAIT_CENTER,CAL_MIN,1429,CAL_MAX,1836,NOISE,4,RAW_PEAK,169,FILTERED_PEAK,169'
            panel.handle_line(diagnostic)
            panel.handle_line('HALL,1,RAW,1600,BASE,1431,THRESHOLD,32,VALID,1,EVENTS,1,REJECTED,0,ERRORS,0')
            self.assertEqual(panel.readings.set('1', 'quality'), '正常')
            self.assertEqual(panel.readings.set('1', 'detector'), '等待回中')
            self.assertEqual(panel.readings.set('1', 'peak'), '169')
            self.assertIn(diagnostic, panel.diagnostic_text())
            self.assertNotIn('HALLDIAG,1', panel.messages.get('1.0', 'end'))
            self.assertEqual(panel.port.packets, [b'HALL,STATUS\nFPGA,STATUS\n'])
            panel.close()
            self.assertEqual(panel.readings.set('1', 'peak'), '-')

    def test_noisy_calibration_explicitly_blocks_channel_in_display(self):
        with self.hall_application() as (app, panel):
            panel.handle_line('HALLDIAG,2,CAL,NOISY,STATE,INVALID,CAL_MIN,1300,CAL_MAX,1700,NOISE,400,RAW_PEAK,200,FILTERED_PEAK,200')
            self.assertEqual(panel.readings.set('2', 'quality'), '噪声过大')
            self.assertEqual(panel.readings.set('2', 'detector'), '禁止触发')

    def test_missing_offline_or_stale_snapshot_status_is_unknown(self):
        with self.hall_application() as (app, panel):
            panel.port = MemoryPort()
            panel.handle_line('PONG,R15-HALL-v3.4.3')
            panel.handle_line('FPGA,ONLINE,ACK,1,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2')
            self.assertIsNone(panel.snapshot_capable)
            panel.handle_line('FPGA,OFFLINE,ACK,2,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2,SNAPSHOT_CAP,1')
            self.assertIsNone(panel.snapshot_capable)
            with patch('hall_panel.time.monotonic', return_value=100.0):
                panel.handle_line('FPGA,ONLINE,ACK,3,MODE,PICK,FRETS,0,0,0,0,0,0,TRIGGER_CAP,1,OVERRIDE,2,SNAPSHOT_CAP,1')
            with patch('hall_panel.time.monotonic', return_value=104.0):
                panel.poll()
            self.assertIsNone(panel.snapshot_capable)
            self.assertIn('状态已超时', panel.snapshot_state.get())


if __name__ == '__main__':
    unittest.main()
