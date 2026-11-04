"""Impulse-excited modal kick: no recordings, no waveform playback."""
from pathlib import Path
import math,json,wave
import numpy as np
R=Path(__file__).resolve().parents[1];FS=48000
# Modal approximation of batter head, coupled carry head/cavity and shell.
FREQ=[64,96,137,181,239,313,409,537,701,919,1193,1543]
DECAY=[.115,.095,.072,.055,.041,.032,.025,.019,.015,.011,.009,.007]
WEIGHT=[.75,1,.72,.52,.36,.25,.17,.12,.08,.055,.035,.022]
def parameters(kit):
 tune=[1.0,.94,1.07][kit];damp=[1.0,.82,.9][kit]
 rows=[]
 for f,t,w in zip(FREQ,DECAY,WEIGHT):
  omega=2*math.pi*f*tune/FS;radius=math.exp(-1/(FS*t*damp))
  # Normalized 2.5 ms raised-cosine strike drives each damped resonator.
  rows.append([round(2*radius*math.cos(omega)*(1<<30)),round(-radius*radius*(1<<30)),round(math.sin(omega)*w/60*(1<<30))])
 return rows
FORCE=[round((1-math.cos(2*math.pi*(n+1)/121))*.5*(1<<23)) for n in range(120)]
def render(kit,velocity=110):
 c=parameters(kit);y1=[0]*12;y2=[0]*12;audio=[]
 for n in range(48000):
  force=(FORCE[n]*velocity)>>7 if n<120 else 0
  accum=0
  for j,(a,b,g) in enumerate(c):
   z=a*y1[j]+b*y2[j]+g*force
   y=(z+(1<<29))>>30
   if n>=48000:y=0
   y2[j]=y1[j];y1[j]=y;accum+=y
  audio.append(accum)
 return np.array(audio,dtype=np.int64)
def write_wav(p,values):
 stereo=np.repeat(values[:,None],2,axis=1)
 with wave.open(str(p),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(FS);w.writeframes(np.clip(np.rint(stereo/256),-32768,32767).astype('<i2').tobytes())
def main():
 out=R/'preview';out.mkdir(exist_ok=True)
 clips=[render(k) for k in range(3)]
 # Predict existing drum track/master scale: /8 * 127/128 * 2.25.
 scaled=[np.rint(x*(127/1024)*2.25).astype(np.int64) for x in clips]
 write_wav(out/'kick_body_model_preview.wav',np.concatenate([v for x in scaled for v in (x,np.zeros(12000,dtype=np.int64))]))
 print([(float(np.max(np.abs(x))),float(20*np.log10(np.max(np.abs(x))/8388608))) for x in scaled])
 data=[]
 for kit in range(3):
  for row in parameters(kit):data.extend(row)
 rom=R/'src/drums/rom';rom.mkdir(exist_ok=True)
 (rom/'kick_modal_coeffs.hex').write_text(''.join(f'{x&0xffffffff:08x}\n' for x in data),encoding='ascii')
 (rom/'kick_force.hex').write_text(''.join(f'{x:06x}\n' for x in FORCE),encoding='ascii')
 (R/'tests/results/kick_modal_parameters.json').write_text(json.dumps({'frequencies':FREQ,'decay_seconds':DECAY,'weights':WEIGHT,'force':'mathematical raised cosine 2.5 ms','source_recordings':False},indent=2))
if __name__=='__main__':main()
