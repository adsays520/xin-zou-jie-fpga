"""Independent integer sample model for the V16 SMS RTL.
All sound is synthesized from spectral parameters; no PCM waveform playback.
"""
from pathlib import Path
import json,sys,numpy as np
from scipy.io import wavfile
from numba import njit
P=Path(__file__).resolve().parents[1];R=P/'violin_r15/sms_rom'
def read(name,shape=None,signed=0):
 a=np.array([int(x,16) for x in (R/name).read_text().split()],dtype=np.int64)
 if signed:a=np.where(a>=2**(signed-1),a-2**signed,a)
 return a.reshape(shape) if shape else a
A=read('amplitude.hex',(46,8,64));PH=read('phase.hex',(46,64));RC=read('release.hex',(46,64));F=read('frequency.hex');SIN=read('sine.hex',signed=16)
@njit(cache=True)
def ss(d,shift):
 if d>0:return (d+(1<<shift)-1)>>shift
 if d<0:return -((-d+(1<<shift)-1)>>shift)
 return 0
@njit(cache=True)
def signed(x,bits):
 x=x&((1<<bits)-1)
 return x-(1<<bits) if x&(1<<(bits-1)) else x
@njit(cache=True)
def render(keys,ons,legs,vels,forces,ratios,A,PH,RC,F,SIN):
 N=len(keys);out=np.zeros(N,np.int32);amps=np.zeros(64,np.int64);offs=np.zeros(64,np.int64);motion=np.zeros(4,np.int64)
 gate=False;active=False;fast=False;snap=True;note=0;key=55;env_age=0;off_age=48000
 target=17538956;cur=17538956;veltarget=0;gain=0;bow=0;base=0;lfsr=0x4f329a17;low=0;slow=0;mc=0;pending=0
 knots=np.array([0,1200,3600,7680,16800,31200,62400,110400]);recips=np.array([13981,6991,4112,1840,1165,538,350,0])
 for i in range(N):
  if keys[i]>=0:
   if forces[i]:gate=False;fast=True;off_age=0
   elif ons[i]:
    note=keys[i]-55;key=keys[i];target=F[note]
    if not active:cur=target;snap=True
    if not legs[i] or not gate:env_age=0
    gate=True;active=True;fast=False;off_age=0;veltarget=vels[i]<<8
   elif keys[i]==key:gate=False;off_age=0
  out[i]=pending
  stage=7
  for k in range(7):
   if env_age<knots[k+1]:stage=k;break
  frac=min(65535,((env_age-knots[stage])*recips[stage])>>8)
  if gate:
   env_age=min(110400,env_age+1);bow=min(32767,bow+32)
  else:
   if off_age>=47999 or (fast and off_age>=383):active=False
   off_age=min(48000,off_age+1)
   if bow:bow=bow-((bow>>9)+1)
  cur+=ss(target-cur,8);gain+=ss(veltarget-gain,8);inc=(cur*ratios[i])>>20
  base=(base+inc)&0xffffffff
  if mc==511:
   vals=np.array([signed(lfsr,16),signed(lfsr>>8,16),signed(lfsr>>16,16),signed(((lfsr&255)<<8)|(lfsr>>24),16)])
   for g in range(4):motion[g]=signed(motion[g]+(signed(vals[g]-motion[g],16)>>5),16)
  mc=(mc+1)&511
  oldlow=low;low=signed(low+((signed(lfsr,24)-low)>>2),24);slow=signed(slow+((oldlow-slow)>>6),24)
  lfsr=((lfsr<<1)|(((lfsr>>31)^(lfsr>>21)^(lfsr>>1)^lfsr)&1))&0xffffffff
  acc=0
  for h in range(64):
   p=(base*(h+1)+(offs[h]<<16))&0xffffffff;sine=SIN[p>>20]
   targetamp=(A[note,stage,h]+(((A[note,min(7,stage+1),h]-A[note,stage,h])*frac)>>16))<<8
   if not active:nxt=0
   elif not gate:
    if fast:nxt=amps[h]-((amps[h]>>5)+(1 if amps[h]!=0 else 0))
    else:
     dec=(amps[h]*RC[note,h])>>16
     nxt=amps[h]-(dec+1) if amps[h]>dec else 0
   elif inc*(h+1)>=0x78000000:nxt=0
   else:nxt=amps[h]+ss(targetamp-amps[h],6)
   amps[h]=nxt
   spectral_motion=motion[h>>4]>>3
   adjusted=nxt+((nxt*spectral_motion)>>15)
   if inc*(h+1)<0x78000000:acc+=(adjusted*sine)>>16
   d=signed(PH[note,h]-offs[h],16)
   offs[h]=PH[note,h] if snap else ((offs[h]+ss(d,9))&65535)
  voice=max(-8388608,min(8388607,(acc*gain)>>15))
  ns=signed(((low-slow)*bow)>>20,24);pending=max(-8388608,min(8388607,voice+((ns*gain)>>15))) if active else 0
  snap=False
 return out

