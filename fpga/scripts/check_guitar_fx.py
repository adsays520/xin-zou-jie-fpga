"""Check assets and RTL output against an independent integer 4x model."""
from pathlib import Path
import sys
import math
import numpy as np
from generate_guitar_fx import assets,PROFILES,ROOT

TABLES={k:list(map(int,v[0])) for k,v in assets().items()}
SIM=ROOT/'impl/guitar_fx_verify'
def sat(x):return min(8388607,max(-8388608,int(x)))
def rounded(x,bits):return (x+(1<<(bits-1))-(x<0))>>bits
def trunc(x,bits):return (x+((1<<bits)-1 if x<0 else 0))>>bits

class Oversample:
    def __init__(self,amp,drive=64):
        self.up=TABLES['fx_fir_up'];self.down=TABLES['fx_fir_down'];self.tanh=TABLES['fx_tanh']
        self.g1=TABLES['fx_gain'][amp*128+drive]
        self.g2=[1024,1126,1843,2867,3584,4096,3072,1024,1331,4096,4608][amp]
        self.bias=262144 if amp==5 else 131072 if amp in (3,4) else 0
        self.dc=256816 if amp==5 else 130400 if amp in (3,4) else 0
        self.amp=amp;self.h=[0]*64;self.o=[0]*256;self.hi=self.lo=0
    def curve(self,x,g):
        u=(x*g>>10)+self.bias;mag=min(4194304,abs(u));idx=mag>>13;f=mag&8191
        val=(self.tanh[idx]*8192+(self.tanh[min(idx+1,512)]-self.tanh[idx])*f)>>9
        return (-val if u<0 else val)-self.dc
    def process(self,sample):
        self.h=[int(sample)]+self.h[:-1]
        for phase in range(4):
            x=sat(rounded(sum(v*c for v,c in zip(self.h,self.up[phase::4])),17))
            x=self.curve(x,self.g1)
            if self.amp==6:x=abs(x)
            x <<= 8
            dh=x-self.hi;dl=x-self.hi-self.lo
            low=x-self.hi if abs(dl)<8 else self.lo+trunc(dl,3)
            self.hi=x if abs(dh)<512 else self.hi+trunc(dh,9)
            self.lo=low
            self.o=[self.curve(rounded(low,8),self.g2)]+self.o[:-1]
        return sat(rounded(sum(v*c for v,c in zip(self.o[3:],self.down)),17))

def check_assets():
    for key,(values,bits) in assets().items():
        actual=[int(s,16) for s in (ROOT/'src/effects/rom'/f'{key}.hex').read_text().split()]
        assert actual==[int(v)&((1<<bits)-1) for v in values],key
    h=np.array(TABLES['fx_fir_down'])/131072
    f=np.fft.rfftfreq(262144,1/192000);response=np.abs(np.fft.rfft(h,262144))
    stop=float(20*np.log10(response[f>=24000].max()))
    ripple=float(np.max(np.abs(20*np.log10(response[f<=12000]))))
    assert stop < -65,("FIR stop",stop)
    assert ripple<.02,("FIR pass",ripple)
    for p in range(11):
        for s in (*range(8),9,10):
            c=np.array(TABLES['fx_biquad'][p*128+s*8:p*128+s*8+5])/2**20
            assert max(abs(np.roots([1,-c[3],-c[4]])))<1,(p,s)
    print(f'PASS assets: FIR stop {stop:.1f} dB at >=24 kHz, passband ripple {ripple:.4f} dB; stable quantized EQ')

def check_render():
    data=np.loadtxt(SIM/'guitar_fx_render.txt',dtype=np.int64)
    assert data.shape==(24000,5),data.shape
    total=0;spectra=[]
    for amp in range(1,11):
        rows=data[data[:,0]==amp];model=Oversample(amp)
        expected=np.array([model.process(x) for x in rows[:,3]])
        bad=np.flatnonzero(expected!=rows[:,4])
        assert not len(bad),f'amp {amp} integer mismatch sample {bad[0]}: model {expected[bad[0]]}, RTL {rows[bad[0],4]}'
        y=rows[:,2]/2**23
        assert .0001<np.sqrt(np.mean(y*y))<.7
        assert np.max(abs(y))<.9
        spectrum=abs(np.fft.rfft(y[1200:]*np.hanning(1200)))
        spectra.append(spectrum/(np.linalg.norm(spectrum)+1e-20))
        total+=len(rows)
        print(f'  {amp:2}: rms {20*np.log10(np.sqrt(np.mean(y*y))):.2f} dBFS; peak {20*np.log10(max(abs(y))):.2f} dBFS')
    assert np.linalg.norm(spectra[0]-spectra[8])>.05,'TS and Mesa should differ'
    print(f'PASS RTL 4x reference: {total} bit-exact samples, ten distinct voicings')

