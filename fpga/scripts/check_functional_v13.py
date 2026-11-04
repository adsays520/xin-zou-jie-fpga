import json
import os
import re

from iverilog_runner import assert_source_hashes
from panel_inputs_v13 import ROOT, sources


def verify():
    run_name = os.environ.get('PANEL_V13_RUN', 'panel_v13_build')
    assert re.fullmatch(r'panel_v13_build(?:_retry[0-9]+)?', run_name)
    path = ROOT / 'tests/results' / run_name / 'functional_gate.json'
    proof = json.loads(path.read_text(encoding='utf-8'))
    assert proof['passed'] and proof['finished'] and proof['sources'] == sources()
    for case in proof['cases']:
        assert case['passed'] and case['returncode'] == 0 and case['finished']
    assert len(proof['board_cases']) == 3
    for case in proof['board_cases']:
        assert case['returncode'] == 0 and case['passed']
        assert_source_hashes(case['sources'])
    return {'passed': True, 'source_files': len(proof['sources']), 'whole_board_cases': 3,
            'scope': 'source_bound_models_and_RTL_not_physical_board_listening'}


if __name__ == '__main__':
    print('PASS V13 functional gate:', json.dumps(verify()), flush=True)
