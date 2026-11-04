"""Fit harmonic SMS controls; recordings are offline inputs, never runtime audio."""
from pathlib import Path
import argparse, json, math, sys, hashlib
from concurrent.futures import ProcessPoolExecutor
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
FS=48000; MODES=16; RANK=12
KNOTS=np.r_[np.arange(64)*32,2048+np.arange(64)*128,
            10240+np.arange(128)*512,75776+np.arange(256)*2048]
NAMES=['C','Cs','D','Ds','E','F','Fs','G','Gs','A','As','B']

def soundfile_module(deps):
    if deps:sys.path.append(str(deps))
    import soundfile
    return soundfile

def peak_hz(power,k,size):
    a,b,c=np.log(power[k-1:k+2]+1e-40)
    d=np.clip(.5*(a-c)/(a-2*b+c+1e-30),-.5,.5)
    return float((k+d)*FS/size)

def harmonic_frequencies(x,key):
    f0=440*2**((key-69)/12);size=262144;n=min(len(x),FS)
    power=abs(np.fft.rfft(x[:n]*np.hanning(n),size))**2
    ff=np.fft.rfftfreq(size,1/FS)
    peaks=np.flatnonzero((power[1:-1]>power[:-2])&(power[1:-1]>=power[2:]))+1
    base=f0;B=.0001 if key<60 else .001
    for iteration in range(3):
        hs=[];values=[];weights=[]
        for h in range(1,min(10,int(21000/f0))+1):
            target=base*h*math.sqrt(1+B*h*h)
            width=max(2.,f0*.25+target*.012)
            candidates=peaks[abs(ff[peaks]-target)<width]
            if len(candidates)==0:continue
            scores=power[candidates]*np.exp(-.5*((ff[candidates]-target)/max(2.,width*.55))**2)
            k=int(candidates[np.argmax(scores)])
            if power[k]<power.max()*1e-4:continue
            hs.append(h*h);values.append((peak_hz(power,k,size)/h)**2)
            weights.append(math.sqrt(float(power[k])))
        if len(hs)>=2:
            a=np.column_stack([np.ones(len(hs)),hs]);w=np.sqrt(np.asarray(weights)/max(weights))
            fit=np.linalg.lstsq(a*w[:,None],np.asarray(values)*w,rcond=1e-8)[0]
            base=float(np.clip(math.sqrt(max(fit[0],1)),f0*.94,f0*1.06))
            B=float(np.clip(fit[1]/max(fit[0],1),0,.02))
    frequencies=[]
    for h in range(1,MODES+1):
        target=base*h*math.sqrt(1+B*h*h)
        if target>=22000:frequencies.append(0.);continue
        width=max(2.,f0*.24+target*.006)
        candidates=peaks[abs(ff[peaks]-target)<width]
        if len(candidates):
            scores=power[candidates]*np.exp(-.5*((ff[candidates]-target)/max(2.,width*.6))**2)
            k=int(candidates[np.argmax(scores)]);target=peak_hz(power,k,size)
        frequencies.append(float(target))
    return np.array(frequencies),base,B

def hammer_fit(residual,key):
    n=min(len(residual),2160);t=np.arange(n)/FS;rise=1-np.exp(-t/.00035)
    spectrum=abs(np.fft.rfft(residual[:n]*np.hanning(n),8192));ff=np.fft.rfftfreq(8192,1/FS)
    pk=np.flatnonzero((spectrum[1:-1]>spectrum[:-2])&(spectrum[1:-1]>=spectrum[2:]))+1
    low=80 if key<84 else max(800,440*2**((key-69)/12)*.7)
    selected=[]
    for k in sorted(pk,key=lambda k:spectrum[k],reverse=True):
        if low<ff[k]<21000 and all(abs(ff[k]-f)>150 for f in selected):selected.append(float(ff[k]))
        if len(selected)==24:break
    if not selected:selected=[1000.]
    matrices=[];descriptions=[]
    for f in selected:
        for tau in (.0015,.0035,.008):
            env=rise*np.exp(-t/tau)
            matrices.append(np.column_stack([env*np.cos(2*np.pi*f*t),env*np.sin(2*np.pi*f*t)]))
            descriptions.append((f,tau))
    normalized=[a/np.maximum(np.sqrt(np.sum(a*a,axis=0)),1e-20) for a in matrices]
    remainder=residual[:n].copy();chosen=[]
    for _ in range(8):
        scores=[-1 if i in chosen else float(np.sum((a.T@remainder)**2)) for i,a in enumerate(normalized)]
        chosen.append(int(np.argmax(scores)))
        design=np.column_stack([matrices[i] for i in chosen])
        coeff=np.linalg.lstsq(design,residual[:n],rcond=1e-6)[0]
        remainder=residual[:n]-design@coeff
    return np.array([[*descriptions[i],*coeff[2*j:2*j+2]] for j,i in enumerate(chosen)])

