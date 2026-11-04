from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from backend_options_v9 import EXPECTED, validate_backend_command, validate_requested_tcl


def command_fixture():
    return '\n'.join((
        '-d ' + str(ROOT / 'impl/gwsynthesis/ensemble_daw_v9.vg'),
        '-pn GW5AST-LV138FPG676AES',
        '-cst ' + str(ROOT / 'constraints/audio.cst'),
        '-sdc ' + str(ROOT / 'constraints/audio.sdc'),
        '-timing', '-replicate', '-place_option 2', '-route_option 2',
        '-clock_route_order 1', '-correct_hold 1', '-route_maxfan 23',
    ))


class BackendOptionsTests(unittest.TestCase):
    def test_current_tcl(self):
        self.assertEqual(validate_requested_tcl((ROOT / 'build_merged.tcl').read_text()), EXPECTED)

    def test_expected_backend(self):
        self.assertEqual(validate_backend_command(command_fixture(), ROOT), EXPECTED)

    def test_rejects_old_routing_algorithm(self):
        with self.assertRaises(ValueError):
            validate_backend_command(command_fixture().replace('-route_option 2', '-route_option 1'), ROOT)

    def test_rejects_implicit_wide_ram_conversion(self):
        with self.assertRaises(ValueError):
            validate_backend_command(command_fixture() + '\n-convert_sdp32_36_to_sdp16_18', ROOT)

    def test_rejects_missing_timing_driven_flag(self):
        with self.assertRaises(ValueError):
            validate_backend_command(command_fixture().replace('-timing', ''), ROOT)

    def test_rejects_stale_netlist(self):
        with self.assertRaises(ValueError):
            validate_backend_command(command_fixture().replace('ensemble_daw_v9.vg', 'ensemble_daw_v8.vg'), ROOT)

    def test_rejects_wrong_clock_priority(self):
        with self.assertRaises(ValueError):
            validate_backend_command(command_fixture().replace('-clock_route_order 1', '-clock_route_order 0'), ROOT)

    def test_rejects_disabled_hold_correction(self):
        with self.assertRaises(ValueError):
            validate_backend_command(command_fixture().replace('-correct_hold 1', '-correct_hold 0'), ROOT)

    def test_rejects_conflicting_tcl_options(self):
        content = (ROOT / 'build_merged.tcl').read_text() + '\nset_option -route_option 1\n'
        with self.assertRaises(ValueError):
            validate_requested_tcl(content)

    def test_rejects_incremental_placement(self):
        with self.assertRaises(ValueError):
            validate_backend_command(command_fixture() + '\n-inc_place 1', ROOT)


if __name__ == '__main__':
    unittest.main(verbosity=2)
