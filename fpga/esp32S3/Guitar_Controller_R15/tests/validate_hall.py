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
    (PROJECT / 'tests/hall_v3_4_2_runtime.log').write_text(output, encoding='utf-8')
    assert result.returncode == 0 and 'Ran 62 tests' in output, output
    binary_path = PROJECT / 'build_r15/Guitar_Controller_S3_R15.bin'
    binary = binary_path.read_bytes()
    for marker in (b'R15-HALL-v3.4.2', b'READ_DISAGREE', b'NOTE_ACK', b'HALL,MASK,DISARMED', b'/dev/secondary'):
        assert marker in binary, marker
    config = (PROJECT / 'build_r15/config/sdkconfig.h').read_text(encoding='utf-8')
    assert '#define CONFIG_HALL_ADC_ENABLE 1' in config
    assert '#define CONFIG_HALL_ACTIVE_MASK 0x3f' in config
    assert '#define CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG 1' in config
    assert 'Project build complete' in (PROJECT / 'build_hall_v3_4_2_console.log').read_text(encoding='utf-8-sig')
    sources = {}
    for source in (PROJECT / 'main').iterdir():
        if source.is_file():
            assert source.stat().st_mtime <= binary_path.stat().st_mtime, source
            sources[str(source.relative_to(PROJECT))] = digest(source)
    for name in ('CMakeLists.txt', 'sdkconfig', 'sdkconfig.defaults'):
        sources[name] = digest(PROJECT / name)
    before = WORKSPACE / 'output/pre_hall_20261020_015142/s3/main'
    for name in ('cy8cmbr3116.c', 'touch_filter.h', 'touch_recovery.h', 'note_trace.c', 'touch_output.c'):
        assert digest(PROJECT / 'main' / name) == digest(before / name), name
    old_polling = (before / 'touch_serial.c').read_text(encoding='utf-8')
    polling = (PROJECT / 'main/touch_serial.c').read_text(encoding='utf-8')
    assert polling.replace('    TOUCH_LOGI("HOST_REPLY", "%s", line);\n', '') == old_polling
    manifest = PROJECT.parent / 'CY8_Performance_Config/profiles/source_hashes.json'
    for entry in json.loads(manifest.read_text(encoding='utf-8')):
        assert digest(Path(entry['source'])) == entry['sha256']
    report = {'version': 'R15-HALL-v3.4.2', 'application_size': len(binary),
              'application_sha256': digest(binary_path), 'tests_passed': 62,
              'USB_control_path': '/dev/secondary',
              'hall_adc_enabled': True, 'hall_boot_disarmed': True,
              'default_channel_mask': '0x3f', 'touch_guard_and_recovery_unchanged': True,
              'D_original_HEX_unchanged': 32, 'sources': sources,
              'flashed': False, 'physical_hall_tested': False,
              'requires_matching_timing_passed_FPGA_for_software_mode': True}
    (PROJECT / 'tests/hall_v3_4_2_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({name: value for name, value in report.items() if name != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
