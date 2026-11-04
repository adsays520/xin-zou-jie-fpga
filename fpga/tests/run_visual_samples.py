from pathlib import Path
import sys,os
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'scripts'))
from iverilog_runner import compile_sim,simulate
p=compile_sim('tb_visual_samples',['src/verification/verification_visuals.v','tests/tb_visual_samples.sv',os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')])
print(simulate(p,'visual_samples_log.txt'),flush=True)
