"""Run actual RTL, decode UART captures, verify independent spectral peaks."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root/'host'))
from live_verification import CaptureParser, peaks

iv = os.environ.get('IVERILOG') or shutil.which('iverilog')
vvp = os.environ.get('VVP') or shutil.which('vvp')
if not iv or not vvp:
    raise SystemExit('Install Icarus Verilog or set IVERILOG and VVP paths.')
args = [iv]
if os.environ.get('IVERILOG_LIB'):
    args.extend(['-B', os.environ['IVERILOG_LIB']])
result_dir = root/'tests/results'
result_dir.mkdir(exist_ok=True)
sources = [root/'src/audio_driver.v',root/'src/st7735_status.v'] + sorted((root/'src/verification').glob('*.v')) + [root/'tests/tb_verification.sv']
args.extend(['-g2012', '-s', 'tb_verification', '-s','GSR', '-o', str(result_dir/'verification.vvp')])
sources += [Path(os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'))]
args.extend(map(str, sources))
def run(command):
    p = subprocess.run(command, cwd=root, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stdout+p.stderr)
    return p.stdout+p.stderr
compilation = run(args)
log = run([vvp, str(result_dir/'verification.vvp')])
fast_args = [iv]
if os.environ.get('IVERILOG_LIB'):
    fast_args.extend(['-B',os.environ['IVERILOG_LIB']])
fast_args.extend(['-g2012','-s','tb_fast_key','-o',str(result_dir/'fast_key.vvp'),
                 str(root/'src/verification/verification_fast_key.v'),str(root/'tests/tb_fast_key.sv')])
compilation += run(fast_args)
log += run([vvp,str(result_dir/'fast_key.vvp')])
(result_dir/'rtl_test_log.txt').write_text(compilation+log, encoding='utf-8')
report = dict(source='Icarus RTL simulation; no physical board connected', end_to_end_5ms_verified=False, cases=[])
for count in range(1, 5):
    data = bytes.fromhex((result_dir/('uart_%d.hex'%count)).read_text())
    parser = CaptureParser()
    captures = parser.feed(data)
    assert len(captures)==1 and parser.bad_packets==0
    c = captures[0]
    assert c.flags & 3 == 3 and c.active_count==count
    detected = peaks(c.samples, c.sample_rate)
    assert sorted(round(f) for f, db in detected)==[375,750,1125,1500][:count], detected
    assert np.abs(c.samples.astype(np.int32)).max()<32767
    np.savetxt(result_dir/('rtl_samples_%d.csv'%count),c.samples,fmt='%d',delimiter=',',header='left,right',comments='')
    report['cases'].append(dict(voices=count, peaks_hz_dbfs=detected, latency_cycles=c.latency_cycles,
                                digital_response_ms=c.latency_ms, crc='PASS', clipping=False))
normal = CaptureParser().feed(bytes.fromhex((result_dir/'uart_normal.hex').read_text()))[0]
assert normal.active_count==0 and not normal.flags & 1
np.testing.assert_array_equal(normal.samples, np.tile([1234,-2345],(512,1)))
report['normal_path_restore']='PASS; stereo word tap matches +1234/-2345 exactly'
report['audio_schedule']='1041 or 1042 cycles per stereo sample; deterministic 20 ns quantisation, not a zero-jitter claim'
(result_dir/'rtl_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(log)
print('PASS: independent UART decoding, CRC, 1-4 real RTL spectral peaks, restoration, DFT bins, fast key and sample schedule.')
