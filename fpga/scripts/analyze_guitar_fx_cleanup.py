"""Reproducible recording measurements and before/after quiet-tail regression.

No denoising or subjective listening claims; MP3 measurements include the
recording chain. Plots are diagnostic, not proof of analog amp equivalence.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
import numpy as np
import soundfile as sf
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from check_guitar_fx import Oversample, ROOT


def load_old_model():
    folder=ROOT/'impl/fx_before_cleanup_20260929'
    def module(name,path):
        spec=importlib.util.spec_from_file_location(name,path)
        result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
        return result
    original=sys.modules['generate_guitar_fx']
    try:
        sys.modules['generate_guitar_fx']=module('old_fx_assets',folder/'generate_guitar_fx.py')
        return module('old_fx_check',folder/'check_guitar_fx.py').Oversample
    finally:
        sys.modules['generate_guitar_fx']=original


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('recording',type=Path)
    args=parser.parse_args()
    out=ROOT/'impl/fx_cleanup_analysis';out.mkdir(exist_ok=True)
    audio,fs=sf.read(args.recording,always_2d=True);mono=audio.mean(axis=1)
    def db(x):return float(20*np.log10(max(float(x),1e-15)))
    report={'recording':str(args.recording),'sample_rate':fs,'seconds':len(audio)/fs,
            'peak_dbfs':db(np.max(abs(audio))),'segments':[],'tail_test':[]}
    for begin,end in [(1,9),(9,13),(14,22),(23,26),(26,32)]:
        x=mono[begin*fs:end*fs]
        f,p=signal.welch(x,fs,nperseg=8192)
        report['segments'].append({'seconds':[begin,end],'rms_dbfs':db(np.std(x)),
            'above_4k_energy_db':float(10*np.log10(p[f>=4000].sum()/p.sum()))})
    old=load_old_model()
    for amp in (4,10):
        for label,model_class in [('before',old),('after',Oversample)]:
            rms=[]
            for amplitude in (1000,100):
                model=model_class(amp,127)
                x=(amplitude*np.sin(2*np.pi*440*np.arange(4800)/48000)).astype(int)
                y=np.array([model.process(v) for v in x])[2400:]
                rms.append(np.std(y))
            report['tail_test'].append({'amp':amp,'version':label,'input_drop_db':20,
                                       'output_drop_db':db(rms[0]/rms[1])})
    fig,ax=plt.subplots(2,1,figsize=(12,7),layout='constrained')
    step=240
    ax[0].plot(np.arange(0,len(mono),step)/fs,mono[::step],lw=.6,color='#237b9f')
    ax[0].set(ylabel='Recorded amplitude',xlim=(0,len(mono)/fs),title='User recording (includes recorder/environment noise)')
    f,t,z=signal.stft(mono,fs,nperseg=2048,noverlap=1536)
    select=f<=10000
    im=ax[1].pcolormesh(t,f[select],20*np.log10(abs(z[select])+1e-12),vmin=-90,vmax=-25,shading='auto',cmap='magma')
    ax[1].set(xlabel='Time (s)',ylabel='Frequency (Hz)')
    fig.colorbar(im,ax=ax[1],label='dBFS (STFT magnitude)')
    fig.savefig(out/'recording_spectrum.png',dpi=140);plt.close(fig)
    (out/'measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    source=ROOT/'impl/guitar_fx_string_verify/guitar_fx_string.txt'
    if source.exists():
        data=np.loadtxt(source,dtype=np.int64)
        sf.write(out/'guitar_fx_cleanup_rtl_preview.wav',data[:,2]/2**23,48000,subtype='PCM_24')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
