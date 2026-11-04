import os
import shutil
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
iv=os.environ.get('IVERILOG') or shutil.which('iverilog')
vvp=os.environ.get('VVP') or shutil.which('vvp')
prim=os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
if not iv or not vvp or not Path(prim).exists():raise SystemExit('Set IVERILOG, VVP and GOWIN_PRIM_SIM.')
out=root/'tests/results';out.mkdir(exist_ok=True)
args=[iv]
if os.environ.get('IVERILOG_LIB'):args+=['-B',os.environ['IVERILOG_LIB']]
args+=['-g2012','-s','tb_init_equivalence','-s','GSR','-o',str(out/'init_equivalence.vvp')]
args += [str(root/p) for p in ('src/poly32/guitar_voice_tdm_core.v','src/poly32/poly32_context_ram.v',
                              'src/poly32/poly32_road_bank.v','src/poly32/poly32_scratch_bank.v',
                              'tests/reference/guitar_voice_tdm_core_baseline.v','tests/tb_init_equivalence.sv')]
args.append(prim)
log=''
for command in (args,[vvp,str(out/'init_equivalence.vvp')]):
    p=subprocess.run(command,cwd=root,capture_output=True,text=True,errors='replace',timeout=600)
    log+=p.stdout+p.stderr;(out/'init_equivalence_log.txt').write_text(log,encoding='utf-8')
    if p.returncode:raise RuntimeError(log[-4000:])
print(log[-2000:])
