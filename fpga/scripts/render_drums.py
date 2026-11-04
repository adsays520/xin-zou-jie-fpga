"""Algorithmic reference previews. No input WAVs or recorded sample assets."""
from pathlib import Path
import sys
import json
import wave
import numpy as np
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))
from drum_patterns import PRESETS, preset, NAMES

RATE = 48000

def voice_wave(voice, kit, length=RATE * 3):
    params = np.array([int(x,16) for x in (ROOT / "src/drums/rom/params.hex").read_text().split()], dtype=np.int64)
    base = (kit * 16 + voice) * 8
    cfg = int(params[base + 7]); b,n,p,lp,hp = [(cfg >> shift) & 15 for shift in (0,4,8,12,16)]
    t = np.arange(length)
    env_b = (1 - 2.**-b)**t; env_n = (1 - 2.**-n)**t
    excursion = params[base + 6] * (1 - 2.**-p)**t
    phases = np.empty((6,length))
    for osc in range(6):
        phases[osc] = np.cumsum(params[base + osc] + (excursion if osc == 0 else 0)) / 2.**32
    sine = np.sin(2 * np.pi * phases)
    modal = sine[0] + .5*sine[1] + .125*np.sum(sine[2:], axis=0)
    metallic = np.sum(np.where((phases % 1) >= .5, -.25, .25), axis=0)
    random = np.random.default_rng(20260929 + voice * 17 + kit).uniform(-1,1,length)
    cymbal = voice in (2,3,5,6)
    exciter = random + metallic*.5 if cymbal else random
    low = lfilter([2.**-lp], [1, -(1 - 2.**-lp)], exciter)
    dc = lfilter([2.**-hp], [1, -(1 - 2.**-hp)], low)
    noise = low - dc
    bright = exciter - low
    if voice == 0: body,noisy = modal, noise*.5
    elif voice == 1: body,noisy = modal*.5,noise
    elif voice in (2,3): body,noisy = np.zeros(length),bright
    elif voice == 4:
        body,noisy = np.zeros(length),noise
        env_n[:] = 0
        for start in (0,480,960):
            end = min(start+480,length)
            env_n[start:end] = env_b[start] * (1 - 2.**-7)**np.arange(end-start)
        env_n[1440:] = env_n[1439] * (1 - 2.**-n)**np.arange(1,length-1439)
    elif voice == 5: body,noisy = modal/64,bright+noise*.5
    elif voice == 6: body,noisy = modal/32,bright+noise*.5
    elif voice in (7,8,9): body,noisy = modal,noise*.25
    elif voice == 10: body,noisy = modal,noise*.5
    else: body,noisy = metallic*.5,np.zeros(length)
    result = (body*env_b + noisy*env_n) / 8
    result[:8] *= .125; result[8:16] *= .25; result[16:32] *= .5
    result[-240:] *= np.linspace(1,0,240)
    return result

def write(path, data):
    if data.ndim == 1: data=np.column_stack((data,data))
    pcm=np.rint(np.clip(data,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(pcm.tobytes())

def main():
    out = ROOT / "previews/drums_v3";out.mkdir(parents=True,exist_ok=True)
    waves = {(k,v): voice_wave(v,k) for k in range(3) for v in range(12)}
    manifest={"kind":"algorithmic reference; not board recording; uses same modal/envelope parameters with floating point filters and PRNG", "sample_rate":RATE, "presets":[]}
    for i,name in enumerate(PRESETS):
        pattern=preset(name)
        steps=np.rint(np.cumsum([0]+[pattern.step_seconds(s) for s in range(64)])*RATE).astype(int)
        tracks=np.zeros((12,steps[-1]+RATE*3))
        for v in range(12):
            for s,value in enumerate(pattern.cells[v]):
                if not value:continue
                start=steps[s]; source=waves[pattern.kit,v]*(value/128)*(pattern.levels[v]/128)
                # One voice per instrument: a retrigger restarts its envelope.
                tracks[v,start:]=0;tracks[v,start:start+len(source)]=source
                if v==2:tracks[3,start:]=0
        # Apply closed-hat choke after assembling the open-hat lane.
        for s,value in enumerate(pattern.cells[2]):
            if value:
                start=steps[s]
                next_open=[steps[j] for j in range(s+1,64) if pattern.cells[3][j]]
                end=next_open[0] if next_open else tracks.shape[1]
                tracks[3,start:end]=0
        left=tracks.copy();right=tracks.copy();left[[3,6,9]]*=.5;right[[2,5,7]]*=.5
        audio=np.column_stack((left.sum(axis=0),right.sum(axis=0)))
        path=out/f"{i+1:02d}_preset.wav";write(path,audio)
        manifest['presets'].append({"file":path.name,"name":name,"bpm":pattern.bpm,"swing":pattern.swing,"peak":float(np.max(np.abs(audio)))})
        pattern.save(out/f"{i+1:02d}_pattern.json")
    # A full solo kit, separated by a small gap, for comparison and tuning.
    solos=[]
    for v in range(12): solos.extend((waves[0,v]*.78,np.zeros(RATE//4)))
    write(out/'00_solo_kit.wav',np.concatenate(solos))
    # Short focused reference for hearing the four revised cymbal voices.
    cymbals=[]
    for v in (2,3,5,6): cymbals.extend((waves[0,v]*.78,np.zeros(RATE//4)))
    write(out/'00_cymbals_only.wav',np.concatenate(cymbals))
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Generated {len(PRESETS)} synthesized reference grooves and a solo kit in {out}")

if __name__=='__main__':main()
