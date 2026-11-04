from datetime import datetime, timezone, timedelta
import argparse
import json
import os
import subprocess
import sys
import time

from build_inputs_v10 import ROOT, sources
from iverilog_runner import assert_source_hashes


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--await-existing-tdm', action='store_true')
    arguments = parser.parse_args()
    folder = ROOT / 'tests/results/candidate_v10'
    folder.mkdir(exist_ok=False)
    state_path = folder / 'pipeline_state.json'
    frozen = sources()
    state = {'started': now(), 'phase': 'configuration', 'sources': frozen,
             'FPGA_written': False, 'S3_written': False}
    environment = dict(os.environ)
    environment['TMP'] = environment['TEMP'] = str(ROOT / 'tests/runtime_temp')

    def save():
        state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')

    def run(script, name, timeout=7400):
        assert frozen == sources(), 'Pipeline input changed'
        state['phase'] = name
        save()
        print(name + ' started: ' + now(), flush=True)
        with (folder / (name + '.log')).open('w', encoding='utf-8') as stream:
            child = subprocess.run([sys.executable, '-B', '-X', 'utf8', script], cwd=ROOT, env=environment,
                                   stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        state.setdefault('completed', []).append({'phase': name, 'returncode': child.returncode, 'finished': now()})
        save()
        assert child.returncode == 0, f'{name} exited {child.returncode}; see actual log'
        assert frozen == sources(), 'Pipeline input changed during ' + name
        print(name + ' passed: ' + now(), flush=True)

    try:
        save()
        run('scripts/verify_backend_v10.py', 'backend_configuration', 300)
        run('scripts/verify_units_v8.py', 'protocol_memory_mixer_units', 1800)
        run('scripts/verify_excitation_math_v10.py', 'excitation_math', 600)
        run('scripts/verify_scratch_audio_v8.py', 'guitar_PCM_equivalence', 1800)
        run('scripts/verify_drawn_v9.py', 'drawn_RTL_and_Gowin_memory_gate', 2200)
        state['phase'] = 'await_existing_TDM_equivalence'
        save()
        deadline = time.monotonic() + 2500
        tdm_path = ROOT / 'tests/results/excitation_tdm_v10.json'
        if not tdm_path.exists() and not arguments.await_existing_tdm:
            run('scripts/verify_excitation_tdm_v10.py', 'TDM_equivalence', 2600)
        while not tdm_path.exists():
            log_path = ROOT / 'tests/results/excitation_tdm_v10.log'
            log = log_path.read_text(errors='replace') if log_path.exists() else ''
            assert not any(marker in log for marker in ('FATAL', 'ERROR', 'Unable to open')), log[-4000:]
            assert time.monotonic() < deadline, 'Existing TDM equivalence did not finish; no physical build launched'
            time.sleep(15)
        tdm = json.loads(tdm_path.read_text())
        assert tdm['passed'] and tdm['returncode'] == 0
        assert_source_hashes(tdm['sources'])
        state.setdefault('completed', []).append({'phase': 'source_bound_TDM_equivalence', 'returncode': 0, 'finished': now()})
        save()
        run('scripts/verify_daw_board_v8.py', 'daw_regression')
        (ROOT / 'tests/results/daw_terminal_v8.json').write_text(json.dumps(
            {'finished': now(), 'returncode': 0, 'tests': ['tb_daw_board_v8']}, indent=2), encoding='utf-8')
        run('scripts/verify_ensemble_board.py', 'legacy_board')
        run('scripts/verify_ensemble_hall_piano.py', 'legacy_hall')
        (ROOT / 'tests/results/legacy_terminal_v8.json').write_text(json.dumps(
            {'finished': now(), 'returncode': 0, 'tests': ['tb_ensemble_board', 'tb_ensemble_hall_piano']}, indent=2), encoding='utf-8')
        run('scripts/check_functional_v10.py', 'functional_gate', 120)
        run('scripts/build_physical_v10.py', 'physical_build', 22000)
        state.update(phase='physical_build_passed_not_board_listening', finished=now(), sources_unchanged=frozen == sources())
        save()
    except BaseException as error:
        state.update(phase='stopped_with_error', error=f'{type(error).__name__}: {error}',
                     finished=now(), sources_unchanged=frozen == sources())
        save()
        raise


if __name__ == '__main__':
    main()
