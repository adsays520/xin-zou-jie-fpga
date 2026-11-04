"""Reproducible, original coefficient assets (48 kHz / 192 kHz). No sampled IRs.
Run from any directory. Generated ROMs are checked by test_guitar_fx_assets.py.
"""
from pathlib import Path
import json
import math
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'src/effects/rom'

def biquad(kind, f, q=.70710678, db=0):
    w=2*math.pi*f/48000; c=math.cos(w); s=math.sin(w); a=s/(2*q); A=10**(db/40)
    if kind=='hp': b=[(1+c)/2,-(1+c),(1+c)/2]; den=[1+a,-2*c,1-a]
    elif kind=='lp': b=[(1-c)/2,1-c,(1-c)/2];den=[1+a,-2*c,1-a]
    else: b=[1+a*A,-2*c,1-a*A];den=[1+a/A,-2*c,1-a/A]
    return [*(v/den[0] for v in b),-den[1]/den[0],-den[2]/den[0]]

# input HP, pre mid frequency/gain, bass shaping, output mid/gain, cab resonance,
# cab cutoff, first/second gain. Curves are deliberately different, not labels on a clipper.
PROFILES=[
 (90,1500,0,0,1000,0,2,5500,1,1),
 (110,850,6,-8,800,3,2,4800,5,1.1),
 (85,1700,3,-2,1200,2,3,5800,3.5,1.8),
 (85,1400,3,-3,1100,2,3,4200,10,2.8),
 (80,1300,3,-2,1000,2.5,3.5,4000,12,3.5),
 (70,900,1,2,750,1,2,4300,12,4),
 (100,1300,2,-3,1500,1,2,4800,10,3),
 (280,2500,5,-6,1800,1,0,7500,1.5,1),
 (80,1100,2,-1,950,2,2,6000,2,1.3),
 (100,1400,2,-3,750,-4,4,4200,14,4),
 (120,1600,3,-5,850,-3,3,4000,16,4.5),
]

def assets():
    h=np.sinc(2*18000/192000*(np.arange(129)-64)) * (2*18000/192000) * np.kaiser(129,7.5)
    h/=h.sum()
    # Individually normalize interpolation phases: constant input stays constant.
    up=h*4
    for phase in range(4):up[phase::4]/=up[phase::4].sum()
    coeff=[0]*2304;gain=[1024]*2048
    for n,p in enumerate(PROFILES):
        hp,pref,preg,bass,midf,midg,res,cut,g1,g2=p
        sections=[biquad('hp',hp),biquad('peak',pref,.85,preg),biquad('peak',180,.6,bass),
                  biquad('hp',65),biquad('peak',midf,.75,midg),biquad('peak',115,1.1,res),
                  biquad('lp',cut,.5411961),biquad('lp',cut,1.306563)]
        for s,row in enumerate(sections):
            coeff[n*128+s*8:n*128+s*8+5]=[round(v*2**20) for v in row]
        # Extra input bandwidth control before gain; broad presence reduction
        # belongs to the cabinet, and is skipped when the cabinet is disabled.
        for s,row in ((9,biquad('lp',6500 if n==7 else 4500)),
                      (10,biquad('peak',3200,.9,-4 if n in (3,4,9,10) else -2))):
            coeff[n*128+s*8:n*128+s*8+5]=[round(v*2**20) for v in row]
        for d in range(128):gain[n*128+d]=min(131071,round(g1*10**((d-64)*12/63/20)*1024))
    for t in range(8):
        coeff[2048+t*8:2053+t*8]=[round(v*2**20) for v in biquad('lp',3000+t*5000/7)]
    for w in range(16):
        coeff[2112+w*8:2117+w*8]=[round(v*2**20) for v in biquad('peak',350*(7**(w/15)),2,12)]
    return dict(fx_fir_up=(np.rint(up*131072).astype(int),18),
                fx_fir_down=(np.rint(h*131072).astype(int),18),
                fx_biquad=(coeff,24),
                fx_biquad_packed=([sum((coeff[i+j]&0xffffff)<<(24*j) for j in range(5)) for i in range(0,2304,8)],120),
                fx_gain=(gain,18),
                fx_tanh=([round(math.tanh(n/128)*65536) for n in range(513)],18),
                fx_level=([0 if v==0 else round(10**((-30+(v-1)*30/126)/20)*32768*trim)
                          for trim in (1,1,1,.7,.5,.35,.65,2.8,1.8,.55,.5,1,1,1,1,1)
                          for v in range(128)],18),
                fx_gate=([round(10**((-78+v*38/127)/20)*2**20) for v in range(128)],24),
                fx_lfo=([round(math.sin(2*math.pi*n/1024)*32767) for n in range(1024)],16),
                fx_compressor=([round((1 if n<=102 else ((n/102)**(-2/3)))*32768) for n in range(1024)],16))

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(values,bits) in assets().items():
        (OUT/(name+'.hex')).write_text(''.join(f'{int(v)&((1<<bits)-1):0{(bits+3)//4}x}\n' for v in values),encoding='ascii')
    (OUT/'profiles.json').write_text(json.dumps(PROFILES,indent=2)+'\n',encoding='ascii')
    print('Generated original FIR, EQ, gain, tanh, level, gate and LFO tables.')
