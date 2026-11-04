from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from backend_v10 import EXPECTED, STEM, TCL, validate_command, validate_tcl
from timing_report_v10 import analyze, read_report


def command_fixture():
    return '\n'.join(('-d ' + str(ROOT / f'impl/gwsynthesis/{STEM}.vg'),
                      '-pn GW5AST-LV138FPG676AES', '-cst ' + str(ROOT / 'constraints/audio.cst'),
                      '-sdc ' + str(ROOT / 'constraints/audio.sdc'), '-timing', '-replicate',
                      '-place_option 2', '-route_option 2', '-clock_route_order 1',
                      '-route_maxfan 23', '-correct_hold 1', '-convert_sdp32_36_to_sdp16_18'))


class BackendTests(unittest.TestCase):
    def test_tcl(self):
        self.assertEqual(validate_tcl((ROOT / TCL).read_text()), EXPECTED)

    def test_expected_command(self):
        self.assertEqual(validate_command(command_fixture(), ROOT), EXPECTED)

    def test_rejects_unsplit_ddr(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace('-convert_sdp32_36_to_sdp16_18', ''), ROOT)

    def test_rejects_prior_routing(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace('-route_option 2', '-route_option 1'), ROOT)

    def test_rejects_stale_netlist(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace(STEM + '.vg', 'ensemble_daw_v9_ddr_split.vg'), ROOT)

    def test_rejects_hold_correction_off(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture().replace('-correct_hold 1', '-correct_hold 0'), ROOT)

    def test_rejects_incremental(self):
        with self.assertRaises(ValueError):
            validate_command(command_fixture() + '\n-inc_pnr 1', ROOT)

    def test_preserves_ddr_locations(self):
        self.assertEqual((ROOT / 'constraints/audio.cst').read_text().count(
            '/u_in_fifo/gowin_add_SDPB_mem0_mem0_0_'), 8)

    def test_passing_v7_report(self):
        report = ROOT.parent / 'ensemble_hall_v7/impl/pnr/ensemble_hall_piano_v7_tr_content.html'
        result = read_report(report)
        self.assertTrue(result['passed'])
        self.assertEqual(result['setup_violations'], 0)
        self.assertAlmostEqual(result['setup_worst_slack_ns'], 0.043)

    def test_rejects_failed_v9_report(self):
        report = ROOT.parent / 'ensemble_daw_v9/impl/pnr/ensemble_daw_v9_ddr_split_tr_content.html'
        result = read_report(report)
        self.assertFalse(result['passed'])
        self.assertEqual(result['setup_violations'], 60)
        self.assertAlmostEqual(result['setup_worst_slack_ns'], -1.300)

    def test_rejects_missing_timing(self):
        with self.assertRaises(ValueError):
            analyze('<html></html>')

    def test_rejects_changed_target(self):
        report = ROOT.parent / 'ensemble_hall_v7/impl/pnr/ensemble_hall_piano_v7_tr_content.html'
        with self.assertRaises(ValueError):
            analyze(report.read_text().replace('50.000(MHz)', '25.000(MHz)'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
