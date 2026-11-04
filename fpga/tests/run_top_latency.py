import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parent.parent
iv = os.environ.get('IVERILOG') or shutil.which('iverilog')
vvp = os.environ.get('VVP') or shutil.which('vvp')
primitive = os.environ.get('GOWIN_PRIM_SIM', 'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
if not iv or not vvp or not Path(primitive).exists():
    raise SystemExit('Set IVERILOG, VVP and GOWIN_PRIM_SIM to installed Icarus / GW5A simulator libraries.')
out = root/'tests/results'
out.mkdir(exist_ok=True)
args = [iv]
if os.environ.get('IVERILOG_LIB'):
    args.extend(['-B',os.environ['IVERILOG_LIB']])
args.extend(['-g2012','-s','tb_top_latency','-s','GSR','-o',str(out/'top_latency.vvp')])
args.extend(str(root / f.attrib['path']) for f in ET.parse(root/'guitar_audio_low_speed.gprj').iter('File')
            if f.attrib.get('type') == 'file.verilog')
args.extend([primitive,str(root/'tests/tb_top_latency.sv')])
log = ''
for command in (args, [vvp,str(out/'top_latency.vvp')]):
    p = subprocess.run(command,cwd=root,capture_output=True,text=True,errors='replace',timeout=600)
    log += p.stdout+p.stderr
    (out/'top_latency_log.txt').write_text(log,encoding='utf-8')
    if p.returncode:
        raise RuntimeError(log[-5000:])
print(log[-3000:])
