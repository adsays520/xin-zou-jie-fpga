import json

from build_inputs_v9 import digest
from iverilog_runner import ROOT, compile_sim, simulate, source_hashes, assert_source_hashes


def main():
    baseline = ROOT.parent / 'ensemble_daw_v9'
    record = json.loads((ROOT / 'docs/v9_timing_failed_proof.json').read_text())
    originals = ['src/poly32/guitar_voice_tdm_core.v', 'src/poly32/guitar_poly32_tdm.v']
    for name in originals:
        assert digest(baseline / name) == record['sources'][name], name
    runtime = ROOT / 'tests/runtime_temp'
    core = (baseline / originals[0]).read_text().replace(
        'module guitar_voice_tdm_core #', 'module guitar_voice_core_v9_reference #')
    parent = (baseline / originals[1]).read_text().replace(
        'module guitar_poly32_tdm #', 'module guitar_poly32_tdm_v9_reference #').replace(
        'guitar_voice_tdm_core #', 'guitar_voice_core_v9_reference #')
    (runtime / 'guitar_voice_v9_reference.v').write_text(core, encoding='utf-8')
    (runtime / 'guitar_poly32_v9_reference.v').write_text(parent, encoding='utf-8')
    sources = [
        'src/guitar_note_params.v', 'src/poly32/guitar_poly32_tdm.v',
        'src/poly32/guitar_voice_tdm_core.v', 'src/poly32/poly32_context_ram.v',
        'src/poly32/poly32_tail_cleaner.v', 'src/poly32/poly32_bus_manager.v',
        'src/gowin_adsr/gowin_adsr.v',
        'tests/ensemble_guitar_bank_models.v', 'tests/tb_excitation_tdm_v10.sv',
        'tests/runtime_temp/guitar_voice_v9_reference.v',
        'tests/runtime_temp/guitar_poly32_v9_reference.v',
        'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v',
    ]
    bound = source_hashes(sources + ['scripts/verify_excitation_tdm_v10.py'])
    executable = compile_sim('tb_excitation_tdm_v10', sources)
    output = simulate(executable, 'excitation_tdm_v10.log', timeout=2400)
    assert 'PASS EXCITATION TDM V10: 920 PCM frames' in output
    assert not any(word in output for word in ('FATAL', 'ERROR', 'Unable to open'))
    assert_source_hashes(bound)
    (ROOT / 'tests/results/excitation_tdm_v10.json').write_text(json.dumps({
        'passed': True, 'returncode': 0, 'PCM_frames': 920, 'voices': 32,
        'scope': 'real_TDM_and_Gowin_context_RAM; fast_delay_and_scratch_bank_models',
        'sources': bound,
    }, indent=2), encoding='utf-8')
    print(output, flush=True)


if __name__ == '__main__':
    main()
