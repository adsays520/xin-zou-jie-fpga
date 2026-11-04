import os,shutil,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1];out=r/'tests/results';sys.path.insert(0,str(r/'host'))
from drum_patterns import BASIC_PRESETS,preset,frame
packets=[];cells=[]
for name in BASIC_PRESETS:
    p=preset(name);data=b''.join(p.upload_frames())+frame(0x52,1)
    assert len(data)==4716,len(data)
    packets.extend(data);cells.extend(v for row in p.cells for v in row)
for name,values in [('frames',packets),('cells',cells)]:
    (out/f'basic_patterns_{name}.hex').write_text(''.join(f'{v:02x}\n' for v in values))

sys.path.insert(0,str(r/'scripts'))
from iverilog_runner import compile_sim, simulate
p=compile_sim('tb_basic_patterns',['src/drums/drum_synth.v','src/drums/kick_modal.v','src/performance_mixer.v','src/drums/drum_machine.v','tests/tb_basic_patterns.sv','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'])
print(simulate(p,'basic_patterns_log.txt'),flush=True)
