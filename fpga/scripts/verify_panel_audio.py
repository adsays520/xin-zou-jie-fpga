from pathlib import Path
import numpy as np
from iverilog_runner import compile_sim,simulate,ROOT
from validate_piano_sms import reference,read_raw
p=compile_sim('tb_panel_piano',['src/piano/piano_wavetable16_tdm.v','src/piano/piano_soundboard.v','src/piano/piano_ddr_bank.v','tests/piano/piano_packet_memory.sv','tests/tb_panel_piano.sv'])
for ratio in (1048576,2097152,1018739):
 raw=ROOT/f'tests/runtime_temp/panel_piano_{ratio}.raw'
 s=simulate(p,f'panel_piano_{ratio}.log','+KEY=96','+VEL=110','+FRAMES=2048',f'+RATIO={ratio}',f'+OUT={raw}')
 q=read_raw(raw)
 if ratio==1048576:assert np.array_equal(q,reference(96,110,2048)), 'unity changed piano samples'
 assert np.any(q) and np.max(np.abs(q))<8388607
 print(s,flush=True)
print('PASS panel piano: enabled unity exact; octave and negative vibrato; 16-voice deadline and retrigger')

for top,src in [('tb_panel_bass_drawn',['src/bass/bass_poly8.v','src/piano/drawn_synth16.v','src/piano/drawn_table_ram_pages.v','src/poly32/poly32_bus_manager.v','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v']),('tb_panel_violin',['violin_r15/violin_core.v'])]:
 p=compile_sim(top,src+['tests/'+top+'.sv'])
 s=simulate(p,top+'.log');assert 'PASS panel' in s,s
 print(s,flush=True)