def events(N):
 return [np.full(N,-1,np.int64),np.zeros(N,np.int64),np.zeros(N,np.int64),np.full(N,100,np.int64),np.zeros(N,np.int64),np.full(N,1048576,np.int64)]
def put(e,i,key,on=1,leg=0,vel=100,force=0):
 e[0][i]=key;e[1][i]=on;e[2][i]=leg;e[3][i]=vel;e[4][i]=force

def smoke():
 e=events(12000)
 put(e,0,55);put(e,1200,69,leg=1);put(e,1800,55,on=0,vel=1);e[5][2400:]=1176987
 put(e,3000,69,on=0,vel=1);put(e,4000,100,vel=127);put(e,5000,100,on=0,vel=1,force=1)
 for i in range(5600,11000):
  if i%110==0:put(e,i,55+((i-5600)//110)%46,leg=1)
 put(e,11200,100,on=0,vel=1,force=1)
 return render(*e,A,PH,RC,F,SIN)

if __name__=='__main__':
 if '--compare' in sys.argv:
  got=np.loadtxt(P/'tests/results/violin_sms_audio.txt',dtype=np.int32);ref=smoke();bad=np.flatnonzero(got!=ref)
  if len(bad):
   i=int(bad[0]);print('FIRST MISMATCH',i,int(got[i]),int(ref[i]),'mismatches',len(bad));sys.exit(1)
  print('PASS independent integer model: 12000 RTL output samples bit exact',flush=True)
 else:
  O=P.parents[1]/'试听';N=4*168000;e=events(N)
  for j,key in enumerate([55,62,69,76]):put(e,j*168000,key);put(e,j*168000+115200,key,on=0,vel=1)
  x=render(*e,A,PH,RC,F,SIN)
  assert np.max(np.abs(x))<8388607
  wavfile.write(O/'V16_最终定点模型_四音干声.wav',48000,(x>>8).astype(np.int16))
  # A legato passage plus one long sustain. No vibrato is enabled in this version.
  e=events(384000)
  for i,key in enumerate([62,64,66,67,69,71,73,74]):put(e,i*18000,key,leg=int(i>0),vel=96)
  put(e,144000,74,on=0,vel=1);put(e,192000,69,vel=100);put(e,336000,69,on=0,vel=1)
  y=render(*e,A,PH,RC,F,SIN);assert np.max(np.abs(y))<8388607
  wavfile.write(O/'V16_最终定点模型_连奏与长音.wav',48000,(y>>8).astype(np.int16))
  (O/'定点模型音频检查.json').write_text(json.dumps(dict(four_note_peak=int(np.max(np.abs(x))),legato_peak=int(np.max(np.abs(y))),vibrato=False,model='Independent integer model; RTL equivalence is checked separately',sample_rate=48000),indent=2))
  print('Saved final fixed-model auditions',flush=True)
