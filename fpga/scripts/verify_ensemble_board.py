from pathlib import Path
import re,os,sys
from iverilog_runner import compile_sim,simulate,ROOT
sources=re.findall(r'<File path="([^"\n]+\.v)"',(ROOT/'guitar_audio_low_speed.gprj').read_text())
sources=[s for s in sources if not s.startswith('ip/')]
# Avoid billions of idle vendor-memory events during full-bank boot.
# Unit memory and sounded core equivalence use real vendor primitives.
if '--vendor-guitar-banks' not in sys.argv:
    sources=[s for s in sources if s not in ('src/poly32/poly32_road_bank.v','src/poly32/poly32_scratch_bank.v')]
    sources+=['tests/ensemble_guitar_bank_models.v']
prim=os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
p=compile_sim('tb_ensemble_board',sources+['tests/piano/ddr_parameter_app_model.sv','tests/piano/ddr_phy_mock.sv','tests/storage/sd_sector_model.sv','tests/tb_ensemble_board.sv',prim])
s=simulate(p,'ensemble_board.log',timeout=7200)
assert 'PASS ENSEMBLE BOARD' in s and 'ERROR' not in s and 'Unable to open' not in s,s[-6000:]
print(s,flush=True)
