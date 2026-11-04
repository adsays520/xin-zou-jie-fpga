from pathlib import Path
import sys,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from iverilog_runner import *
p=compile_sim('tb_violin_sms',['violin_r15/violin_core.v','tests/tb_violin_sms.sv'])
print(simulate(p,'violin_sms_smoke.log'),flush=True)
# Complete-system elaboration uses the existing board bench, which supplies
# Gowin's required global GSR instance and the external DDR PHY model.
sources=[x.attrib['path'] for x in ET.parse(ROOT/'guitar_audio_low_speed.gprj').findall('.//File') if x.attrib.get('type')=='file.verilog' and x.attrib.get('enable')=='1' and not x.attrib['path'].startswith('ip/')]
sources=[s for s in sources if s not in ('src/poly32/poly32_road_bank.v','src/poly32/poly32_scratch_bank.v')]
sources+=['tests/ensemble_guitar_bank_models.v','tests/piano/ddr_parameter_app_model.sv','tests/piano/ddr_phy_mock.sv','tests/storage/sd_sector_model.sv','tests/tb_ensemble_board.sv','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v']
compile_sim('tb_ensemble_board',sources)
print('PASS complete board elaboration (external memory/PHY models)',flush=True)
