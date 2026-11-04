from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from backend_ddr_split_v9 import EXPECTED, STEM, TCL, validate_command, validate_tcl


def command_fixture():
    return '\n'.join(('-d ' + str(ROOT / f'impl/gwsynthesis/{STEM}.vg'),
                      '-pn GW5AST-LV138FPG676AES', '-cst ' + str(ROOT / 'constraints/audio.cst'),
                      '-sdc ' + str(ROOT / 'constraints/audio.sdc'), '-timing', '-replicate',
                      '-place_option 2', '-route_option 2', '-clock_route_order 1',
                      '-route_maxfan 23', '-correct_hold 1', '-convert_sdp32_36_to_sdp16_18'))


class DdrBackendTests(unittest.TestCase):
    def test_tcl(self):
        self.assertEqual(validate_tcl((ROOT / TCL).read_text()), EXPECTED)

    def test_expected_actual_command(self):
        self.assertEqual(validate_command(command_fixture(), ROOT), EXPECTED)

    def test_rejects_unsplit_ddr(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace('-convert_sdp32_36_to_sdp16_18', ''), ROOT)

    def test_rejects_prior_routing_algorithm(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace('-route_option 2', '-route_option 1'), ROOT)

    def test_rejects_stale_native_netlist(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace(STEM + '.vg', 'ensemble_daw_v9.vg'), ROOT)

    def test_rejects_hold_correction_off(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace('-correct_hold 1', '-correct_hold 0'), ROOT)

    def test_rejects_incremental(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture() + '\n-inc_pnr 1', ROOT)

    def test_preserves_named_ddr_fifo_locations(self):
        content = (ROOT / 'constraints/audio.cst').read_text()
        self.assertEqual(content.count('/u_in_fifo/gowin_add_SDPB_mem0_mem0_0_'), 8)
        self.assertEqual(EXPECTED['convert_sdp32_36_to_sdp16_18'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
