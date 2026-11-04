import os,shutil,subprocess,json,wave
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'tests/results'
iv=os.environ.get('IVERILOG') or shutil.which('iverilog');vvp=os.environ.get('VVP') or shutil.which('vvp')
args=[iv]+(['-B',os.environ['IVERILOG_LIB']] if os.environ.get('IVERILOG_LIB') else [])
args+=['-g2012','-s','tb_drums_acoustic','-o',str(out/'drums_acoustic.vvp'),
       str(root/'src/drums/drum_synth.v'),str(root/'tests/reference/drum_synth_before_pages.v'),str(root/'tests/tb_drums_acoustic.sv')]
log=''
for cmd in (args,[vvp,str(out/'drums_acoustic.vvp')]):
    p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=1800)
    log+=p.stdout+p.stderr;(out/'drums_acoustic_log.txt').write_text(log,encoding='utf-8')
    if p.returncode:raise RuntimeError(log[-4000:])
data=np.loadtxt(out/'drums_acoustic_q23.txt',dtype=np.int32)
metrics=[];sounds=[]
for v in (0,1,2,3,5,7):
    a=data[(data[:,0]==1)&(data[:,1]==v),3:5].astype(np.float64)
    assert len(a)==8192
    p=np.abs(np.fft.rfft((a[:2048,0]-a[:2048,0].mean())*np.hanning(2048)))**2
    freq=np.fft.rfftfreq(2048,1/48000)
    item=dict(voice=v,peak_q23=int(np.abs(a).max()),above_3khz=float(p[freq>=3000].sum()/p.sum()),
              dominant_hz=float(freq[p.argmax()]),rms_first_10ms=float(np.sqrt(np.mean(a[:480]**2))),
              rms_last_10ms=float(np.sqrt(np.mean(a[-480:]**2))))
    assert item['peak_q23']<8388607 and item['rms_first_10ms']>1000
    if v==0:assert freq[p.argmax()]<180, item
    if v==2:assert item['above_3khz']>.65 and item['rms_last_10ms']<item['rms_first_10ms']*.05,item
    metrics.append(item);sounds.extend([a,np.zeros((4800,2))])
audio=np.concatenate(sounds)
pcm=np.round(audio*(28000/np.abs(audio).max())).clip(-32768,32767).astype('<i2')
with wave.open(str(out/'原声质感鼓组_RTL试听.wav'),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(48000);f.writeframes(pcm.tobytes())
(out/'drums_acoustic_metrics.json').write_text(json.dumps(dict(source='actual RTL Q23 output, common normalization for listening only',physical_listening_verified=False,metrics=metrics),ensure_ascii=False,indent=2),encoding='utf-8')
print(log[-2500:]);print(json.dumps(metrics,indent=2))
