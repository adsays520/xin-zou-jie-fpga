"""Export actual RTL output for listening; WAV files are never FPGA inputs."""
from pathlib import Path
import json,wave
import numpy as np
r=Path(__file__).resolve().parents[1];out=r/'tests/results';preview=r/'preview';preview.mkdir(exist_ok=True)
log=(out/'drums_synth_render.log').read_text()
assert 'PASS algorithmic drums mode=1' in log
raw=np.loadtxt(out/'drums_synth_q23.txt',dtype=np.int64)
assert raw.ndim==2 and raw.shape[1]==5
rate=48000
names=['kick','snare','closed_hat','open_hat','clap','crash','ride','low_tom','mid_tom','high_tom','rim','cowbell']
clips={(int(k),int(v)):raw[(raw[:,0]==k)&(raw[:,1]==v),3:5] for k,v in np.unique(raw[:,:2],axis=0)}
def write(name,signal):
 assert np.abs(signal).max()<8388607
 # Fixed Q23 -> signed 16 bit conversion; no per-file normalization or EQ.
 audio=np.clip(np.rint(signal/256),-32768,32767).astype('<i2')
 with wave.open(str(preview/name),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes(audio.tobytes())
def spaced(values,gap=.25):
 return np.concatenate([part for x in values for part in (x,np.zeros((int(rate*gap),2),dtype=np.int64))])
write('kick_three_kits.wav',spaced([clips[k,0] for k in range(3)],.5))
write('kick_retrigger.wav',clips[1,12])
write('all_drums_tight_pop.wav',spaced([clips[1,v] for v in range(12)]))
metrics=[]
for (kit,voice),x in clips.items():
 peak=np.abs(x).max();mono=x.mean(axis=1)/8388608
 if voice==12:continue
 first=np.flatnonzero(np.any(x!=0,axis=1));assert len(first)>450
 m=dict(kit=kit,voice=names[voice],frames=len(x),peak_dbfs=float(20*np.log10(peak/8388608)),first_nonzero_sample=int(first[0]))
 if voice==0:
  attack=mono[32:32+960];f=np.fft.rfftfreq(8192,1/rate);power=np.abs(np.fft.rfft(attack*np.hanning(len(attack)),8192))**2
  m['attack_1k_4k_energy_percent']=float(100*power[(f>=1000)&(f<=4000)].sum()/power.sum())
  m['attack_20ms_rms_dbfs']=float(20*np.log10(np.sqrt(np.mean(attack**2))))
  m['body_50_150ms_rms_dbfs']=float(20*np.log10(np.sqrt(np.mean(mono[2400:7200]**2))))
  tail=np.sqrt(np.mean(mono[19200:24000]**2));m['tail_400_500ms_rms_dbfs']=float(20*np.log10(max(tail,1e-12)))
 metrics.append(m)
report={'source':'actual drum_synth + impulse-excited kick_modal RTL simulation, velocity 110, track level 127, before final performance mixer','sample_rate':rate,'normalization':False,'recordings_used_as_source':False,'results':metrics}
(out/'drums_audio_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2));print('PASS RTL listening exports: finite, unclipped, fixed playback scale')
