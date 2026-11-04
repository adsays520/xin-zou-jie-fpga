from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
S3 = PROJECT.parent / 'esp32S3/Guitar_Controller_R15'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_report(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify_sources(sources, root):
    for source, expected in sources.items():
        assert digest(root / source) == expected, source


def main():
    suites = {'touch_hall_link_proof.json': 1, 'touch_hall_backpressure_proof.json': 4,
              'esp_hall_wire_proof.json': 1, 'hall_integration_proof.json': 7, 'integration_proof.json': 7}
    for name, count in suites.items():
        proof = read_report(ROOT / 'test_results' / name)
        assert len(proof) == count, name
        for sources in proof.values():
            verify_sources(sources, PROJECT)
    firmware = read_report(S3 / 'tests/hall_v3_4_3_validation.json')
    verify_sources(firmware['sources'], S3)
    assert firmware['tests_passed'] == 73
    assert digest(S3 / 'build_r15/Guitar_Controller_S3_R15.bin') == firmware['application_sha256']
    host_log = ROOT / 'test_results/hall_link_v2_host_tests.log'
    assert 'Ran 22 tests' in host_log.read_text(encoding='utf-8') and '\nOK\n' in host_log.read_text(encoding='utf-8')
    for name in ('hall_panel.py', 'test_ui.py', 'test_host.py'):
        assert (ROOT / name).stat().st_mtime <= host_log.stat().st_mtime, name
    build = read_report(PROJECT / 'tests/results/hall_link_v2_build/proof.json')
    verify_sources(build['sources'], PROJECT)
    before = read_report(PROJECT / 'tests/results/hall_v1_build/proof.json')['sources']
    changed = {source.replace('\\', '/') for source in before.keys() & build['sources'].keys()
               if before[source] != build['sources'][source]}
    assert changed == {'violin_r15/s3_spi_link.v', 'violin_r15/touch_to_command.v',
                       'violin_r15/touch_legacy.v', 'violin_r15/violin_touch_control.v', 'violin_r15/audio_core.v'}, changed
    original_bitstream = PROJECT / 'impl/pnr/guitar_audio_violin_r15.fs'
    assert digest(original_bitstream) == '1a49ce5607587b424eac213ca2431a6275da32fa9a36d7c545afe35424d21782'
    report = {'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'functional_validation_passed': True, 'firmware_version': firmware['version'],
              'firmware_sha256': firmware['application_sha256'], 'S3_tests': 73, 'host_tests': 22,
              'FPGA_suites': suites, 'changed_FPGA_modules': sorted(changed),
              'clock_pin_DDR_constraints_and_other_audio_sources_unchanged': True,
              'original_timing_passed_bitstream_unchanged': True,
              'FPGA_build_accepted': build['passed'],
              'timing_status': 'passed' if build['passed'] else 'failed' if build.get('finished') else 'not_finished',
              'FPGA_flashed': False, 'S3_flashed': False, 'physical_Hall_or_audio_verified': False}
    (ROOT / 'test_results/hall_link_v2_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
