from pathlib import Path
import os,sys,json
import numpy as np
from iverilog_runner import compile_sim,simulate
from validate_piano_sms import reference,read_raw,write_wav
r=Path(__file__).resolve().parents[1];out=r/'tests/results';out.mkdir(exist_ok=True)
rawdir=r/'tests/runtime_temp/sms_audio';rawdir.mkdir(parents=True,exist_ok=True)
exe=compile_sim('tb_piano_physical',['src/piano/piano_wavetable16_tdm.v','src/piano/piano_soundboard.v','src/piano/piano_ddr_bank.v','tests/piano/piano_packet_memory.sv','tests/piano/tb_piano_physical.sv'])
records=[];clips=[]
cases=[(21,110,24000),(60,110,24000),(84,110,24000),(96,110,24000),(108,110,24000)]+[(60,v,2048) for v in (32,64,96,127)]
for key,vel,frames in cases:
 raw=rawdir/f'{key}_{vel}.raw'
 log=simulate(exe,f'piano_sms_{key}_{vel}.log',f'+KEY={key}',f'+VEL={vel}',f'+FRAMES={frames}',f'+OUT={raw}')
 assert 'PASS DDR piano' in log and 'ERROR' not in log and 'Unable to open' not in log,log
 q=read_raw(raw);expected=reference(key,vel,min(len(q),2048))
 assert np.array_equal(q[:len(expected)],expected),(key,vel,'integer reference mismatch',np.flatnonzero(q[:len(expected)]!=expected)[:8].tolist())
 board=read_raw(Path(str(raw)+'.board')).reshape(-1,2)
 assert np.array_equal(board[:,0],q) and np.array_equal(board[:,1],q)
 assert max(abs(q))<8388607
 records.append(dict(key=key,velocity=vel,frames=len(q),integer_frames=len(expected),peak=float(max(abs(q))/8388608),stereo_unity_exact=True))
 if vel==110:clips.extend([q,np.zeros(12000,dtype=np.int64)])
 print(log.strip(),flush=True)
preview=r/'preview';preview.mkdir(exist_ok=True)
write_wav(preview/'piano_sms_ddr_A0_C4_C6_C7_C8.wav',np.concatenate(clips))
result=dict(passed=True,records=records,scope='actual RTL, independent integer first 2048 samples/case, pedal/retrigger/16-voice stress in bench',hardware_listening_verified=False)
(out/'piano_sms_result.json').write_text(json.dumps(result,indent=2))
print('PASS integrated SMS piano: integer reference, unity stereo, pedal/retrigger/16-voice deadline, RTL audition',flush=True)
