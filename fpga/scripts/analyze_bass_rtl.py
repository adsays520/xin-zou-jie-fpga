"""Measure actual RTL samples, check pitch, and compare isolated voices bitwise."""
from pathlib import Path
import json
import wave
import numpy as np
from generate_bass_assets import tables, FS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'verification'
bright, dark, pitches = tables()


def one_voice(step, frames=130000):
    result = []
    phase = amplitude = 0
    brightness = 32768
    target = 127 << 16
    for age in range(frames):
        if age < 64:
            amplitude = min(target, amplitude + (target >> 6))
        elif age >= 96000:
            amplitude = 0 if amplitude < 4096 else amplitude - (amplitude >> 10)
        elif age < 4800:
            amplitude -= amplitude >> 14
        else:
            amplitude -= amplitude >> 17
        address, fraction = phase >> 21, (phase >> 5) & 65535
        adjacent = (address + 1) & 2047
        b = bright[address] + (((bright[adjacent] - bright[address]) * fraction) >> 16)
        d = dark[address] + (((dark[adjacent] - dark[address]) * fraction) >> 16)
        value = d + (((b - d) * brightness) >> 15)
        result.append((value * amplitude) >> 17)
        phase = (phase + step) & 0xffffffff
        brightness = 0 if brightness < 512 else brightness - (brightness >> 11)
    return np.array(result, dtype=np.int64)


def frequency(samples, expected):
    signal = samples[5000:53000].astype(float)
    length = 2**20
    spec = np.abs(np.fft.rfft(signal * np.hanning(len(signal)), length))
    lo, hi = int(expected*.98/FS*length), int(expected*1.02/FS*length)+1
    index = lo + np.argmax(spec[lo:hi])
    # Log-parabolic interpolation, much finer than one FFT bin.
    y0, y1, y2 = np.log(spec[index-1:index+2])
    correction = .5*(y0-y2)/(y0-2*y1+y2)
    return float((index+correction)*FS/length)


def save_wave(name, samples):
    pcm = np.clip(samples >> 8, -32768, 32767).astype('<i2')
    with wave.open(str(OUT / name), 'wb') as file:
        file.setnchannels(1); file.setsampwidth(2); file.setframerate(FS)
        file.writeframes(pcm.tobytes())


report = {}
for scenario, label in [(0,'E1'),(1,'four_strings'),(2,'rapid_poly'),(3,'rapid_mono'),(4,'highest_G_fret20')]:
    file = OUT / f'bass_rtl_{scenario}.txt'
    assert file.exists(), f'Missing actual RTL scenario {scenario}'
    samples = np.loadtxt(file, dtype=np.int64)
    assert np.max(np.abs(samples)) <= 7000000
    assert np.all(samples[-100:] == 0), 'Residual digital noise at tail'
    assert np.all(samples[:110] == 0), 'Power-on/upper strings not silent'
    item = {'frames':len(samples),'peak_q23':int(np.max(np.abs(samples))),
            'peak_dbfs':float(20*np.log10(max(1,np.max(np.abs(samples)))/8388608)),
            'tail_last_100_exact_zero':True}
    segment = samples[12000:24000].astype(float)
    window = np.hanning(len(segment))
    spectrum = np.fft.rfft(segment*window)
    high = np.fft.rfftfreq(len(segment),1/FS) >= 6000
    high_rms = np.sqrt(2*np.sum(np.abs(spectrum[high])**2)/(len(segment)*np.sum(window**2)))
    item['steady_6khz_above_rms_dbfs'] = float(20*np.log10(max(high_rms,1e-20)/8388608))
    if scenario in (0,4):
        step = pitches[96] if scenario==0 else pitches[20]
        expected = np.concatenate((np.zeros(110,dtype=np.int64),one_voice(step),np.zeros(100,dtype=np.int64)))
        assert len(samples)==len(expected)
        assert np.array_equal(samples,expected), f'Bit mismatch {np.flatnonzero(samples!=expected)[:10]}'
        item['integer_reference_bit_exact'] = True
        target = 41.205 if scenario==0 else 98*2**(20/12)
        measured = frequency(samples,target)
        item.update(expected_hz=target,measured_hz=measured,pitch_error_cents=float(1200*np.log2(measured/target)))
        assert abs(item['pitch_error_cents']) < .2
    report[label] = item
    save_wave(f'bass_actual_rtl_{label}.wav',samples)

# All 84 pitch-ROM values are checked independently against UI convention.
for row,base in enumerate((98,73.415,55,41.205)):
    for fret in range(21):
        err = abs(pitches[row*32+fret]*FS/2**32-base*2**(fret/12))
        assert err<FS/2**33+1e-10
report['pitch_table_84_notes'] = 'PASS'
(OUT / 'bass_audio_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
