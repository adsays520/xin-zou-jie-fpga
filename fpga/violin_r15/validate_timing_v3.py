from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
WORKSPACE = PROJECT.parent
BASELINE = WORKSPACE / 'output/hall_link_v2_setup_failed_20261020_171348'
S3 = WORKSPACE / 'esp32S3/Guitar_Controller_R15'


def read_report(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources(sources, root):
    for source, expected in sources.items():
        assert digest(root / source) == expected, source


def main():
    units = read_report(ROOT / 'test_results/hall_timing_v3/proof.json')
    assert units['passed'] and len(units['suites']) == 8
    for sources in units['suites'].values():
        verify_sources(sources, PROJECT)
    counts = {'touch_hall_link_proof.json': 1, 'touch_hall_backpressure_proof.json': 4,
              'esp_hall_wire_proof.json': 1, 'integration_proof.json': 7}
    for name, count in counts.items():
        proof = read_report(ROOT / 'test_results' / name)
        assert len(proof) == count, name
        for sources in proof.values():
            verify_sources(sources, PROJECT)
    firmware = read_report(S3 / 'tests/hall_v3_4_3_validation.json')
    verify_sources(firmware['sources'], S3)
    assert firmware['tests_passed'] == 73
    assert digest(S3 / 'build_r15/Guitar_Controller_S3_R15.bin') == firmware['application_sha256']
    before = read_report(BASELINE / 'build/proof.json')['sources']
    build = read_report(PROJECT / 'tests/results/hall_timing_v3_build/proof.json')
    verify_sources(build['sources'], PROJECT)
    options = read_report(PROJECT / 'tests/results/hall_timing_v3_build/implementation_options.json')
    assert options['build_started'] == build['started']
    assert options['options'] == {'OUTPUT_BASE_NAME': 'guitar_audio_hall_timing_v3',
                                 'Place_Option': '2', 'Route_Option': '1', 'Run_Timing_Driven': True}
    changed = {source.replace('\\', '/') for source in before.keys() & build['sources'].keys()
               if before[source] != build['sources'][source]}
    assert changed == {'guitar_ddr_violin_r15.gprj', 'bram_r13/poly32.v', 'output_r12/audio_driver.v',
                       'src/drums/drum_machine.v', 'violin_r15/audio_core.v',
                       'violin_r15/master_space_fx.v', 'violin_r15/touch_legacy.v'}, changed
    added = {source.replace('\\', '/') for source in build['sources'].keys() - before.keys()}
    removed = {source.replace('\\', '/') for source in before.keys() - build['sources'].keys()}
    assert added == {'violin_r15/note_params_banked.v', 'build_hall_timing_v3.tcl'}, added
    assert removed == {'build_hall_link_v2.tcl'}, removed
    baseline_project = BASELINE / 'source/drum_bass_pitch_20261013'
    for relative in ('timing_r10c/check_timing.tcl', 'scripts/check_ddr_pulse.tcl'):
        assert digest(PROJECT / relative) == digest(baseline_project / relative), relative
    old_entries = [entry.attrib for entry in ET.parse(baseline_project / 'guitar_ddr_violin_r15.gprj').getroot().find('FileList')]
    new_entries = [entry.attrib for entry in ET.parse(PROJECT / 'guitar_ddr_violin_r15.gprj').getroot().find('FileList')]
    assert [entry for entry in new_entries if entry['path'] != 'violin_r15/note_params_banked.v'] == old_entries
    script = (PROJECT / 'build_hall_timing_v3.tcl').read_text(encoding='utf-8')
    assert script.count('set_option -place_option 2\n') == 1
    assert script.count('set_option -route_option 1\n') == 1
    normalized_script = script.replace('guitar_audio_hall_timing_v3', 'guitar_audio_hall_link_v2').replace(
        'Hall timing v3', 'Hall link v2').replace('set_option -place_option 2\n',
        'set_option -place_option 0\n').replace('set_option -route_option 1\n', 'set_option -route_option 0\n')
    assert normalized_script == (baseline_project / 'build_hall_link_v2.tcl').read_text(encoding='utf-8')
    assert digest(PROJECT / 'impl/pnr/guitar_audio_violin_r15.fs') == '1a49ce5607587b424eac213ca2431a6275da32fa9a36d7c545afe35424d21782'
    assert digest(PROJECT / 'impl/pnr/guitar_audio_hall_link_v2.fs') == '197b92a031f91de2b5a858fe1d81d1067864f7e2bf6a08fe6f05337f028ac70e'
    timing_path = PROJECT / 'tests/results/hall_timing_v3_build/timing.json'
    timing = read_report(timing_path) if timing_path.exists() else None
    accepted = bool(build['passed'] and timing and timing['passed'] and
                    timing['current_sources_match'] and timing['fresh_outputs'])
    bitstream_sha256 = None
    if accepted:
        assert build['sources_unchanged']
        bitstream_sha256 = digest(PROJECT / 'impl/pnr/guitar_audio_hall_timing_v3.fs')
        assert bitstream_sha256 == build['bitstream_sha256'] == timing['bitstream_sha256']
    result = {'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'functional_validation_passed': True, 'timing_unit_suites': 8,
              'FPGA_suites': counts, 'changed_existing_sources': sorted(changed),
              'added_sources': sorted(added), 'S3_sources_and_firmware_unchanged': True,
              'firmware_sha256': firmware['application_sha256'],
              'clocks_pins_DDR_and_acceptance_checks_unchanged': True,
              'place_option': 2, 'route_option': 1, 'timing_driven': True,
              'original_passed_and_v2_failed_bitstreams_preserved': True,
              'FPGA_build_accepted': accepted,
              'bitstream_sha256': bitstream_sha256,
              'timing_status': 'passed' if accepted else 'failed' if build.get('finished') else 'not_finished',
              'timing': timing['timing'] if timing else None,
              'FPGA_flashed': False, 'S3_flashed': False, 'physical_audio_verified': False}
    (ROOT / 'test_results/hall_timing_v3_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
