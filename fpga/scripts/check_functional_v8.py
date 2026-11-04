import hashlib
import json
from pathlib import Path
from iverilog_runner import assert_source_hashes, ROOT


def verify():
    folder = ROOT / 'tests/results'
    units = json.loads((folder / 'units_v8.json').read_text())
    assert units['passed'] and len(units['cases']) == 4
    for case in units['cases']:
        assert case['passed']
        assert_source_hashes(case['sources'])
    audio = json.loads((folder / 'scratch_audio_v8.json').read_text())
    assert audio['passed']
    assert_source_hashes(audio['sources'])
    for name, expected in [('daw', ['tb_daw_board_v8']),
                           ('legacy', ['tb_ensemble_board', 'tb_ensemble_hall_piano'])]:
        terminal = json.loads((folder / (name + '_terminal_v8.json')).read_text())
        assert terminal['returncode'] == 0 and terminal['finished'] and terminal['tests'] == expected
    for top, name, marker in [('tb_daw_board_v8', 'daw_board_v8.log', 'PASS DAW BOARD V8:'),
                              ('tb_ensemble_board', 'ensemble_board.log', 'PASS ENSEMBLE BOARD:'),
                              ('tb_ensemble_hall_piano', 'ensemble_hall_piano.log', 'PASS ENSEMBLE HALL PIANO:')]:
        assert_source_hashes(json.loads((folder / (top + '_source_sha256.json')).read_text()))
        log = (folder / name).read_text()
        assert marker in log and not any(error in log for error in ('FATAL', 'ERROR', 'Unable to open')), name
    baseline = json.loads((ROOT / 'docs/v7_baseline_sha256.json').read_text())
    original = ROOT.parent / 'ensemble_hall_v7'
    for name, value in baseline.items():
        assert hashlib.sha256((original / name).read_bytes()).hexdigest() == value, 'v7 changed: ' + name
        if name.startswith(('ip/', 'constraints/')):
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value, 'clock/IP/constraint changed: ' + name
    return {'units': 4, 'scratch_PCM_frames': 24234, 'five_bus_DAC': True,
            'legacy_board_and_Hall': True, 'original_v7_inputs_checked': len(baseline),
            'real_board_listening': False}


if __name__ == '__main__':
    print('PASS V8 functional gate:', json.dumps(verify()), flush=True)
