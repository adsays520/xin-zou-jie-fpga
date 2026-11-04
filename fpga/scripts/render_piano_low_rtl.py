from pathlib import Path
import numpy as np
from iverilog_runner import simulate
from validate_piano_sms import read_raw,reference,write_wav
r=Path(__file__).resolve().parents[1];folder=r/'tests/runtime_temp/sms_audio';folder.mkdir(parents=True,exist_ok=True)
clips=[]
for key in (36,48):
 raw=folder/f'{key}_110.raw'
 s=simulate('tests/results/tb_piano_physical.vvp',f'piano_sms_{key}_110.log',f'+KEY={key}','+VEL=110','+FRAMES=24000',f'+OUT={raw}')
 assert 'PASS DDR piano' in s,s
 q=read_raw(raw);expected=reference(key,110,2048);assert np.array_equal(q[:2048],expected)
 clips.extend((q,np.zeros(12000,dtype=np.int64)));print(s,flush=True)
for key in (60,84,96,108):
 raw=folder/f'{key}_110.raw'
 q=read_raw(raw);assert len(q)==24000
 clips.extend((q,np.zeros(12000,dtype=np.int64)))
write_wav(r/'preview/piano_ddr_C2_C3_C4_C6_C7_C8_RTL.wav',np.concatenate(clips))
print('PASS low/high final RTL audition: C2,C3,C4,C6,C7,C8; fixed Q23 to 16-bit, no per-note normalization',flush=True)
