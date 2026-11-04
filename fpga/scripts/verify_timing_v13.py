import subprocess
import sys

from iverilog_runner import ROOT, compile_sim, simulate


PRIMITIVES = 'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'
CASES = [
    ('tb_audio_tick_v13', ['src/audio_driver.v', 'tests/reference_v12/audio_driver.v']),
    ('tb_queue_equivalence_v13', ['src/pluck_event_queue.v', 'tests/reference_v12/pluck_event_queue.v']),
    ('tb_pluck_event_queue', ['src/pluck_event_queue.v']),
    ('tb_scratch_v8', ['src/poly32/poly32_scratch_bank.v', PRIMITIVES]),
]


def main():
    for top, sources in CASES:
        executable = compile_sim(top, sources + [f'tests/{top}.sv'])
        output = simulate(executable, top + '.log')
        assert 'PASS' in output and 'ERROR' not in output, output
        print(output, flush=True)
    subprocess.run([sys.executable, '-B', '-X', 'utf8', 'scripts/verify_timing_v12.py'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-B', '-X', 'utf8', 'scripts/verify_excitation_tdm_v10.py'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
