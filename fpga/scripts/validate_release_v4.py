from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import zlib

from build_hall_piano_v4 import ROOT, BEFORE, verify_baseline
from finalize_pnr_v4 import OUTPUT, input_hashes
from iverilog_runner import assert_source_hashes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_s3_source():
    base = ROOT / 'esp32_ref/current_hall_v3_4_4'
    project = base / 'source/esp32S3/Guitar_Controller_R15'
    frozen = json.loads((base / 'validation/hall_v3_4_4_validation.json').read_text(encoding='utf-8'))
    for name, expected in frozen['sources'].items():
        assert digest(project / name) == expected, name
    entries = json.loads((base / 'source_sha256.json').read_text(encoding='utf-8-sig'))
    for entry in entries:
        assert digest(base / 'source' / entry['path']) == entry['sha256'], entry['path']
    vectors = json.loads((ROOT / 'tests/results/esp_hall_wire_vectors.json').read_text(encoding='utf-8'))
    assert vectors['actual_ESP_C_task_executed'] and vectors['transfers'] == 10
    for name, expected in vectors['sources'].items():
        assert digest(project / name) == expected, name
    wire = bytes(int(value, 16) for value in (ROOT / 'tests/results/esp_hall_wire_vectors.hex').read_text().split())
    assert hashlib.sha256(wire).hexdigest() == vectors['wire_sha256']
    native = (ROOT / 'tests/results/paired_s3_runtime.log').read_text(encoding='utf-8')
    assert re.search(r'Ran 83 tests[\s\S]*\bOK\b', native)
    compiled = json.loads((ROOT / 'tests/results/paired_s3_build_validation.json').read_text(encoding='utf-8'))
    assert compiled['passed'] and compiled['source_files_verified'] == len(entries)
    assert compiled['source_manifest_sha256'] == digest(base / 'source_sha256.json')
    assert compiled['build_log_sha256'] == digest(ROOT / 'tests/results/paired_s3_build.log')
    assert compiled['configuration_values_identical'] and compiled['partition_table_identical']
    assert compiled['already_flashed_application_sha256'] == digest(base / 'firmware/Guitar_Controller_S3_R15.bin')
    return len(entries)


def read_timing():
    base = ROOT / 'impl/pnr/ensemble_hall_piano_v4'
    content = Path(str(base) + '_tr_content.html').read_text(encoding='utf-8', errors='replace')
    result = {}
    for kind, following in (('Setup', 'Hold_Slack_Table'), ('Hold', 'Recovery_Slack_Table'),
                            ('Recovery', 'Removal_Slack_Table'), ('Removal', 'MIN_PULSE_WIDTH_TABLE')):
        section = content.split('name="' + kind + '_Slack_Table"', 1)[1].split('name="' + following + '"', 1)[0]
        values = [float(value) for value in re.findall(r'<tr[^>]*>\s*<td>\d+</td>\s*<td>([-\d.]+)</td>', section)]
        assert values and min(values) >= 0, (kind, values)
        result[kind.lower() + '_worst_slack_ns'] = min(values)
    section = content.split('name="MIN_PULSE_WIDTH_TABLE"', 1)[1].split('</table>', 1)[0]
    pulses = [float(value) for value in re.findall(r'<tr[^>]*>\s*<td>\d+</td>\s*<td>([-\d.]+)</td>', section)]
    assert pulses and min(pulses) >= 0
    result['minimum_pulse_slack_ns'] = min(pulses)
    for clock, frequency in (('sys_clk', 50), ('ddr_user100', 100), ('mem400', 400), ('ddr_ref100', 100)):
        match = re.search('<td>' + clock + r'</td>\s*<td>' + f'{frequency:.3f}' +
                          r'\(MHz\)</td>\s*<td[^>]*>([\d.]+)\(MHz\)</td>', content)
        assert match and float(match[1]) >= frequency, clock
        result[clock + '_fmax_mhz'] = float(match[1])
    resources = {}
    resource_text = Path(str(base) + '.rpt.txt').read_text(encoding='utf-8', errors='replace')
    for name in ('BSRAM', 'DSP', 'Register', 'Logic'):
        match = re.search(r'\b' + name + r'\s*\|\s*([\d.]+)/([\d.]+)', resource_text)
        assert match and float(match[1]) <= float(match[2]), name
        resources[name] = {'used': float(match[1]), 'available': float(match[2])}
    command = (ROOT / 'impl/pnr/cmd.do').read_text(encoding='utf-8-sig')
    assert re.search(r'^-place_option 2$', command, re.M) and re.search(r'^-route_option 1$', command, re.M)
    assert re.search(r'^-timing$', command, re.M)
    return result, resources


