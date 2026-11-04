import json

from iverilog_runner import ROOT, compile_sim, simulate, source_hashes, assert_source_hashes


def main():
    sources = [
        'src/poly32/guitar_voice_tdm_core.v', 'src/poly32/poly32_context_ram.v',
        'src/poly32/poly32_road_bank.v', 'src/poly32/poly32_scratch_bank.v',
        'tests/tb_excitation_math_v10.sv',
        'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v',
    ]
    bound = source_hashes(sources + ['scripts/verify_excitation_math_v10.py'])
    executable = compile_sim('tb_excitation_math_v10', sources)
    output = simulate(executable, 'excitation_math_v10.log', timeout=300)
    assert 'PASS EXCITATION MATH V10: 116807 ' in output
    assert not any(word in output for word in ('FATAL', 'ERROR', 'Unable to open'))
    assert_source_hashes(bound)
    (ROOT / 'tests/results/excitation_math_v10.json').write_text(json.dumps(
        {'passed': True, 'returncode': 0, 'cases': 116807, 'sources': bound}, indent=2), encoding='utf-8')
    print(output, flush=True)


if __name__ == '__main__':
    main()
