from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'scripts'))
from iverilog_runner import compile_sim,simulate
sources=['src/effects/'+n for n in ['guitar_fx.v','guitar_fx_biquad.v','guitar_fx_oversample.v','guitar_fx_modulation.v']]
p=compile_sim('tb_effects_deadline',[*sources,'tests/tb_effects_deadline.sv'])
print(simulate(p,'effects_deadline_log.txt'),flush=True)
