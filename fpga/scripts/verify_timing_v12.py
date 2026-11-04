import subprocess
import sys

from iverilog_runner import ROOT, compile_sim, simulate


PRIMITIVES = 'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'
CASES = [
    ('tb_raster_equivalence_v12', ['src/panel_raster.v', 'tests/reference_v11/panel_raster.v']),
    ('tb_pitch_pipeline_v12', ['src/panel_pitch.v', 'tests/reference_v11/panel_pitch.v']),
    ('tb_ddr_equivalence_v12', ['src/piano/piano_ddr_transport.v',
         'tests/reference_v11/piano_ddr_transport.v', 'src/excitation_ddr/async_fifo64.v', PRIMITIVES]),
    ('tb_address_math_v12', ['src/poly32/poly32_road_bank.v', PRIMITIVES]),
]


def main():
    for top, sources in CASES:
        executable = compile_sim(top, sources + [f'tests/{top}.sv'])
        output = simulate(executable, top + '.log')
        assert 'PASS V12' in output and 'ERROR' not in output and 'WARNING' not in output, output
        print(output, flush=True)
    for script in ('verify_packed_road.py', 'verify_piano_ddr_transport.py'):
        subprocess.run([sys.executable, '-B', '-X', 'utf8', 'scripts/' + script], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
