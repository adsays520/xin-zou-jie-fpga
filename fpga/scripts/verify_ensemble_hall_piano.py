import os
import re

from iverilog_runner import ROOT, compile_sim, simulate

sources = re.findall(r'<File path="([^"\n]+\.v)"', (ROOT / 'guitar_audio_low_speed.gprj').read_text())
sources = [source for source in sources if not source.startswith('ip/') and source not in
           ('src/poly32/poly32_road_bank.v', 'src/poly32/poly32_scratch_bank.v')]
sources.extend(['tests/ensemble_guitar_bank_models.v', 'tests/piano/ddr_parameter_app_model.sv',
                'tests/piano/ddr_phy_mock.sv', 'tests/storage/sd_sector_model.sv',
                'tests/tb_ensemble_hall_piano.sv', os.environ.get('GOWIN_PRIM_SIM',
                'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')])
executable = compile_sim('tb_ensemble_hall_piano', sources)
output = simulate(executable, 'ensemble_hall_piano.log', timeout=7200)
assert 'PASS ENSEMBLE HALL PIANO:' in output and 'ERROR' not in output and 'Unable to open' not in output, output[-6000:]
print(output, flush=True)
