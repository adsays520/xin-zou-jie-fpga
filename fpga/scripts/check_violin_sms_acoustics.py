from pathlib import Path
import sys,json,numpy as np
from scipy.signal import periodogram
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from violin_sms_integer_model import *
records=[]
for key in range(55,101):
 e=events(36000);put(e,0,key,vel=127);x=render(*e,A,PH,RC,F,SIN).astype(np.float64)/8388608
 steady=x[12000:];peak=float(np.max(np.abs(x)));rms=float(np.sqrt(np.mean(steady**2)))
 assert peak<.9 and rms>.015,(key,peak,rms)
 # Test pitch at its expected fundamental rather than the loudest overtone.
 freq,power=periodogram(steady,48000,nfft=262144);ft=440*2**((key-69)/12);sel=(freq>ft*.98)&(freq<ft*1.02);fp=float(freq[sel][np.argmax(power[sel])]);cents=float(1200*np.log2(fp/ft));assert abs(cents)<4,(key,cents)
 records.append(dict(midi=key,peak=peak,steady_rms=rms,fundamental_cents_error=cents))
# Full release must reach a quiet tail rather than a stuck plateau.
e=events(180000);put(e,0,55);put(e,115200,55,on=0,vel=1);x=render(*e,A,PH,RC,F,SIN)
assert not np.any(x[-8000:]),'release did not reach silence'
# Common-gain monotonic velocity response.
vr=[]
for v in (1,30,60,100,127):
 e=events(24000);put(e,0,69,vel=v);x=render(*e,A,PH,RC,F,SIN).astype(float);vr.append(float(np.sqrt(np.mean(x[12000:]**2))))
assert all(b>a for a,b in zip(vr,vr[1:])),vr
result=dict(passed=True,all_keys=records,velocity_rms=vr,release_reaches_silence=True,vibrato=False)
(P/'tests/results/violin_sms_acoustic_checks.json').write_text(json.dumps(result,indent=2))
print('PASS all 46 notes at velocity 127: pitch, nonzero sustain and headroom; velocity monotonic; release quiet',flush=True)
print('maximum peak',max(r['peak'] for r in records),'maximum cents error',max(abs(r['fundamental_cents_error']) for r in records))
