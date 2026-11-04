"""Verify single-pluck pitch DSP against the original guitar model.
The memories here are behavioral; verify_merged_iverilog.py separately runs
actual Gowin memory primitives, UART, 32-voice context switching and final output.
No recordings are used as a sound source by the FPGA or GUI.
"""
from pathlib import Path
import os
import subprocess
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tests/results'
OUT.mkdir(parents=True, exist_ok=True)
TOOLS = Path(os.environ.get('BASS_IVERILOG_HOME', str(ROOT.parent.parent / 'tmp/sim_tools/mingw64')))
ENV = os.environ.copy()
ENV['PATH'] = str(TOOLS / 'bin') + os.pathsep + ENV['PATH']
ENV['TEMP'] = ENV['TMP'] = str(ROOT / 'tests/runtime_temp')


def run(command, log):
    result = subprocess.run(command, cwd=ROOT, env=ENV, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=300)
    output = result.stdout + result.stderr
    (OUT / log).write_text(output, encoding='utf-8')
    assert result.returncode == 0, (result.returncode, output[-5000:])
    return output


def peak(samples, target=None):
    values = samples.astype(float)
    values -= values.mean()
    length = 1
    while length < len(values) * 4:
        length *= 2
    spectrum = np.abs(np.fft.rfft(values * np.hanning(len(values)), length))
    frequencies = np.fft.rfftfreq(length, 1 / 48000)
    candidates = np.arange(1, len(spectrum) - 1)
    if target is not None:
        candidates = candidates[(frequencies[candidates] > target * .85) &
                                (frequencies[candidates] < target * 1.15)]
    index = candidates[np.argmax(spectrum[candidates])]
    y = np.log(np.maximum(spectrum[index - 1:index + 2], 1e-30))
    offset = (y[0] - y[2]) / (2 * (y[0] - 2 * y[1] + y[2]))
    return float((index + offset) * 48000 / length)


def instantaneous_frequency(samples, center):
    length = len(samples)
    spectrum = np.fft.fft(samples.astype(float))
    frequency = np.fft.fftfreq(length, 1 / 48000)
    # Extract one harmonic and its modulation sidebands; ignore negative bins.
    band = (frequency > center * .85) & (frequency < center * 1.15)
    analytic = np.fft.ifft(spectrum * band * 2)
    phase = np.unwrap(np.angle(analytic))
    result = np.diff(phase) * 48000 / (2 * np.pi)
    return np.convolve(result, np.ones(240) / 240, mode='same')


# These files contain pitch ratios, not audio samples.
frames = np.arange(36000)
slide = np.minimum(1200, np.maximum(0, frames - 6000) * 1200 / 18000)
vibrato = 35 * np.sin(2 * np.pi * 5 * (frames - 6000) / 48000)
for label, cents in [('slide', slide), ('vibrato', vibrato)]:
    ratios = np.rint(1048576 * 2 ** (cents / 1200)).astype(int)
    (ROOT / f'tests/ratio_{label}_q20.mem').write_text(''.join(f'{r:06x}\n' for r in ratios), encoding='ascii')

sources = ['tests/tb_pitch_core.sv', 'tests/pitch_ram_models.v',
           'tests/ref/pitch_legacy_core.v', 'src/poly32/guitar_voice_tdm_core.v',
           'src/guitar_note_params.v']