def main():
    original_manifest = json.loads((BEFORE / 'SHA256清单.json').read_text(encoding='utf-8-sig'))
    for name, expected in original_manifest.items():
        assert digest(BEFORE / name) == expected, name
    build = json.loads((OUTPUT / 'proof.json').read_text(encoding='utf-8'))
    assert build['passed'] and build['sources'] == input_hashes(build.get('input_mode', 'resume1'))
    assert build['place_option'] == 2 and build['route_option'] == 1
    assert verify_baseline() == build['baseline_unchanged_files_checked']
    host = json.loads((ROOT / 'tests/results/host_source_validation.json').read_text(encoding='utf-8'))
    assert host['passed'] and host['tests'] == 118
    assert_source_hashes(host['sources'])
    sd = json.loads((ROOT / 'tests/results/sd_boot_summary.json').read_text())
    assert sd['cases'] == 8 and len(sd['results']) == 8
    piano = json.loads((ROOT / 'tests/results/piano_sms_result.json').read_text())
    assert piano['passed'] and len(piano['records']) == 9
    for record in piano['records']:
        assert record['integer_frames'] == 2048 and record['stereo_unity_exact']
    hall = json.loads((ROOT / 'tests/results/hall_v4_summary.json').read_text())
    assert len(hall) == 6 and all('PASS ' in output for output in hall.values())
    tops = ('tb_s3_link', 'tb_pluck_event_queue', 'tb_touch_to_command', 'tb_s3_ingress',
            'tb_s3_bulk_ingress', 'tb_violin_controls', *hall.keys(), 'tb_sd_boot',
            'tb_piano_physical', 'tb_ensemble_board', 'tb_ensemble_hall_piano',
            'tb_piano_ddr_transport', 'tb_piano_status_uart')
    for top in tops:
        evidence = ROOT / f'tests/results/{top}_source_sha256.json'
        assert_source_hashes(json.loads(evidence.read_text()))
    for logfile, marker in (('ensemble_board.log', 'PASS ENSEMBLE BOARD:'),
                            ('ensemble_hall_piano.log', 'PASS ENSEMBLE HALL PIANO:'),
                            ('piano_ddr_transport.log', 'PASS DDR transport:'),
                            ('piano_status_uart.log', 'PASS DDR status UART:')):
        output = (ROOT / 'tests/results' / logfile).read_text(encoding='utf-8')
        assert marker in output and 'FATAL' not in output and 'ERROR' not in output
    binary = (ROOT / 'sd_card/PIANOSMS.BIN').read_bytes()
    assert len(binary) == 281600 and zlib.crc32(binary) == 0x9d9a4073
    assert binary == (ROOT / 'host/assets/piano_sms_ddr.bin').read_bytes()
    preview = ROOT / 'preview/piano_sms_ddr_A0_C4_C6_C7_C8.wav'
    assert digest(preview) == digest(BEFORE / 'preview/piano_sms_ddr_A0_C4_C6_C7_C8.wav')
    bitstream = ROOT / 'impl/pnr/ensemble_hall_piano_v4.fs'
    assert digest(bitstream) == build['bitstream_sha256']
    timing, resources = read_timing()
    s3_record_path = ROOT.parents[1] / 'esp32S3/Guitar_Controller_R15/flash_records/hall_v3_4_4_20261020/flash_result.json'
    s3_record = json.loads(s3_record_path.read_text(encoding='utf-8'))
    assert s3_record['version'] == 'R15-HALL-v3.4.4' and s3_record['status'] == 'verified_usb_handshake_and_status_observed'
    assert digest(ROOT / 'esp32_ref/current_hall_v3_4_4/firmware/Guitar_Controller_S3_R15.bin') == s3_record['candidate_sha256']
    copied_record = ROOT / 'esp32_ref/current_hall_v3_4_4/validation/flash_result.json'
    assert digest(copied_record) == digest(s3_record_path)
    s3_source_files = verify_s3_source()
    report = {'validated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'passed': True, 'baseline': str(BEFORE), 'baseline_manifest_entries_verified': len(original_manifest),
              'baseline_audio_IP_constraints_and_parameters_unchanged': verify_baseline(),
              'host_tests': host['tests'], 'Hall_link_groups': len(hall), 'SD_boot_cases': sd['cases'],
              'piano_integer_reference_cases': len(piano['records']),
              'piano_RTL_preview_identical_to_requested_baseline': True,
              'piano_RTL_preview_sha256': digest(preview),
              'whole_board_and_Hall_to_DDR_piano_to_DAC': True,
              'timing': timing, 'resources': resources, 'place_option': 2, 'route_option': 1,
              'bitstream_sha256': digest(bitstream), 'bitstream_size': bitstream.stat().st_size,
              'FPGA_flashed': False, 'physical_listening_verified': False,
              'S3_version': s3_record['version'], 'S3_flashed_and_independently_verified': True,
              'paired_S3_source_files_verified': s3_source_files, 'paired_S3_native_tests': 83,
              'S3_flash_record': str(s3_record_path)}
    (ROOT / 'tests/results/release_v4_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
