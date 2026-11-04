import os,shutil,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent.parent
iv=os.environ.get('IVERILOG') or shutil.which('iverilog')
vvp=os.environ.get('VVP') or shutil.which('vvp')
prim=os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
if not iv or not vvp:raise SystemExit('Set IVERILOG and VVP')
out=root/'tests/results';out.mkdir(exist_ok=True)
args=[iv]
if os.environ.get('IVERILOG_LIB'):args+=['-B',os.environ['IVERILOG_LIB']]
args+=['-g2012','-s','tb_audio_path_equivalence','-s','GSR','-o',str(out/'audio_path_equivalence.vvp')]
args += [str(root/f.attrib['path']) for f in ET.parse(root/'guitar_audio_low_speed.gprj').iter('File') if f.attrib.get('type')=='file.verilog']
args += [str(root/'tests/reference/guitar_audio_top_original.v'),str(root/'tests/tb_audio_path_equivalence.sv'),prim]
log=''
for command in (args,[vvp,str(out/'audio_path_equivalence.vvp')]):
    p=subprocess.run(command,cwd=root,capture_output=True,text=True,errors='replace',timeout=900)
    log+=p.stdout+p.stderr;(out/'audio_path_equivalence_log.txt').write_text(log,encoding='utf-8')
    if p.returncode:raise RuntimeError(log[-4000:])
print(log[-2000:])
