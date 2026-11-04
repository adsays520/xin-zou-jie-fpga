import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parents[1]
BACKUP = WORKSPACE / 'output/pre_hall_v3_4_5_20261021'
HOST = WORKSPACE / 'drum_bass_pitch_20261013/violin_r15'
FPGA = WORKSPACE / 'drum_bass_pitch_20261013/ensemble_hall_v7'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for entry in json.loads((BACKUP / 'sha256.json').read_text(encoding='utf-8-sig')):
        assert digest(BACKUP / entry['path']) == entry['sha256'], entry['path']
    allowed = {'fpga_link.c', 'fpga_link.h', 'hall_adc.c', 'Kconfig.projbuild', 'main.c', 'host_usb.c'}
    actual = {source.name for source in (PROJECT / 'main').iterdir() if source.is_file()
              and digest(source) != digest(BACKUP / 'main' / source.name)}
    assert actual == allowed, actual
    for name in ('CMakeLists.txt', 'sdkconfig', 'sdkconfig.defaults'):
        assert digest(PROJECT / name) == digest(BACKUP / name), name
    assert digest(PROJECT / 'build_r15/Guitar_Controller_S3_R15.bin') == digest(BACKUP / 'Guitar_Controller_S3_R15.bin')
    for logfile, count in ((PROJECT / 'tests/hall_v3_4_5_runtime.log', 93),
                           (HOST / 'test_results/hall_v3_4_5_host.log', 26)):
        output = logfile.read_text(encoding='utf-8-sig')
        assert f'Ran {count} tests' in output and '\nOK\n' in output, logfile
    binary_path = PROJECT / 'build_hall_v3_4_5/Guitar_Controller_S3_R15.bin'
    binary = binary_path.read_bytes()
    for marker in (b'R15-HALL-v3.4.5', b'STRUM H1', b'FPGA,STRUM', b'HALLDIAG', b'SNAPSHOT_CAP', b'/dev/secondary'):
        assert marker in binary, marker
    assert 'Project build complete' in (PROJECT / 'build_hall_v3_4_5.log').read_text(encoding='utf-8-sig')
    sources = {}
    for source in (PROJECT / 'main').iterdir():
        if source.is_file():
            assert source.stat().st_mtime_ns <= binary_path.stat().st_mtime_ns, source
            sources[str(source.relative_to(PROJECT))] = digest(source)
    for name in ('CMakeLists.txt', 'sdkconfig', 'sdkconfig.defaults'):
        sources[name] = digest(PROJECT / name)
    proof = json.loads((FPGA / 'tests/results/routing_v7_build/proof.json').read_text(encoding='utf-8-sig'))
    assert proof['passed'] and proof['returncode'] == 0 and proof['sources_unchanged']
    for name, expected in proof['sources'].items():
        assert digest(FPGA / name) == expected, name
    bitstream = FPGA / 'impl/pnr/ensemble_hall_piano_v7.fs'
    assert digest(bitstream) == proof['bitstream_sha256'] == '1cce15f15b4101068c2926d063a9b5be0ff0e8051110b243cf78b7ecdc61a8cc'
    report = {
        'version': 'R15-HALL-v3.4.5',
        'passed': True,
        'application_path': str(binary_path),
        'application_size': len(binary),
        'application_sha256': digest(binary_path),
        'native_tests_passed': 93,
        'host_tests_passed': 26,
        'sources': sources,
        'host_source_sha256': digest(HOST / 'hall_panel.py'),
        'mapping': {'H1': [6, 5, 4, 3, 2, 1], 'H2': 6, 'H3': 5, 'H4': 4, 'H5': 3, 'H6': 2, 'H7': 1},
        'strum_interval_ms_after_ACK': 8,
        'strum_snapshot': 'one enqueue-time touch snapshot and velocity for all six strings',
        'strum_admission': 'one queue item per complete sweep, reject whole job if full',
        'detector_touch_CY8_protocol_and_SDK_unchanged': True,
        'FPGA_inputs_verified': len(proof['sources']),
        'FPGA_bitstream_unchanged_sha256': digest(bitstream),
        'FPGA_written': False,
        'S3_written': False,
        'physical_hall_or_audio_tested': False,
    }
    (PROJECT / 'tests/hall_v3_4_5_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
