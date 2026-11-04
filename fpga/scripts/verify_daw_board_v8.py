import re
from iverilog_runner import ROOT, compile_sim, simulate
from make_sd_v7_fixture import make_image

make_image(real_piano=True)


sources = re.findall(r'<File path="([^"\n]+\.v)"', (ROOT / 'guitar_audio_low_speed.gprj').read_text())
sources = [source for source in sources if not source.startswith('ip/') and source not in
           ('src/poly32/poly32_road_bank.v', 'src/poly32/poly32_scratch_bank.v')]
sources += ['tests/ensemble_guitar_bank_models.v', 'tests/piano/ddr_parameter_app_model.sv',
            'tests/piano/ddr_phy_mock.sv', 'tests/storage/sd_sector_model.sv', 'tests/tb_daw_board_v8.sv',
            'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v']
executable = compile_sim('tb_daw_board_v8', sources)
output = simulate(executable, 'daw_board_v8.log', timeout=7200)
assert 'PASS DAW BOARD V8:' in output and 'ERROR' not in output and 'Unable to open' not in output, output[-6000:]
print(output, flush=True)
