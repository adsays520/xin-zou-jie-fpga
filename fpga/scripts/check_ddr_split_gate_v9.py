import json

from backend_ddr_split_v9 import TCL, validate_tcl
from check_functional_v9 import verify as verify_tested_rtl
from iverilog_runner import ROOT, assert_source_hashes


def verify():
    result = verify_tested_rtl()
    result['prior_backend_requested'] = result.pop('backend_requested')
    result['prior_backend_configuration_tests'] = result.pop('backend_configuration_tests')
    config = json.loads((ROOT / 'tests/results/physical_v9_ddr_split/configuration.json').read_text())
    assert config['passed'] and config['unit_returncode'] == 0 and config['gowin_options_returncode'] == 0
    assert_source_hashes(config['sources'])
    result['backend_requested'] = validate_tcl((ROOT / TCL).read_text())
    result['backend_configuration_tests'] = config['unit_test_count']
    result['functional_evidence_method'] = 'revalidated_current_source_hashes; no RTL changed since completed v9 regressions'
    return result


if __name__ == '__main__':
    print('PASS V9 DDR-split functional gate:', json.dumps(verify()), flush=True)
