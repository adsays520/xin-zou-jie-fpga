import json

from backend_v10 import EXPECTED, TCL, validate_tcl
from build_inputs_v10 import ROOT, digest
from check_functional_v8 import verify as verify_ensemble
from iverilog_runner import assert_source_hashes


def verify():
    result = verify_ensemble()
    proof = json.loads((ROOT / 'tests/results/drawn_v9.json').read_text())
    assert proof['passed'] and len(proof['cases']) == 2
    for case in proof['cases']:
        assert case['passed'] and case['returncode'] == 0
        assert_source_hashes(case['sources'])
    for label in ('excitation_math_v10', 'excitation_tdm_v10'):
        proof = json.loads((ROOT / f'tests/results/{label}.json').read_text())
        assert proof['passed'] and proof['returncode'] == 0
        assert_source_hashes(proof['sources'])
    previous = ROOT.parent / 'ensemble_daw_v9'
    manifest = ROOT / 'docs/v9_timing_failed_proof.json'
    assert manifest.read_bytes() == (previous / 'tests/results/physical_v9_ddr_split/proof.json').read_bytes()
    previous_proof = json.loads(manifest.read_text())
    assert previous_proof['finished'] and previous_proof['returncode'] == 1
    assert previous_proof['sources_unchanged'] and not previous_proof['passed']
    changed = []
    for name, value in previous_proof['sources'].items():
        assert digest(previous / name) == value, 'v9 input changed: ' + name
        if name.startswith(('src/', 'ip/', 'constraints/', 'violin_r15/')) or name.endswith('.gprj'):
            if digest(ROOT / name) != value:
                changed.append(name)
    assert changed == ['src/poly32/guitar_voice_tdm_core.v'], changed
    configuration = json.loads((ROOT / 'tests/results/configuration_v10/proof.json').read_text())
    assert configuration['passed'] and configuration['unit_returncode'] == 0
    assert configuration['gowin_options_returncode'] == 0
    assert_source_hashes(configuration['sources'])
    assert validate_tcl((ROOT / TCL).read_text()) == EXPECTED
    result.update(excitation_signed_math_cases=116807, TDM_voices=32, TDM_PCM_frames=920,
                  saved_context_bits=1007, drawn_integrated_PCM=1700,
                  drawn_actual_Gowin_memory_gate=True, RTL_changed=changed,
                  backend_requested=dict(EXPECTED), whole_board_listening=False)
    return result


if __name__ == '__main__':
    print('PASS V10 functional gate:', json.dumps(verify()), flush=True)
