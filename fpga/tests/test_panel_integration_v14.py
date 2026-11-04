import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT.parent / 'ensemble_daw_v10'
WORKSPACE = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from backend_ddr_split_v9 import EXPECTED, validate_tcl


class IntegrationTests(unittest.TestCase):
    def test_v10_accepted_source_and_bitstream_remain_untouched(self):
        proof = json.loads((BASELINE / 'tests/results/physical_v10/proof.json').read_text())
        self.assertTrue(proof['passed'])
        self.assertEqual(proof['returncode'], 0)
        for name, value in proof['sources'].items():
            self.assertEqual(hashlib.sha256((BASELINE / name).read_bytes()).hexdigest(), value, name)
        bitstream = proof['generated_bitstream']
        self.assertEqual(hashlib.sha256((BASELINE / bitstream['path']).read_bytes()).hexdigest(), bitstream['sha256'])

    def test_current_v10_flash_was_verified_before_new_build(self):
        latest = json.loads((WORKSPACE / 'release_tools/current_20261024/latest_flash.json').read_text())
        proof = json.loads(Path(latest['proof']).read_text())
        self.assertTrue(latest['passed'] and proof['passed'])
        self.assertTrue(proof['flash_program_and_verify'] and proof['independent_flash_verify'])
        self.assertEqual(proof['flash_reload_usercode'], '0x00001054')

    def test_timing_fir_and_compressed_memories_are_preserved(self):
        for name in ('src/poly32/guitar_voice_tdm_core.v',
                     'src/poly32/poly32_context_ram.v',
                     'src/piano/drawn_table_ram_pages.v', 'src/ensemble_mixer.v',
                     'src/guitar_uart_trigger.v', 'src/s3_control_ingress.v'):
            self.assertEqual((ROOT / name).read_bytes(), (BASELINE / name).read_bytes(), name)

    def test_v13_frozen_sources_are_preserved_and_only_drum_synth_changes(self):
        receipt = json.loads((ROOT / 'docs/v14_baseline.json').read_text())
        baseline = Path(receipt['baseline'])
        for name, expected in receipt['baseline_sources'].items():
            self.assertEqual(hashlib.sha256((baseline / name).read_bytes()).hexdigest(), expected, name)
        changed = set()
        for directory in ('src', 'constraints', 'ip', 'violin_r15'):
            for path in (baseline / directory).rglob('*'):
                if path.is_file() and path.suffix in ('.v', '.vh', '.hex', '.sdc', '.cst', '.vo'):
                    name = path.relative_to(baseline).as_posix()
                    if (ROOT / name).read_bytes() != path.read_bytes():
                        changed.add(name)
        self.assertEqual(changed, {'src/drums/drum_synth.v'})

    def test_original_clocks_ddr_ip_and_sd_banks_are_preserved(self):
        self.assertEqual((ROOT / 'constraints/audio.sdc').read_bytes(), (BASELINE / 'constraints/audio.sdc').read_bytes())
        for directory in ('ip', 'sd_card'):
            for path in (BASELINE / directory).rglob('*'):
                if path.is_file():
                    self.assertEqual((ROOT / path.relative_to(BASELINE)).read_bytes(), path.read_bytes())

    def test_pin_changes_only_replace_pa_enable_with_eight_rotary_inputs(self):
        def pins(path):
            return dict(re.findall(r'IO_LOC\s+"([^"]+)"\s+(\w+)\s*;', path.read_text()))
        baseline = pins(BASELINE / 'constraints/audio.cst')
        expected = {**baseline}
        self.assertEqual(expected.pop('PA_EN'), 'Y25')
        expected.update(sw1_enc_a='AB25', sw1_enc_b='AB26', sw2_enc_a='P23', sw2_enc_b='P24',
                        sw1_up_n='AA25', sw1_right_n='AA24', sw1_down_n='Y26', sw1_left_n='Y25')
        actual = pins(ROOT / 'constraints/audio.cst')
        self.assertEqual(actual, expected)
        self.assertEqual(len(set(actual.values())), len(actual))
        self.assertEqual(len(actual), 101)

    def test_project_adds_only_panel_modules_and_resolves_sources(self):
        pattern = r'<File path="([^"\n]+)"'
        previous = set(re.findall(pattern, (BASELINE / 'guitar_audio_low_speed.gprj').read_text()))
        current = set(re.findall(pattern, (ROOT / 'guitar_audio_low_speed.gprj').read_text()))
        self.assertEqual(current - previous, {'src/panel_inputs.v', 'src/panel_controller.v',
                                              'src/panel_pitch.v', 'src/panel_raster.v'})
        self.assertFalse(previous - current)
        self.assertTrue(all((ROOT / name).is_file() for name in current))

    def test_backend_is_timing_driven_nonincremental_place_two_route_two(self):
        self.assertEqual(validate_tcl((ROOT / 'build_panel_v14.tcl').read_text()), EXPECTED)

    def test_panel_does_not_remove_daw_or_add_unguarded_touch_notes(self):
        code = (ROOT / 'src/guitar_audio_top.v').read_text()
        self.assertIn('.selected(timbre_violin||ensemble_mode)', code)
        self.assertIn('.hall_valid(s3_hall_valid&&!ensemble_mode)', code)
        self.assertIn('.command_valid(panel_command_valid||(!ensemble_mode&&', code)
        self.assertIn("assign panel_values[248+:8]={7'd0,ensemble_mode}", code)
        self.assertIn('ensemble_capabilities', code)
        host = (ROOT / 'violin_r15/host_controller.py').read_text()
        self.assertIn('ArrangementPanel(self)', host)
        self.assertIn('arrangement.on_disconnect()', host)

    def test_panel_drawn_pitch_keeps_the_paged_ram_interface(self):
        code = (ROOT / 'src/piano/drawn_synth16.v').read_text()
        self.assertIn('drawn_table_ram_pages u_table', code)
        self.assertNotIn('memory[0:12287]', code)
        self.assertIn('panel_step_product', code)
        self.assertLess(len(code), 12000)

    def test_touch_hall_filtering_and_sensor_calibration_are_not_replaced(self):
        original = WORKSPACE / 'esp32S3/Guitar_Controller_R15'
        for name in ('cy8cmbr3116.c', 'hall_adc.c', 'hall_detector.c', 'touch_filter.h',
                     'touch_serial.c', 'touch_output.c', 'touch_recovery.h'):
            self.assertEqual((ROOT / 'esp32S3/Guitar_Controller_R15/main' / name).read_bytes(),
                             (original / 'main' / name).read_bytes(), name)


    def test_drum_decimal_literals_are_not_adjacent_to_ternary_question_marks(self):
        code = (ROOT / 'src/drums/drum_synth.v').read_text()
        self.assertIsNone(re.search(r"\b\d+'s?d[\d_]+\?", code))


if __name__ == '__main__':
    unittest.main(verbosity=2)

