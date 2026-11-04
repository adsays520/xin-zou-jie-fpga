import hashlib
import json
from pathlib import Path
import shutil

from iverilog_runner import ROOT, compile_sim, simulate, source_hashes, assert_source_hashes


EXPERIMENT = ROOT.parent / 'experiments/drawn_ram_pages_20261023'


def main():
    output = ROOT / 'tests/results/drawn_v9.json'
    assert not output.exists(), 'Preserve prior drawn-RAM validation'
    for filename in ('proof.json', 'synthesis/proof.json', 'gate/proof.json'):
        proof = json.loads((EXPERIMENT / 'tests/results' / filename).read_text())
        assert proof['passed'] and proof['sources_unchanged']
        for name, value in proof['sources'].items():
            path = Path(name) if Path(name).is_absolute() else EXPERIMENT / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == value, name
    core = ROOT / 'src/piano/drawn_synth16.v'
    memory = ROOT / 'src/piano/drawn_table_ram_pages.v'
    expected = (EXPERIMENT / 'tests/runtime_temp/drawn_paged.v').read_text().replace(
        'module drawn_synth16_paged(', 'module drawn_synth16(')
    assert core.read_text() == expected, 'Integrated core differs from verified experiment'
    assert memory.read_bytes() == (EXPERIMENT / 'drawn_table_ram_pages.v').read_bytes()
    runtime = ROOT / 'tests/runtime_temp'
    reference = runtime / 'drawn_reference.v'
    shutil.copy2(EXPERIMENT / 'tests/runtime_temp/drawn_reference.v', reference)
    netlist = EXPERIMENT / 'tests/results/gate/impl/gwsynthesis/drawn_table_gate.vg'
    cases = []
    for label, implementation in (('rtl', memory), ('actual_gowin_memory_gate', netlist)):
        top = 'tb_drawn_v9_' + label
        bench = runtime / (top + '.sv')
        bench.write_text((EXPERIMENT / 'tb_drawn_ram_pages.sv').read_text().replace(
            'module tb_drawn_ram_pages;', f"module {top};\n    GSR GSR(.GSRI(1'b1));").replace(
            'drawn_synth16_paged new_core(', 'drawn_synth16 new_core('))
        inputs = [str(path) for path in (core, implementation, reference, bench,
                  ROOT / 'src/poly32/poly32_bus_manager.v')]
        inputs.append('D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
        bound = source_hashes(inputs + [str(memory), str(Path(__file__))])
        executable = compile_sim(top, inputs)
        log = simulate(executable, top + '.log', timeout=900)
        assert 'PASS DRAWN RAM PAGES:' in log and not any(word in log for word in ('ERROR', 'FATAL', 'Unable to open'))
        assert_source_hashes(bound)
        cases.append({'name': label, 'passed': True, 'returncode': 0, 'sources': bound})
        print(label + ': ' + log, flush=True)
    output.write_text(json.dumps({'passed': True, 'cases': cases,
                                 'scope': 'integrated_actual_core_PCM_and_synthesized_RAM_gate_not_whole_board'},
                                indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