def analyze_case(args):
    key,vel,sources,cache,deps=args
    target=Path(cache)/f'{key}_{vel}.npz'
    if target.exists():return key,vel
    sf=soundfile_module(deps)
    name=f'INSPiano_Vel{vel:02d}_{NAMES[key%12]}{key//12-1}_01.ogg'
    file=Path(sources)/name;x,fs=sf.read(file,always_2d=True);assert fs==FS
    x=x.mean(axis=1)[:FS*8];x-=np.mean(x)
    frequencies,base,B=harmonic_frequencies(x,key)
    n=len(x);size=1<<(2*n-1).bit_length();small=size//16
    spectrum=np.fft.fft(x,size);bins=np.fft.fftfreq(small)*small
    bandwidth=min(90.,440*2**((key-69)/12)*.25)
    lowpass=np.exp(-(abs(bins)*FS/size/bandwidth)**4)
    controls=np.zeros((MODES,512),dtype=complex)
    measured=np.zeros(MODES);carrier=np.zeros(MODES)
    short=min(n,4800);tt=np.arange(short)/FS;tonal=np.zeros(short)
    for m,f in enumerate(frequencies):
        if not f:continue
        center=round(f*size/FS);f=center*FS/size
        env=2/16*np.fft.ifft(spectrum[(center+bins.astype(np.int64))%size]*lowpass)
        t_index=np.arange(small)*16
        z=np.interp(KNOTS,t_index,env.real)+1j*np.interp(KNOTS,t_index,env.imag)
        z[KNOTS>=n]=0
        # Harmonic presence comes from measured musical components, not noise.
        brightness=1.
        if key>=84 and m>0:brightness=min(1.9,1.15+.18*m)
        elif key<48 and m==0:brightness=1.3
        controls[m]=z*brightness
        measured[m]=f;carrier[m]=f*(440*2**((key-69)/12))/base
        env_short=np.interp(np.arange(short),KNOTS,z.real)+1j*np.interp(np.arange(short),KNOTS,z.imag)
        tonal+=(env_short*np.exp(2j*np.pi*f*tt)).real
    trans=hammer_fit(x[:short]-tonal,key);tr=np.zeros(short)
    for f,tau,a,b in trans:
        tr+=(1-np.exp(-tt/.00035))*np.exp(-tt/tau)*(a*np.cos(2*np.pi*f*tt)+b*np.sin(2*np.pi*f*tt))
    residual=x[:short]-tonal-tr;spec=np.fft.rfft(residual*np.hanning(short));ff=np.fft.rfftfreq(short,1/FS)
    noise=[]
    for band,(lo,hi) in enumerate([(150,1500),(1500,4500),(4500,10000),(10000,22000)]):
        q=np.fft.irfft(spec*((ff>=lo)&(ff<hi)),short)
        amount=.06 if key<60 and band==0 else .18 if band<2 else .4
        noise.append(float(np.sqrt(np.mean(q*q))*amount))
    np.savez_compressed(target,frequency=carrier,controls=controls,transient=trans,noise=noise,
                        measured_frequency=measured,estimated_fundamental=base,inharmonicity=B,
                        frames=n,rms=float(np.sqrt(np.mean(x[1200:min(n,14400)]**2))),
                        source_sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    return key,vel

def compress(cache):
    records=[np.load(cache/f'{k}_{v}.npz') for k in range(21,109) for v in range(1,5)]
    matrix=np.concatenate([np.r_[q['controls'].real,q['controls'].imag] for q in records])
    scales=np.maximum(np.sqrt(np.mean(matrix*matrix,axis=1)),1e-8)
    split=(72-21)*4*MODES*2
    curves=[];weights=np.zeros((len(matrix),RANK));explained=[]
    for lo,hi in [(0,split),(split,len(matrix))]:
        normalized=matrix[lo:hi]/np.sqrt(scales[lo:hi,None])
        gram=normalized.T@normalized;values,vectors=np.linalg.eigh(gram)
        c=vectors[:,-RANK:][:,::-1].T;curves.append(c)
        weights[lo:hi]=matrix[lo:hi]@c.T
        explained.append(float(sum(values[-RANK:])/sum(values)))
    curves=np.array(curves);curve_scale=np.max(abs(curves),axis=2)
    curve_q=np.rint(curves/curve_scale[:,:,None]*2047).astype(np.int64)
    weights[:split]*=curve_scale[0];weights[split:]*=curve_scale[1]
    samples=np.arange(1200,14400,2);t=samples/FS
    gains=[]
    for bank,record in enumerate(records):
        group=0 if bank//4+21<72 else 1
        row=bank*MODES*2
        z=(weights[row:row+MODES]@curve_q[group]/2047)+1j*(weights[row+MODES:row+MODES*2]@curve_q[group]/2047)
        y=np.zeros(len(t))
        for m,f in enumerate(record['frequency']):
            env=np.interp(samples,KNOTS,z[m].real)+1j*np.interp(samples,KNOTS,z[m].imag)
            y+=(env*np.exp(2j*np.pi*f*t)).real
        for f,tau,a,b in record['transient']:
            y+=(1-np.exp(-t/.00035))*np.exp(-t/tau)*(a*np.cos(2*np.pi*f*t)+b*np.sin(2*np.pi*f*t))
        target=float(records[(bank//4)*4+2]['rms'])
        gains.append(target/max(float(np.sqrt(np.mean(y*y))),1e-8))
    # Common conservative trim; all layer corrections apply to synthesis parameters.
    gains=np.array(gains)*.6
    out=ROOT/'src/piano/sms';out.mkdir(exist_ok=True)
    wrows=[];freqs=[];transwords=[];noisewords=[]
    for bank,r in enumerate(records):
        row=bank*MODES*2
        for m,f in enumerate(r['frequency']):
            values=np.r_[weights[row+m],weights[row+MODES+m]]*gains[bank]
            exponent=max(-23,int(math.ceil(math.log2(max(float(max(abs(values))),1e-10)/127))))
            shift=23+exponent;assert 0<=shift<=31
            q=np.rint(values/(2.**exponent)).astype(np.int64);assert max(abs(q))<=127
            wrows.append(sum((int(v)&255)<<(8*j) for j,v in enumerate(q)))
            freqs.append((shift<<27)|round(float(f)/FS*(1<<27)))
        for f,tau,re,im in r['transient']:
            radius=math.exp(-1/(tau*FS));theta=2*math.pi*f/FS
            a=round(radius*math.cos(theta)*65536);b=round(radius*math.sin(theta)*65536)
            re=float(re)*gains[bank];im=-float(im)*gains[bank]
            exponent=max(0,min(3,int(math.ceil(math.log2(max(abs(re),abs(im),1e-10))/2))))
            re=round(re*8192/(4**exponent));im=round(im*8192/(4**exponent))
            assert -8192<=re<8192 and -8192<=im<8192,(bank,'transient bound')
            transwords.append(((a&131071)<<47)|((b&131071)<<30)|((re&16383)<<16)|((im&16383)<<2)|exponent)
        noise=0
        for m,a in enumerate(r['noise']):
            radius=math.exp(-[5500,7500,12000,16000][m]/FS)
            q=round(float(a)*gains[bank]*32768*math.sqrt(6*(1-radius*radius)));assert q<32768
            noise|=q<<(16*m)
        noisewords.append(noise)
    basis=[sum((int(curve_q[group,j,k])&4095)<<(12*j) for j in range(RANK)) for group in range(2) for k in range(512)]
    def save(file,values,width):file.write_text(''.join(f'{v:0{width}x}\n' for v in values),encoding='ascii')
    save(out/'weights.hex',wrows,48);save(out/'frequency.hex',freqs,8)
    save(out/'curves.hex',basis,36);save(out/'transient.hex',transwords,16);save(out/'noise.hex',noisewords,16)
    image=[]
    for bank in range(352):
        image.extend(wrows[bank*16+m]|(freqs[bank*16+m]<<192) for m in range(16))
        image.extend(transwords[bank*8+m] for m in range(8));image.append(noisewords[bank])
    ddr=ROOT/'src/piano/sms_ddr';ddr.mkdir(exist_ok=True);save(ddr/'bank_image.hex',image,64)
    manifest=dict(format_version='harmonic_sms_ddr_v1',keys=88,velocity_layers=4,voices=16,
                  tonal_modes=16,transient_modes=8,noise_modes=4,rank=12,recordings_played=False,
                  control_knot_samples=KNOTS.tolist(),svd_explained_energy=explained,
                  boot_records=len(image),ddr_base_native_words=0x100000,bytes_in_ddr=len(image)*32,
                  hardware_listening_verified=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (ddr/'analysis_sources.json').write_text(json.dumps({str(k):str(r['source_sha256']) for k,r in enumerate(records)},indent=2))
    print('PASS fitted harmonic DDR SMS bank',manifest,flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sources',type=Path,required=True)
    ap.add_argument('--deps',type=Path);ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--compress-only',action='store_true');args=ap.parse_args()
    cache=ROOT/'tests/runtime_temp/harmonic_sms';cache.mkdir(parents=True,exist_ok=True)
    if not args.compress_only:
        jobs=[(k,v,str(args.sources),str(cache),str(args.deps) if args.deps else '') for k in range(21,109) for v in range(1,5)]
        with ProcessPoolExecutor(args.workers) as pool:
            for k,v in pool.map(analyze_case,jobs):print('Analyzed harmonic SMS',k,v,flush=True)
    compress(cache)

if __name__=='__main__':main()
