import json
import os
import re

from iverilog_runner import assert_source_hashes
from panel_inputs_v14 import ROOT, sources


def verify():
    run_name = os.environ.get('PANEL_V14_RUN', 'panel_v14_build')
    assert re.fullmatch(r'panel_v14_build(?:_retry[0-9]+)?', run_name)
    path = ROOT / 'tests/results' / run_name / 'functional_gate.json'
    proof = json.loads(path.read_text(encoding='utf-8'))
    assert proof['passed'] and proof['finished'] and proof['sources'] == sources()
    for case in proof['cases']:
        assert case['passed'] and case['returncode'] == 0 and case['finished']
    names = {case['name'] for case in proof['cases']}
    assert {'drum_audio_headroom_SD', 'drum_actual_Gowin_netlist'} <= names
    for top in ('tb_drum_audio_v14', 'tb_drum_headroom_v14', 'tb_drum_morph_v14', 'tb_drum_bank_v7', 'tb_drum_sd_v7'):
        binding = ROOT / 'tests/results' / (top + '_source_sha256.json')
        assert_source_hashes(json.loads(binding.read_text()))
    gate = json.loads((ROOT / 'tests/results/drum_sd_gate_v14_result.json').read_text())
    assert gate['passed']
    assert_source_hashes(gate['sources'])
    assert len(proof['board_cases']) == 3
    for case in proof['board_cases']:
        assert case['returncode'] == 0 and case['passed']
        assert_source_hashes(case['sources'])
    return {'passed': True, 'source_files': len(proof['sources']), 'whole_board_cases': 3,
            'scope': 'source_bound_models_and_RTL_not_physical_board_listening'}


if __name__ == '__main__':
    print('PASS V14 functional gate:', json.dumps(verify()), flush=True)

