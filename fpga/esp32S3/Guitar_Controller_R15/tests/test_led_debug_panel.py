import importlib.util
from pathlib import Path
import unittest
import queue
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('led_debug_panel',Path(__file__).resolve().parents[1]/'tools/led_debug_panel.py')
panel=importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


class PanelProtocolTests(unittest.TestCase):
    def test_disconnect_restores_demo_on_new_firmware_and_off_on_legacy(self):
        class Port:
            is_open = False
            def open(self): self.is_open = True
            def close(self): self.is_open = False
        for version, expected in [('3.4.24', 'LED,MODE,DEMO'), ('3.4.21', 'LED,MODE,OFF')]:
            link = panel.Link('FAKE', queue.Queue())
            commands = []
            def transact(command):
                commands.append(command)
                return 'PONG,R15-HALL-v' + version if command == 'PING' else 'OK,LED'
            link.transact = transact
            link.closing.set()
            with patch.object(panel.serial, 'Serial', return_value=Port()):
                link.run()
            self.assertEqual(commands, ['PING', 'LED,OUTPUT,STATUS', expected])
            self.assertFalse(link.port.is_open)

    def test_rgb_order_and_brightness_are_not_reversed_on_host(self):
        self.assertEqual(panel.output_command(3,[200,100,20],50,False,1,50),
                         'LED,OUTPUT,3,100,50,10,0,0')

    def test_blink_frequency_is_a_whole_on_off_cycle(self):
        self.assertEqual(panel.output_command(7,[255,0,0],100,True,2,25),
                         'LED,OUTPUT,7,255,0,0,500,125')

    def test_fastest_and_slowest_ui_blink_have_valid_phase_lengths(self):
        self.assertTrue(panel.output_command(0,[0,0,255],10,True,10,10).endswith(',100,10'))
        self.assertTrue(panel.output_command(0,[0,0,255],10,True,.1,90).endswith(',10000,9000'))

    def test_invalid_or_non_finite_values_never_form_wire_command(self):
        cases=[(8,[0,0,0],10,True,1,50),(3,[256,0,0],10,False,1,50),
               (3,[1,2,3],101,False,1,50),(3,[1,2,3],10,True,0,50),
               (3,[1,2,3],10,True,float('nan'),50),(3,[1,2,3],10,True,1,99)]
        for args in cases:
            with self.subTest(args=args),self.assertRaises(ValueError):panel.output_command(*args)

    def test_host_reply_prefix_and_ansi_are_accepted(self):
        self.assertEqual(panel.payload('\x1b[0mI (42) HOST_REPLY: OK,LED\r\n'),'OK,LED')
        self.assertEqual(panel.payload('LED,OUTPUT,STATE,ENABLED,0\r\n'),'LED,OUTPUT,STATE,ENABLED,0')

    def test_serial_reply_survives_fragment_boundaries(self):
        class Port:
            def __init__(self):self.chunks=[b'I (42) HOST_',b'REPLY: LED,OUT',b'PUT,STATE,ENABLED,1\r',b'\n']
            @property
            def in_waiting(self):return len(self.chunks[0]) if self.chunks else 0
            def read(self,size):return self.chunks.pop(0) if self.chunks else b''
        link=panel.Link('FAKE',queue.Queue());link.port=Port()
        self.assertEqual([link.read_reply() for _ in range(3)],['','',''])
        self.assertEqual(link.read_reply(),'LED,OUTPUT,STATE,ENABLED,1')

    def test_multiple_serial_lines_are_not_lost_in_one_read(self):
        class Port:
            in_waiting=100
            def read(self,size):return b'I (1) HOST_REPLY: OK,LED\nI (2) HOST_REPLY: PONG,R15-HALL-v3.4.19\n'
        link=panel.Link('FAKE',queue.Queue());link.port=Port()
        self.assertEqual(link.read_reply(),'OK,LED')
        self.assertEqual(link.read_reply(),'PONG,R15-HALL-v3.4.19')


if __name__=='__main__':unittest.main()
