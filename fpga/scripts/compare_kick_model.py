from pathlib import Path
import numpy as np
from generate_kick_modal import render,write_wav
r=Path(__file__).resolve().parents[1]
data=np.loadtxt(r/'tests/results/drums_synth_q23.txt',dtype=np.int64)
clips=[]
for kit in range(3):
 actual=data[(data[:,0]==kit)&(data[:,1]==0),3]
 model=render(kit)[:len(actual)]
 scaled=(model*127)>>10
 expected=(scaled<<1)+(scaled>>2)
 expected=np.concatenate([np.zeros(32,dtype=np.int64),expected[:-32]])
 np.testing.assert_array_equal(actual,expected)
 clips.extend([actual,np.zeros(24000,dtype=np.int64)])
write_wav(r/'preview/kick_body_rtl.wav',np.concatenate(clips))
print('PASS new kick RTL equals integer resonator model at every output bit: 3 kits x 24000 frames')
