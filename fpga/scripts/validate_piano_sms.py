"""Actual SMS RTL regression and independent fixed-point reference renderer."""
from pathlib import Path
import argparse,json,subprocess,os,hashlib,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/sms_validation'
PARAMETER_DIR=ROOT/'src/piano/sms'
MODES=16;RANK=12
def signed(n,bits):return (n^(1<<(bits-1)))-(1<<(bits-1))
def words(name):return [int(x,16) for x in (PARAMETER_DIR/name).read_text().split()]
def read_raw(path):
    b=np.frombuffer(path.read_bytes(),dtype=np.uint8).reshape(-1,3).astype(np.int64)
    q=b[:,0]|(b[:,1]<<8)|(b[:,2]<<16)
    return (q^8388608)-8388608
def write_wav(path,q):
    with wave.open(str(path),'wb') as f:
        f.setparams((1,2,48000,0,'NONE','not compressed'))
        f.writeframes(np.clip(q>>8,-32768,32767).astype('<i2').tobytes())
def reference(key,velocity,n,return_stems=False,envelope_times=None,tonal_mode_gains=None):
    bank=(key-21)*4+(0 if velocity<48 else 1 if velocity<80 else 2 if velocity<112 else 3)
    weight=words('weights.hex');freq=words('frequency.hex');curves=words('curves.hex');sine=words('sine.hex')
    sine=np.array([signed(q,18) for q in sine],dtype=np.int64)
    knots=np.r_[np.arange(64)*32,2048+np.arange(64)*128,10240+np.arange(128)*512,75776+np.arange(256)*2048]
    times=np.arange(n) if envelope_times is None else np.asarray(envelope_times,dtype=np.int64)
    assert len(times)==n and np.all(times>=0)
    idx=np.minimum(np.searchsorted(knots,times,side='right')-1,511)
    nextidx=np.minimum(idx+1,511)
    den=np.maximum(1,knots[nextidx]-knots[idx]);frac=np.where(idx==511,0,((times-knots[idx])*2048)//den)
    group=0 if key<72 else 512
    basis=np.empty((RANK,n),dtype=np.int64)
    for j in range(RANK):
        table=np.array([signed((q>>(12*j))&4095,12) for q in curves[group:group+512]],dtype=np.int64)
        basis[j]=table[idx]+((table[nextidx]-table[idx])*frac>>11)
    y=np.zeros(n,dtype=np.int64)
    for m in range(MODES):
        w=weight[bank*MODES+m];f=freq[bank*MODES+m];step=f&((1<<27)-1);shift=f>>27
        re=np.array([signed((w>>(8*j))&255,8) for j in range(RANK)],dtype=np.int64)@basis
        im=np.array([signed((w>>(8*(j+RANK)))&255,8) for j in range(RANK)],dtype=np.int64)@basis
        re=(re<<shift)>>11;im=(im<<shift)>>11
        address=((np.arange(n,dtype=np.int64)*step)&((1<<27)-1))>>17
        component=(re*sine[(address+256)&1023]-im*sine[address])>>17
        if tonal_mode_gains is not None:
            component=(component*int(round(tonal_mode_gains[m]*65536)))>>16
        y+=component
    tonal=y.copy();transient_stem=np.zeros(n,dtype=np.int64);noise_stem=np.zeros(n,dtype=np.int64)
    trans=words('transient.hex')[bank*8:bank*8+8];noise=words('noise.hex')[bank]
    aa=[signed((q>>47)&131071,17) for q in trans]+[58036,51789,31071,-23480]
    bb=[signed((q>>30)&131071,17) for q in trans]+[6869,21452,40493,40668]
    re=[signed((q>>16)&16383,14)<<(10+2*(q&3)) for q in trans]+[0]*4
    im=[signed((q>>2)&16383,14)<<(10+2*(q&3)) for q in trans]+[0]*4
    amplitudes=[signed((noise>>(16*j))&65535,16) for j in range(4)]
    rng=0x51a73b19;ng=0xffffffff;rise=0;maximum=0
    for frame in range(n):
        value=0;hammer_value=0;noise_value=0
        for m in range(12):
            bit=((rng>>31)^(rng>>21)^(rng>>1)^rng)&1
            rng=((rng<<1)|bit)&0xffffffff
            stochastic=0 if m<8 else (signed(rng>>16,16)*amplitudes[m-8]*(ng>>16))>>7
            r=(re[m]*aa[m]-im[m]*bb[m]+stochastic+32768)>>16
            i=(re[m]*bb[m]+im[m]*aa[m]+32768)>>16
            assert -(1<<31)<=r<1<<31 and -(1<<31)<=i<1<<31,(key,velocity,frame,m,r,i)
            re[m],im[m]=r,i
            component=(r*(rise if m<8 else 65535))>>16
            value+=component
            if m<8:hammer_value+=component
            else:noise_value+=component
        y[frame]+=value
        transient_stem[frame]=hammer_value;noise_stem[frame]=noise_value
        rise=65535 if rise>=65512 else rise+(((65535-rise)*3787)>>16)+1
        loss=(ng>>11)+1;ng=max(0,ng-loss)
    gain=(65535*words('velocity.hex')[velocity])>>15
    y=y*gain>>16
    assert np.max(abs(y))<8388608,(key,velocity,'output overflow',np.max(abs(y)))
    if return_stems:
        return dict(total=y,tonal=tonal*gain>>16,transient=transient_stem*gain>>16,noise=noise_stem*gain>>16)
    return y
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--iverilog',type=Path,required=True)
    ap.add_argument('--quick',action='store_true');ap.add_argument('--reference-only',action='store_true');args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    exe=args.iverilog.resolve();env=os.environ.copy();env['PATH']=str(exe.parent)+os.pathsep+env['PATH']
    env['TMP']=env['TEMP']=str(OUT)
    invocation=[str(exe),'-B',str(exe.parent.parent/'lib/ivl'),'-g2012','-s','tb_piano_physical','-o',str(OUT/'piano.vvp'),
                'src/piano/piano_wavetable16_tdm.v','src/piano/piano_soundboard.v','tests/piano/tb_piano_physical.sv']
    if not args.reference_only:subprocess.run(invocation,cwd=ROOT,env=env,check=True)
    records=[]
    for key in ([96] if args.quick else [21,60,84,96,108]):
        frames=512 if args.quick else 24000
        raw=OUT/f'{key}.raw'
        if not args.reference_only:
            result=subprocess.run([str(exe.parent/'vvp.exe'),str(OUT/'piano.vvp'),f'+KEY={key}','+VEL=110',f'+FRAMES={frames}',f'+OUT={raw}'],
                                  cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
            print(result.stdout,flush=True);(OUT/f'{key}.log').write_text(result.stdout)
            assert result.returncode==0 and 'PASS piano' in result.stdout and 'ERROR' not in result.stdout
        q=read_raw(raw);expected=reference(key,110,min(len(q),1024))
        assert np.array_equal(q[:len(expected)],expected),(key,'integer mismatch',np.flatnonzero(q[:len(expected)]!=expected)[:8].tolist())
        board=read_raw(Path(str(raw)+'.board')).reshape(-1,2)
        assert np.array_equal(board[:,0],q) and np.array_equal(board[:,1],q)
        records.append(dict(key=key,frames=len(q),peak=float(np.max(abs(q))/8388608),integer_reference_exact=True,stereo_unity_exact=True))
    result=dict(passed=True,records=records,hardware_listening_verified=False)
    (OUT/'result.json').write_text(json.dumps(result,indent=2))
    print('PASS actual RTL versus independent integer SMS renderer',flush=True)
if __name__=='__main__':main()
