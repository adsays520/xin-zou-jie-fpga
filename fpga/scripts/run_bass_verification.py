"""Compile and execute actual RTL scenarios with a workspace-only simulator."""
from pathlib import Path
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(os.environ.get('BASS_IVERILOG_HOME', str(ROOT.parent / 'bass_tools' / 'mingw64')))
env = os.environ.copy()
env['PATH'] = str(TOOLS / 'bin') + os.pathsep + env['PATH']
out = ROOT / 'verification'
out.mkdir(exist_ok=True)
command = [str(TOOLS/'bin/iverilog.exe'), '-g2012', '-s', 'bass_tb',
           '-o', 'verification/bass_tb.vvp', 'scripts/bass_tb.v',
           'src/bass/bass_poly8.v', 'src/poly32/poly32_bus_manager.v']
compiled = subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,errors='replace')
(out/'iverilog_compile.log').write_text(compiled.stdout+compiled.stderr,encoding='utf-8')
assert compiled.returncode == 0 and 'Failed to open' not in compiled.stderr, compiled.stderr


def scenario(number):
    process = subprocess.run([str(TOOLS/'bin/vvp.exe'),'verification/bass_tb.vvp',
                              f'+SCENARIO={number}'],cwd=ROOT,env=env,
                             capture_output=True,text=True,errors='replace',timeout=900)
    log = process.stdout+process.stderr
    (out/f'rtl_scenario_{number}.log').write_text(log,encoding='utf-8')
    print(log.strip(),flush=True)
    assert process.returncode == 0 and f'PASS scenario={number}' in log, log


with ThreadPoolExecutor(max_workers=2) as executor:
    list(executor.map(scenario,range(5)))
print('All five actual RTL scenarios PASS.',flush=True)
