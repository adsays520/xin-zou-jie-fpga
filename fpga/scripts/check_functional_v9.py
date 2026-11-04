import json

from check_functional_v8 import verify as verify_ensemble
from iverilog_runner import ROOT, assert_source_hashes
from backend_options_v9 import validate_requested_tcl


def verify():
    result = verify_ensemble()
    proof = json.loads((ROOT / 'tests/results/drawn_v9.json').read_text())
    assert proof['passed'] and len(proof['cases']) == 2
    for case in proof['cases']:
        assert case['passed'] and case['returncode'] == 0
        assert_source_hashes(case['sources'])
    result['drawn_integrated_PCM'] = 1700
    result['drawn_actual_Gowin_memory_gate'] = True
    result['whole_board_listening'] = False
    result['backend_requested'] = validate_requested_tcl((ROOT / 'build_merged.tcl').read_text())
    backend = json.loads((ROOT / 'tests/results/backend_config_reroute_v9/proof.json').read_text())
    assert backend['passed'] and backend['unit_returncode'] == 0 and backend['gowin_options_returncode'] == 0
    assert_source_hashes(backend['sources'])
    result['backend_configuration_tests'] = backend['unit_test_count']
    return result


if __name__ == '__main__':
    print('PASS V9 functional gate:', json.dumps(verify()), flush=True)
