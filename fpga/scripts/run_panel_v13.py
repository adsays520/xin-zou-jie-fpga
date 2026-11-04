from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from backend_ddr_split_v9 import EXPECTED, validate_tcl
from backend_v10 import validate_command
from iverilog_runner import assert_source_hashes
from make_sd_v7_fixture import make_image
from panel_inputs_v13 import ROOT, WORKSPACE, STEM, digest, sources
from timing_report_v10 import read_report


GOWIN = 'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe'
TCL = 'build_panel_v13.tcl'
BOARD_CASES = {'daw': ('tb_daw_board_v8', 'PASS DAW BOARD V8:'),
               'legacy': ('tb_ensemble_board', 'PASS ENSEMBLE BOARD:'),
               'hall': ('tb_ensemble_hall_piano', 'PASS ENSEMBLE HALL PIANO:')}


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def main():
    run_name = os.environ.get('PANEL_V13_RUN', 'panel_v13_build')
    assert re.fullmatch(r'panel_v13_build(?:_retry[0-9]+)?', run_name), 'Unsafe build result name'
    output = ROOT / 'tests/results' / run_name
    output.mkdir(parents=True, exist_ok=False)
    temporary = ROOT / 'tests/runtime_temp'
    temporary.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.update(PYTHONDONTWRITEBYTECODE='1', V13_PYTHON=sys.executable,
                       TMP=str(temporary), TEMP=str(temporary))
    environment['PYTHONPATH'] = os.pathsep.join(str(ROOT / name) for name in ('violin_r15', 'host', 'tools/python_deps'))
    frozen = sources()
    state = {'started': now(), 'phase': 'preflight', 'passed': False, 'sources': frozen,
             'cases': [], 'board_cases': [], 'new_FPGA_written': False, 'new_S3_written': False,
             'board_listening_verified': False}

    def save():
        (output / 'pipeline_state.json').write_text(json.dumps(state, indent=2), encoding='utf-8')

    def unchanged():
        assert frozen == sources(), 'Candidate inputs changed; stop before the next phase'

    def run(name, command, markers=(), timeout=7200, extra_environment=None):
        unchanged()
        state['phase'] = name
        save()
        started = now()
        print(name + ' started: ' + started, flush=True)
        child_environment = dict(environment)
        child_environment.update(extra_environment or {})
        path = output / (name + '.log')
        with path.open('w', encoding='utf-8') as stream:
            process = subprocess.run(command, cwd=ROOT, env=child_environment, stdout=stream,
                                     stderr=subprocess.STDOUT, timeout=timeout)
        text = path.read_text(encoding='utf-8', errors='replace')
        record = {'name': name, 'started': started, 'finished': now(), 'returncode': process.returncode,
                  'passed': process.returncode == 0 and all(marker in text for marker in markers)}
        match = re.search(r'Ran (\d+) tests?', text)
        if match:
            record['test_count'] = int(match[1])
        state['cases'].append(record)
        save()
        assert record['passed'], name + ' failed; see ' + str(path)
        unchanged()
        print(name + ' PASS: ' + record['finished'], flush=True)
        return record

    python = [sys.executable, '-B', '-X', 'utf8']
    try:
        save()
        validate_tcl((ROOT / TCL).read_text())
        run('integration_safety', python + ['-m', 'unittest', 'discover', '-s', 'tests',
                                            '-p', 'test_panel_integration_v13.py', '-v'], ('OK',), 300)
        run('host_arranger_panel', python + ['-m', 'unittest', '-v', 'test_panel_sync',
                                             'test_arrangement', 'test_ensemble_arrangement'], ('OK',), 300)
        run('ESP_native_runtime', python + ['-m', 'unittest', 'discover', '-s',
                 'esp32S3/Guitar_Controller_R15/tests', '-p', 'test_*runtime.py', '-v'], ('OK',), 300)
        run('panel_input_navigation_pitch', python + ['scripts/verify_panel_v8.py'],
            ('PASS panel inputs:', 'PASS panel pitch:', 'PASS panel controller:'), 300)
        run('v13_timing_equivalence', python + ['scripts/verify_timing_v13.py'],
            ('PASS V13 audio:', 'PASS V13 queue:', 'PASS SCRATCH V8:',
             'PASS V12 raster:', 'PASS V12 pitch:', 'PASS V12 DDR:', 'PASS V12 packed address:',
             'PASS PACKED ROAD:', 'PASS DDR transport:'), 1800)
        synthesis = run('fresh_synthesis', [GOWIN, TCL], ('V13 new synthesis finished',), 3600,
                        {'PANEL_V13_PHASE': 'synthesis'})
        netlist = ROOT / f'impl/gwsynthesis/{STEM}.vg'
        assert netlist.is_file() and netlist.stat().st_mtime >= datetime.fromisoformat(synthesis['started']).timestamp()
        state['new_synthesis'] = {'returncode': 0, 'netlist_sha256': digest(netlist),
                                  'netlist_bytes': netlist.stat().st_size, 'finished': synthesis['finished']}
        save()
        run('melodic_pitch_PCM', python + ['scripts/verify_panel_audio.py'],
            ('PASS panel piano:', 'PASS panel bass/drawn:', 'PASS panel violin:'), 3600)
        run('screen_SPI_telemetry_visuals', python + ['scripts/verify_panel_visuals_spi.py'],
            ('PASS panel',), 1800)
        run('actual_LCD_serial_frame', python + ['scripts/verify_panel_lcd.py'], ('PASS panel',), 1800)
        run('ESP_IDF_build', ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                'esp32S3/Guitar_Controller_R15/build_r15.ps1'], ('Project build complete.',), 3600)
        firmware = ROOT / 'esp32S3/Guitar_Controller_R15/build_r15/Guitar_Controller_S3_R15.bin'
        assert b'R15-HALL-v3.4.6' in firmware.read_bytes()
        state['S3_candidate'] = {'path': firmware.relative_to(ROOT).as_posix(),
                                  'sha256': digest(firmware), 'bytes': firmware.stat().st_size, 'flashed': False}
        state['phase'] = 'whole_board_regressions_concurrent'
        save()
        make_image(real_piano=True)
        jobs = []
        for name, (top, marker) in BOARD_CASES.items():
            stream = (output / (name + '_board.log')).open('w', encoding='utf-8')
            command = python + ['scripts/run_board_panel_v13.py', name]
            process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
            record = {'name': name, 'top': top, 'started': now(), 'pid': process.pid}
            jobs.append((process, stream, record, marker))
            state['board_cases'].append(record)
        save()
        deadline = time.monotonic() + 10000
        pending = list(jobs)
        while pending:
            unchanged()
            assert time.monotonic() < deadline, 'Whole-board regressions exceeded the bounded wait'
            for job in list(pending):
                process, stream, record, marker = job
                code = process.poll()
                if code is None:
                    continue
                stream.close()
                text = (output / (record['name'] + '_board.log')).read_text(encoding='utf-8', errors='replace')
                record.update(returncode=code, finished=now(),
                    passed=code == 0 and marker in text and not any(word in text for word in ('FATAL', 'ERROR', 'Unable to open')))
                save()
                assert record['passed'], record['name'] + ' board regression failed'
                binding = ROOT / 'tests/results' / (record['top'] + '_source_sha256.json')
                record['sources'] = json.loads(binding.read_text())
                assert_source_hashes(record['sources'])
                pending.remove(job)
                print(record['name'] + ' full-board PASS: ' + record['finished'], flush=True)
            save()
            if pending:
                time.sleep(10)
        unchanged()
        gate = {'passed': True, 'finished': now(), 'sources': frozen, 'cases': state['cases'],
                'board_cases': state['board_cases'], 'real_board_listening': False}
        (output / 'functional_gate.json').write_text(json.dumps(gate, indent=2), encoding='utf-8')
        from check_functional_v13 import verify
        verify()
        physical = {'started': now(), 'passed': False, 'physical_build_only': True,
                    'sources': frozen, 'backend_requested': dict(EXPECTED),
                    'new_FPGA_written': False, 'new_S3_written': False, 'board_listening_verified': False}
        proof_path = output / 'proof.json'
        proof_path.write_text(json.dumps(physical, indent=2), encoding='utf-8')
        try:
            run('new_placement_routing', [GOWIN, TCL],
                ('PASS V13 functional gate:', 'R10 Pro DDR PASS:', 'PASS minimum pulse width',
                 'V13 timing PASS: setup=0 hold=0'), 21600, {'PANEL_V13_PHASE': 'pnr'})
            command = ROOT / 'impl/pnr/cmd.do'
            raw = command.read_text()
            physical['backend_actual'] = validate_command(raw.replace(STEM + '.vg', 'ensemble_daw_v10.vg'), ROOT)
            physical['backend_command_sha256'] = digest(command)
            bitstream = ROOT / f'impl/pnr/{STEM}.fs'
            started = datetime.fromisoformat(physical['started']).timestamp()
            assert bitstream.stat().st_mtime >= started
            physical['generated_bitstream'] = {'path': bitstream.relative_to(ROOT).as_posix(),
                'sha256': digest(bitstream), 'bytes': bitstream.stat().st_size, 'accepted': False}
            report = ROOT / f'impl/pnr/{STEM}_tr_content.html'
            assert report.stat().st_mtime >= started
            physical['timing'] = read_report(report)
            physical['timing_report_sha256'] = digest(report)
            physical.update(returncode=0, sources_unchanged=frozen == sources())
            physical['passed'] = physical['sources_unchanged'] and physical['timing']['passed']
            physical['generated_bitstream']['accepted'] = physical['passed']
            assert physical['passed']
        except BaseException as error:
            physical['error'] = f'{type(error).__name__}: {error}'
            physical['returncode'] = state['cases'][-1]['returncode'] if state['cases'][-1]['name'] == 'new_placement_routing' else None
            raise
        finally:
            physical['finished'] = now()
            physical['sources_unchanged'] = frozen == sources()
            if not physical['passed']:
                log_path = output / 'new_placement_routing.log'
                text = log_path.read_text(encoding='utf-8', errors='replace') if log_path.exists() else ''
                physical['failure_kind'] = 'unrouted' if 'PR0004' in text else 'physical_or_timing_error'
                report = ROOT / f'impl/pnr/{STEM}_tr_content.html'
                if report.exists() and report.stat().st_mtime >= datetime.fromisoformat(physical['started']).timestamp():
                    try:
                        physical['timing'] = read_report(report)
                        physical['timing_report_sha256'] = digest(report)
                        if not physical['timing']['passed']:
                            physical['failure_kind'] = 'timing_failed'
                    except Exception as report_error:
                        physical['timing_parse_error'] = str(report_error)
            proof_path.write_text(json.dumps(physical, indent=2), encoding='utf-8')
        state.update(passed=True, phase='physical_build_passed_not_board_listening', finished=now(), sources_unchanged=True)
        save()
    except BaseException as error:
        state.update(phase='stopped_with_error', error=f'{type(error).__name__}: {error}',
                     finished=now(), sources_unchanged=frozen == sources())
        save()
        raise


if __name__ == '__main__':
    main()
