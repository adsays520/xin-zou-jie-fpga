import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import tkinter as tk
from unittest.mock import patch

from host_controller import ViolinController
from hall_panel import serial, list_ports


def main():
    parser = argparse.ArgumentParser(description='Read-only live Hall GUI handshake/status probe; no mode or trigger changes')
    parser.add_argument('--port', default='COM30')
    arguments = parser.parse_args()
    devices = [port for port in list_ports.comports() if port.device == arguments.port]
    if len(devices) != 1 or devices[0].vid != 0x303a or devices[0].pid != 0x1001:
        raise RuntimeError('Select the S3 native USB port, not FPGA/FTDI/Bluetooth')
    output = Path(__file__).resolve().parent / 'test_results'
    original = tk.Tk.__init__
    def hidden_init(instance, *positional, **keywords):
        original(instance, *positional, **keywords)
        instance.withdraw()
    with patch.object(tk.Tk, '__init__', hidden_init):
        app = ViolinController()
    panel = app.hall_panel
    report = {}
    try:
        app.show_page('hall')
        port = serial.Serial(port=None, baudrate=115200, timeout=0, write_timeout=1)
        port.dtr = False
        port.rts = False
        port.port = arguments.port
        port.open()
        panel.port = port
        panel.request_handshake()
        started = time.monotonic()
        while time.monotonic() - started < 10:
            app.update()
            if panel.compatible and panel.last_fpga_status is not None and time.monotonic() - started > 2:
                break
            time.sleep(0.02)
        report = {'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
                  'port': arguments.port, 'serial_number': devices[0].serial_number,
                  'handshake': panel.compatible, 'fpga_online': panel.fpga_online,
                  'fpga_capable': panel.fpga_capable, 'effective_mode': panel.effective_mode,
                  'connection_label': panel.status.get(), 'mode_label': panel.mode.get(),
                  'hall_label': panel.sensor_state.get(), 'read_only_queries': True,
                  'mode_changed': False, 'hall_armed': False, 'notes_sent': False}
        (output / 'hall_usb_live_ui.log').write_text(panel.messages.get('1.0', 'end'), encoding='utf-8')
        (output / 'hall_usb_live_ui.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    finally:
        panel.compatible = False
        panel.close()
        app.disconnect()
        for token in app.tk.call('after', 'info'):
            app.tk.call('after', 'cancel', token)
        app.destroy()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report.get('handshake') or not report.get('fpga_online'):
        raise RuntimeError('Live GUI did not receive both S3 handshake and FPGA online status')


if __name__ == '__main__':
    main()
