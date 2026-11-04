from pathlib import Path
import json,math
import numpy as np
from pack_piano_ddr_bank import ROOT,pack
p=ROOT/'src/piano/sms'
report=json.loads((ROOT/'tests/results/piano_ddr_bank_measure.json').read_text())
def read(name):return [int(x,16) for x in (p/name).read_text().split()]
def signed(q,b):return (q^(1<<(b-1)))-(1<<(b-1))
weights=read('weights.hex');freq=read('frequency.hex');trans=read('transient.hex');noise=read('noise.hex')
factors=[]
for key in range(21,109):
 rows=[r for r in report['rows'] if r['key']==key]
 assert [r['velocity'] for r in rows]==[32,64,96,127]
 levels=[r['rms']/(r['velocity']/127)**1.6 for r in rows]
 target=math.exp(sum(math.log(x) for x in levels)/4)
 factors.extend(target/x for x in levels)
for bank,scale in enumerate(factors):
 for m in range(16):
  index=bank*16+m;oldshift=freq[index]>>27
  values=np.array([signed((weights[index]>>(8*j))&255,8) for j in range(24)],dtype=float)*(2.**oldshift)*scale
  shift=max(0,int(math.ceil(math.log2(max(float(max(abs(values))),1)/127))))
  assert shift<=31
  q=np.rint(values/(2.**shift)).astype(np.int64);assert max(abs(q))<=127
  weights[index]=sum((int(v)&255)<<(8*j) for j,v in enumerate(q))
  freq[index]=(freq[index]&((1<<27)-1))|(shift<<27)
 for m in range(8):
  index=bank*8+m;word=trans[index];oldexp=word&3
  re=signed((word>>16)&16383,14)*(2.**(10+oldexp*2))*scale
  im=signed((word>>2)&16383,14)*(2.**(10+oldexp*2))*scale
  exponent=next((e for e in range(4) if max(abs(re),abs(im))/(2.**(10+e*2))<=8191),None)
  assert exponent is not None,(bank,m,'transient calibration range')
  re=round(re/(2.**(10+exponent*2)));im=round(im/(2.**(10+exponent*2)))
  trans[index]=(word&~((1<<30)-1))|((re&16383)<<16)|((im&16383)<<2)|exponent
 noise[bank]=sum((round(signed((noise[bank]>>(16*j))&65535,16)*scale)&65535)<<(16*j) for j in range(4))
for name,values,width in [('weights.hex',weights,48),('frequency.hex',freq,8),('transient.hex',trans,16),('noise.hex',noise,16)]:
 (p/name).write_text(''.join(f'{q:0{width}x}\n' for q in values),encoding='ascii')
(p/'calibration.json').write_text(json.dumps(dict(method='post-quantization integer body RMS; continuous MIDI law retained',factors=factors),indent=2))
pack()
print('PASS applied per-layer integer synthesis calibration',min(factors),max(factors),flush=True)
