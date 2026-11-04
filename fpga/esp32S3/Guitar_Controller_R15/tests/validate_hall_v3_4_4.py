import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parents[1]
HOST = WORKSPACE / 'drum_bass_pitch_20261013/violin_r15'
BEFORE = WORKSPACE / 'output/pre_hall_v3_4_4_20261020'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for entry in json.loads((BEFORE / 'sha256.json').read_text(encoding='utf-8-sig')):
        assert digest(BEFORE / entry['path']) == entry['sha256'], entry['path']
    modified = {'hall_detector.c', 'hall_detector.h', 'hall_adc.c', 'main.c', 'host_usb.c'}
    for source in (PROJECT / 'main').iterdir():
        if source.is_file() and source.name not in modified:
            assert digest(source) == digest(BEFORE / 'main' / source.name), source
    for name in ('CMakeLists.txt', 'sdkconfig', 'sdkconfig.defaults'):
        assert digest(PROJECT / name) == digest(BEFORE / name), name
    for logfile, count in ((PROJECT / 'tests/hall_v3_4_4_runtime.log', 83),
                           (HOST / 'test_results/hall_v3_4_4_host.log', 24)):
        output = logfile.read_text(encoding='utf-8-sig')
        assert f'Ran {count} tests' in output and '\nOK\n' in output, output
    binary_path = PROJECT / 'build_r15/Guitar_Controller_S3_R15.bin'
    binary = binary_path.read_bytes()
    for marker in (b'R15-HALL-v3.4.4', b'HALLDIAG', b'FILTERED_PEAK', b'WAIT_CENTER',
                   b'UNREACHABLE', b'SNAPSHOT_CAP', b'CTRL_QUEUE', b'PICK_QUEUE', b'/dev/secondary'):
        assert marker in binary, marker
    assert 'Project build complete' in (PROJECT / 'build_hall_v3_4_4.log').read_text(encoding='utf-8-sig')
    sources = {}
    for source in (PROJECT / 'main').iterdir():
        if source.is_file():
            assert source.stat().st_mtime <= binary_path.stat().st_mtime, source
            sources[str(source.relative_to(PROJECT))] = digest(source)
    for name in ('CMakeLists.txt', 'sdkconfig', 'sdkconfig.defaults'):
        sources[name] = digest(PROJECT / name)
    fpga = WORKSPACE / 'drum_bass_pitch_20261013/impl/pnr/guitar_audio_hall_timing_v3.fs'
    assert digest(fpga) == '967faad6f191e14cb72d2cc6be3b54a3482cb1a3a561b2986bee49fe0bbf4efc'
    report = {
        'version': 'R15-HALL-v3.4.4', 'application_size': len(binary),
        'application_sha256': digest(binary_path), 'tests_passed': 83, 'host_tests_passed': 24,
        'sources': sources, 'host_source_sha256': digest(HOST / 'hall_panel.py'),
        'robust_calibration': '128 samples, median center, P90-P10 span * 3 + 8, minimum 32',
        'noisy_calibration': 'reject above 128, never clamp to claim valid',
        'trigger_confirmation': 'median of 3, 3 consecutive same-direction crossings, 4ms peak',
        'release': '35ms deadtime, 3 consecutive centered samples, 75 percent threshold',
        'SPI_scheduler_touch_and_CY8_unchanged': True, 'SDK_configuration_unchanged': True,
        'FPGA_file_unchanged_sha256': digest(fpga), 'flashed': False,
        'physical_hall_tested': False,
    }
    (PROJECT / 'tests/hall_v3_4_4_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
