import json
from iverilog_runner import compile_sim, simulate, OUT, source_hashes


PRIM = 'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'
CASES = [
    ('tb_scratch_v8', ['src/poly32/poly32_scratch_bank.v', 'tests/tb_scratch_v8.sv', PRIM], 'PASS SCRATCH V8:'),
    ('tb_ensemble_protocol_v8', ['src/guitar_uart_trigger.v', 'tests/tb_ensemble_protocol_v8.sv'], 'PASS ENSEMBLE PROTOCOL V8:'),
    ('tb_ensemble_mixer_v8', ['src/performance_mixer.v', 'src/ensemble_mixer.v', 'tests/tb_ensemble_mixer_v8.sv'], 'PASS ENSEMBLE MIXER V8:'),
    ('tb_ensemble_capabilities_v8', ['src/guitar_uart_trigger.v', 'src/ensemble_capabilities.v',
                                  'src/verification/verification_telemetry.v', 'tests/tb_ensemble_capabilities_v8.sv'], 'PASS ENSEMBLE CAPABILITIES V8:'),
]


def main():
    results = []
    for top, sources, marker in CASES:
        executable = compile_sim(top, sources)
        log = simulate(executable, top + '.log', timeout=180)
        assert marker in log and not any(error in log for error in ('ERROR', 'FATAL', 'Unable to open')), log
        results.append({'top': top, 'passed': True, 'sources': source_hashes(sources)})
        print(log, flush=True)
    (OUT / 'units_v8.json').write_text(json.dumps({'passed': True, 'cases': results}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