if os.name == 'nt':
    # The MSYS2 13.0 driver crashes during cleanup after combined compilation.
    # Its preprocessing path and the compiler backend both exit successfully
    # when called separately. Do not ignore a nonzero exit from either stage.
    run([str(TOOLS / 'bin/iverilog.exe'), '-E', '-B', str(TOOLS / 'lib/ivl'),
         '-g2012', '-o', 'tests/runtime_temp/pitch_preprocessed.v', *sources],
        'pitch_preprocess.log')
    config = ['root:tb_pitch_core', f'basedir:{TOOLS / "lib/ivl"}']
    config += [f'module:{TOOLS / "lib/ivl" / (name + ".vpi")}' for name in
               ('system', 'vhdl_sys', 'vhdl_textio', 'v2005_math', 'va_math', 'v2009')]
    config += ['generation:2012', 'generation:no-specify', 'generation:no-interconnect',
               'generation:assertions', 'generation:xtypes', 'generation:io-range-error',
               'generation:no-strict-ca-eval', 'generation:no-strict-expr-width',
               'generation:shared-loop-index', 'generation:no-verilog-ams',
               'generation:icarus-misc', 'warnings:n', 'ignore_missing_modules:false',
               'out:tests/results/pitch_core.vvp', 'iwidth:32', 'widthcap:65536']
    (OUT / 'pitch_ivl_config.txt').write_text('\n'.join(config) + '\n', encoding='utf-8')
    run([str(TOOLS / 'lib/ivl/ivl.exe'), '-C', 'tests/results/pitch_ivl_config.txt',
         '-C', str(TOOLS / 'lib/ivl/vvp.conf'), '--',
         'tests/runtime_temp/pitch_preprocessed.v'], 'pitch_core_compile.log')
else:
    run([str(TOOLS / 'bin/iverilog'), '-g2012', '-s', 'tb_pitch_core',
         '-o', 'tests/results/pitch_core.vvp', *sources], 'pitch_core_compile.log')


report = []
cases = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 0, 0),
         (1, 5, 3), (4, 5, 5), (2, 5, 0)]
for scenario, string_index, fret in cases:
    name = f'pitch_core_{scenario}_s{string_index + 1}_f{fret}'
    log = run([str(TOOLS / 'bin/vvp.exe'), 'tests/results/pitch_core.vvp',
               f'+SCENARIO={scenario}', f'+STRING={string_index}', f'+FRET={fret}'], name + '.log')
    assert 'PASS pitch core' in log
    data = np.loadtxt(OUT / 'pitch_core_samples.txt', dtype=np.int64)
    np.save(OUT / (name + '.npy'), data)
    late = data[data[:, 0] >= 26000]
    reference = peak(late[:, 2])
    rms = float(np.sqrt(np.mean(late[:, 1].astype(float) ** 2)))
    assert rms > 50 and np.max(np.abs(data[:, 1])) < 8388607
    case = dict(scenario=scenario, string=string_index + 1, fret=fret,
                reference_hz=reference, rms_q23=rms, note_on_count=1,
                memory='behavioral; separate full-top test uses Gowin primitives', finite=True)
    if scenario == 0:
        np.testing.assert_array_equal(data[:, 1], data[:, 2])
        case['bypass_exact'] = True
    elif scenario in (1, 2, 4):
        cents = {1: 200, 2: 1200, 4: -200}[scenario]
        target = reference * 2 ** (cents / 1200)
        output = peak(late[:, 1], target)
        error = float(1200 * np.log2(output / target))
        assert abs(error) < 10, (name, error)
        case.update(target_hz=target, output_hz=output, error_cents=error)
    elif scenario == 3:
        start = data[data[:, 0] >= 6000]
        new_frequency = instantaneous_frequency(start[:, 1], reference)
        old_frequency = instantaneous_frequency(start[:, 2], reference)
        trim = 2400
        cents = 1200 * np.log2(new_frequency[trim:-trim] / old_frequency[trim:-trim])
        time = np.arange(len(new_frequency))[trim:-trim] / 48000
        design = np.column_stack((np.ones(len(time)), np.sin(2 * np.pi * 5 * time),
                                  np.cos(2 * np.pi * 5 * time)))
        fit = np.linalg.lstsq(design, cents, rcond=None)[0]
        depth = float(np.hypot(fit[1], fit[2]))
        residual_rms = float(np.sqrt(np.mean((cents - design @ fit) ** 2)))
        assert abs(fit[0]) < 10 and 25 < depth < 45 and residual_rms < 10
        case.update(center_error_cents=float(fit[0]), measured_depth_cents=depth,
                    requested_depth_cents=35, requested_rate_hz=5,
                    sinusoid_residual_rms_cents=residual_rms)
    report.append(case)
    print(json.dumps(case), flush=True)

(OUT / 'pitch_audio_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('PASS: bypass exact; one-pluck up/down pitch and vibrato verified on model-generated audio.', flush=True)
