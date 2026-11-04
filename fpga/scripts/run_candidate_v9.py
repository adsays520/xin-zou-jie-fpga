from datetime import datetime, timezone, timedelta
import json
import subprocess
import sys

from build_inputs_v9 import ROOT


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def main():
    folder = ROOT / 'tests/results/candidate_v9_paged'
    folder.mkdir(parents=True, exist_ok=True)
    state_path = folder / 'pipeline_state.json'
    assert not state_path.exists(), 'Preserve existing attempt'
    state = {'started': now(), 'phase': 'unit_regression', 'FPGA_written': False, 'S3_written': False}

    def save():
        state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')

    def run(script, name, timeout=7400):
        state['phase'] = name
        save()
        with (folder / (name + '.log')).open('w', encoding='utf-8') as stream:
            completed = subprocess.run([sys.executable, '-B', '-X', 'utf8', script], cwd=ROOT,
                                       stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        state.setdefault('completed', []).append({'phase': name, 'returncode': completed.returncode, 'finished': now()})
        save()
        assert completed.returncode == 0, f'{name} exited {completed.returncode}; see actual log'

    try:
        run('scripts/verify_units_v8.py', 'protocol_memory_mixer_units', timeout=1800)
        run('scripts/verify_scratch_audio_v8.py', 'guitar_PCM_equivalence', timeout=1800)
        run('scripts/verify_drawn_v9.py', 'drawn_RTL_and_Gowin_memory_gate', timeout=2200)
        run('scripts/verify_daw_board_v8.py', 'daw_regression')
        (ROOT / 'tests/results/daw_terminal_v8.json').write_text(json.dumps(
            {'finished': now(), 'returncode': 0, 'tests': ['tb_daw_board_v8']}, indent=2), encoding='utf-8')
        run('scripts/verify_ensemble_board.py', 'legacy_board')
        run('scripts/verify_ensemble_hall_piano.py', 'legacy_hall')
        (ROOT / 'tests/results/legacy_terminal_v8.json').write_text(json.dumps(
            {'finished': now(), 'returncode': 0, 'tests': ['tb_ensemble_board', 'tb_ensemble_hall_piano']}, indent=2), encoding='utf-8')
        run('scripts/check_functional_v9.py', 'functional_gate', timeout=120)
        run('scripts/build_physical_v9.py', 'physical_build', timeout=22000)
        state.update(phase='physical_build_passed_not_board_listening', finished=now())
        save()
    except BaseException as error:
        state.update(phase='stopped_with_error', error=f'{type(error).__name__}: {error}', finished=now())
        save()
        raise


if __name__ == '__main__':
    main()