def check_alias():
    # Same memoryless tanh transfer at base rate vs 4x with idealized second
    # stage omitted: isolate alias suppression, not EQ or cabinet attenuation.
    n=12000;x=.55*np.sin(2*np.pi*10000*np.arange(n)/48000)
    h=np.array(TABLES['fx_fir_down'])/131072
    hu=np.array(TABLES['fx_fir_up'])/131072
    up=np.zeros(n*4);up[::4]=x
    os=np.convolve(np.tanh(np.convolve(up,hu)[:n*4]*10),h)[:n*4:4]
    naive=np.tanh(x*10)
    def aliases(y):
        y=y[1200:10800];f=np.fft.rfftfreq(len(y),1/48000);s=abs(np.fft.rfft(y))
        return float(np.sqrt(sum(s[np.argmin(abs(f-hz))]**2 for hz in (2000,6000,14000,18000,22000)))/s[np.argmin(abs(f-10000))])
    a,b=aliases(naive),aliases(os)
    improvement=20*np.log10(a/b)
    assert improvement>30,improvement
    print(f'PASS isolated 10 kHz tanh alias test: {improvement:.1f} dB reduction (not a full-chain specification)')

def check_modulation():
    data=np.loadtxt(SIM/'guitar_fx_modulation.txt',dtype=np.int64)
    assert data.shape==(48000,3),data.shape
    sine=TABLES['fx_lfo']
    for mode in range(1,5):
        phase=0;wp=0;filled=0;delayed=0;ram=[0]*2048;apx=[0]*4;apy=[0]*4
        rows=data[data[:,0]==mode]
        for i,(_,xin,actual) in enumerate(rows):
            x=int(xin);original=x;motion=sine[phase>>22]*127
            phase=(phase+17896+127*5495)&0xffffffff
            if mode==1:expected=x*(32768-127*128+(motion>>8))>>15
            elif mode in (2,4):
                dq=122880+(motion>>7) if mode==2 else 28672+(motion>>8)
                delay=dq>>8;fraction=dq&255
                ram[wp]=sat(x+(delayed>>2)) if mode==4 else x
                filled=min(2047,filled+1)
                d0=ram[(wp-delay)&2047] if filled>delay+1 else 0
                d1=ram[(wp-delay-1)&2047] if filled>delay+1 else 0
                delayed=sat(d0+((d1-d0)*fraction>>8))
                expected=delayed if mode==2 else sat((x+delayed)>>1)
                wp=(wp+1)&2047
            else:
                a=22000+(motion>>9)
                for s in range(4):
                    y=sat(apx[s]+((apy[s]-x)*a>>15));apx[s]=x;apy[s]=y;x=y
                expected=sat((original+x)>>1)
            assert int(actual)==expected,f'mod {mode}, frame {i}: {actual} != {expected}'
    print('PASS modulation oracle: 48000 bit-exact tremolo/vibrato/phaser/flanger samples')

def check_quiet_tail():
    data=np.loadtxt(SIM/'guitar_fx_tail.txt',dtype=np.int64)
    for amp in (4,10):
        rms=[]
        for magnitude in (1000,100):
            rows=data[(data[:,0]==amp)&(data[:,1]==magnitude)]
            model=Oversample(amp,127)
            expected=np.array([model.process(x) for x in rows[:,2]])
            assert np.array_equal(expected,rows[:,3]),('quiet tail oracle',amp,magnitude)
            y=rows[-2400:,3].astype(float)
            rms.append(np.std(y))
            # Exactly 22 periods, so exclude only the fundamental bin (440 Hz).
            spectrum=abs(np.fft.rfft(y-y.mean()))
            fundamental=spectrum[22]
            unwanted=np.sqrt(np.sum(spectrum**2)-fundamental**2)/fundamental
            assert unwanted<.025,('tail THD+N',amp,magnitude,unwanted)
        drop=20*np.log10(rms[0]/rms[1])
        assert 19<drop<21,('quiet-tail gain discontinuity',amp,drop)
        print(f'PASS quiet tail amp {amp}: 20 dB input reduction -> {drop:.2f} dB output reduction')

if __name__=='__main__':
    check_assets()
    check_alias()
    if '--assets-only' not in sys.argv:
        check_render()
        check_modulation()
        check_quiet_tail()
