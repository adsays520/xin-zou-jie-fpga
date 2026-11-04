import hashlib
import json
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                             str(PROJECT / 'tests'), '-p', 'test_*.py', '-v'],
                            capture_output=True, text=True, encoding='utf-8')
    output = result.stdout + result.stderr
    (PROJECT / 'tests/hall_v3_4_3_runtime.log').write_text(output, encoding='utf-8')
    assert result.returncode == 0 and 'Ran 73 tests' in output and '\nOK\n' in output, output
    binary_path = PROJECT / 'build_r15/Guitar_Controller_S3_R15.bin'
    binary = binary_path.read_bytes()
    for marker in (b'R15-HALL-v3.4.3', b'READ_DISAGREE', b'NOTE_ACK', b'HALL,MASK,DISARMED',
                   b'/dev/secondary', b'SNAPSHOT_CAP', b'CTRL_QUEUE', b'PICK_QUEUE'):
        assert marker in binary, marker
    assert 'Project build complete' in (PROJECT / 'build_hall_v3_4_3_link.log').read_text(encoding='utf-8-sig')
    before = WORKSPACE / 'output/pre_touch_hall_link_fix_20261020/s3'
    protected = ('hall_adc.c', 'hall_detector.c', 'hall_detector.h', 'cy8cmbr3116.c',
                 'touch_serial.c', 'touch_filter.h', 'touch_recovery.h', 'note_trace.c',
                 'touch_output.c', 'control_line.c', 'control_line.h')
    for name in protected:
        assert digest(PROJECT / 'main' / name) == digest(before / 'main' / name), name
    for name in ('sdkconfig', 'sdkconfig.defaults'):
        assert digest(PROJECT / name) == digest(before / name), name
    sources = {}
    for source in (PROJECT / 'main').iterdir():
        if source.is_file():
            assert source.stat().st_mtime <= binary_path.stat().st_mtime, source
            sources[str(source.relative_to(PROJECT))] = digest(source)
    for name in ('CMakeLists.txt', 'sdkconfig', 'sdkconfig.defaults'):
        sources[name] = digest(PROJECT / name)
    manifest = WORKSPACE / 'esp32S3/CY8_Performance_Config/profiles/source_hashes.json'
    originals = json.loads(manifest.read_text(encoding='utf-8'))
    for entry in originals:
        assert digest(Path(entry['source'])) == entry['sha256']
    report = {'version': 'R15-HALL-v3.4.3', 'application_size': len(binary),
              'application_sha256': digest(binary_path), 'tests_passed': 73, 'sources': sources,
              'fair_command_pick_scheduling': True, 'pending_frame_retry_unchanged': True,
              'event_snapshot_at_enqueue': True, 'Hall_FIFO_items': 32, 'Hall_item_bytes': 18,
              'hall_detection_touch_filter_and_recovery_unchanged': True,
              'D_original_HEX_unchanged': len(originals), 'flashed': False, 'physical_hall_tested': False,
              'requires_matching_FPGA_for_snapshot_binding': True}
    (PROJECT / 'tests/hall_v3_4_3_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
