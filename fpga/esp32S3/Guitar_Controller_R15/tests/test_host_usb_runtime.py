import ctypes
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UsbRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.libraries = {}
        shared = ROOT.parent.parent / 'esp32C3/Bluedroid_Connection/main'
        for mode in ('primary', 'secondary'):
            library = ROOT / f'tests/build/usb_{mode}_{os.getpid()}.dll'
            command = [os.environ.get('TOUCH_TEST_TCC', str(ROOT / 'tests/tools/tcc/tcc.exe')), '-shared', '-o', str(library),
                       '-include', str(ROOT / 'tests/include/idf_test.h'), '-I', str(ROOT / 'tests/include'),
                       '-I', str(ROOT / 'main'), '-I', str(shared)]
            if mode == 'primary':
                command.append('-DTEST_USB_PRIMARY=1')
            command.extend([str(ROOT / 'tests/usb_sim.c'), str(ROOT / 'main/control_line.c')])
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            simulator = ctypes.CDLL(str(library))
            for name in ('sim_usb_path', 'sim_usb_reply', 'sim_usb_command'):
                getattr(simulator, name).restype = ctypes.c_char_p
            cls.libraries[mode] = simulator

    def setUp(self):
        for simulator in self.libraries.values():
            simulator.sim_usb_reset()
        self.sim = self.libraries['secondary']

    def test_secondary_console_opens_registered_secondary_path(self):
        self.assertEqual(self.sim.sim_usb_start(), 0)
        self.assertEqual(self.sim.sim_usb_path(), b'/dev/secondary')
        self.assertEqual(self.sim.sim_usb_tasks(), 1)
        self.assertTrue(self.sim.sim_usb_nonblocking())
        self.assertTrue(self.sim.sim_usb_rx_ready())

    def test_primary_console_still_opens_primary_path(self):
        simulator = self.libraries['primary']
        self.assertEqual(simulator.sim_usb_start(), 0)
        self.assertEqual(simulator.sim_usb_path(), b'/dev/usbserjtag')

    def test_missing_path_cannot_report_success_or_start_rx(self):
        self.sim.sim_usb_open_failure(1)
        self.assertEqual(self.sim.sim_usb_start(), -1)
        self.assertEqual(self.sim.sim_usb_tasks(), 0)
        self.assertEqual(self.sim.sim_usb_closes(), 0)

    def test_task_failure_closes_descriptor_and_can_retry(self):
        self.sim.sim_usb_task_failure(1)
        self.assertEqual(self.sim.sim_usb_start(), 0x101)
        self.assertEqual(self.sim.sim_usb_closes(), 1)
        self.sim.sim_usb_task_failure(0)
        self.assertEqual(self.sim.sim_usb_start(), 0)

    def test_ping_returns_version_without_instrument_commands(self):
        self.sim.sim_usb_start()
        self.sim.sim_usb_line(b'PING')
        self.assertEqual(self.sim.sim_usb_reply(), b'PONG,R15-HALL-v3.4.27-BLE\r\n')
        self.assertEqual(self.sim.sim_usb_commands(), 0)

    def test_usb_dispatch_preserves_status_allowlist(self):
        self.sim.sim_usb_start()
        self.sim.sim_usb_line(b'FPGA,STATUS')
        self.assertEqual(self.sim.sim_usb_command(), b'FPGA,STATUS')
        self.sim.sim_usb_line(b'HALL,STATUS')
        self.assertEqual(self.sim.sim_usb_command(), b'HALL,STATUS')
        self.sim.sim_usb_line(b'I2C,WRITE,0x37')
        self.assertEqual(self.sim.sim_usb_commands(), 2)
        self.assertEqual(self.sim.sim_usb_reply(), b'ERROR,USB_COMMAND\r\n')
        self.sim.sim_usb_line(b'HALL,UNKNOWN')
        self.assertEqual(self.sim.sim_usb_reply(), b'ERROR,COMMAND\r\n')

    def test_secondary_console_installs_rx_and_tx_buffers(self):
        self.assertEqual(self.sim.sim_usb_start(), 0)
        self.assertEqual(self.sim.sim_usb_driver_installs(), 1)
        self.assertEqual(self.sim.sim_usb_rx_size(), 1024)
        self.assertEqual(self.sim.sim_usb_tx_size(), 4096)

    def test_readonly_touch_and_i2c_status_reach_handler(self):
        self.sim.sim_usb_start()
        for command in (b'TOUCH,STATUS', b'I2C,STATUS'):
            self.sim.sim_usb_line(command)
            self.assertEqual(self.sim.sim_usb_command(), command)
        self.assertEqual(self.sim.sim_usb_commands(), 2)

    def test_led_commands_reach_handler_without_expanding_i2c_access(self):
        self.sim.sim_usb_start()
        for command in (b'LED,STATUS', b'LED,MODE,LIVE', b'LED,ADD,0,21,6,200'):
            self.sim.sim_usb_line(command)
            self.assertEqual(self.sim.sim_usb_command(), command)
        self.assertEqual(self.sim.sim_usb_commands(), 3)

    def test_diagnostic_prefix_does_not_allow_writes_or_reset(self):
        self.sim.sim_usb_start()
        for command in (b'TOUCH,RESET', b'TOUCH,WRITE', b'I2C,WRITE,39,00,FFFF', b'I2C,RESET'):
            self.sim.sim_usb_line(command)
            self.assertEqual(self.sim.sim_usb_reply(), b'ERROR,USB_COMMAND\r\n')
        self.assertEqual(self.sim.sim_usb_commands(), 0)

    def test_existing_console_driver_is_reused_not_installed_twice(self):
        self.sim.sim_usb_existing_driver()
        self.assertEqual(self.sim.sim_usb_start(), 0)
        self.assertEqual(self.sim.sim_usb_driver_installs(), 0)
        self.assertTrue(self.sim.sim_usb_rx_ready())

    def test_driver_failure_does_not_open_path_or_spawn_rx(self):
        self.sim.sim_usb_driver_failure()
        self.assertEqual(self.sim.sim_usb_start(), 0x101)
        self.assertEqual(self.sim.sim_usb_path(), b'')
        self.assertEqual(self.sim.sim_usb_tasks(), 0)
        self.assertFalse(self.sim.sim_usb_rx_ready())


if __name__ == '__main__':
    unittest.main()
