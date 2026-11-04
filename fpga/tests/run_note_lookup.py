import os,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
iv=os.environ.get('IVERILOG') or shutil.which('iverilog')
vvp=os.environ.get('VVP') or shutil.which('vvp')
if not iv or not vvp:raise SystemExit('Set IVERILOG and VVP')
out=root/'tests/results';out.mkdir(exist_ok=True)
args=[iv]
if os.environ.get('IVERILOG_LIB'):args+=['-B',os.environ['IVERILOG_LIB']]
args+=['-g2012','-s','tb_note_lookup','-o',str(out/'note_lookup.vvp'),str(root/'src/guitar_note_params.v'),
       str(root/'tests/reference/guitar_note_params_original.v'),str(root/'tests/tb_note_lookup.sv')]
log=''
for command in (args,[vvp,str(out/'note_lookup.vvp')]):
    p=subprocess.run(command,cwd=root,capture_output=True,text=True,errors='replace',timeout=60)
    log+=p.stdout+p.stderr;(out/'note_lookup_log.txt').write_text(log,encoding='utf-8')
    if p.returncode:raise RuntimeError(log[-4000:])
print(log)
