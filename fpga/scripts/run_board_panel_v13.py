import argparse
import re

from iverilog_runner import ROOT, compile_sim, simulate


CASES = {'daw': ('tb_daw_board_v8', 'PASS DAW BOARD V8:'),
         'legacy': ('tb_ensemble_board', 'PASS ENSEMBLE BOARD:'),
         'hall': ('tb_ensemble_hall_piano', 'PASS ENSEMBLE HALL PIANO:')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=CASES)
    arguments = parser.parse_args()
    top, marker = CASES[arguments.case]
    sources = re.findall(r'<File path="([^"\n]+\.v)"', (ROOT / 'guitar_audio_low_speed.gprj').read_text())
    sources = [name for name in sources if not name.startswith('ip/') and name not in
               ('src/poly32/poly32_road_bank.v', 'src/poly32/poly32_scratch_bank.v')]
    sources += ['tests/ensemble_guitar_bank_models.v', 'tests/piano/ddr_parameter_app_model.sv',
                'tests/piano/ddr_phy_mock.sv', 'tests/storage/sd_sector_model.sv', f'tests/{top}.sv',
                'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v']
    executable = compile_sim(top, sources)
    output = simulate(executable, arguments.case + '_board_v13.log', timeout=9600)
    assert marker in output and not any(word in output for word in ('FATAL', 'ERROR', 'Unable to open')), output[-6000:]
    print(output, flush=True)


if __name__ == '__main__':
    main()
