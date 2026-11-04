"""Run the actual C modules with mocked hardware/RTOS; requires Windows TinyCC."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--tcc', default=os.environ.get('TOUCH_TEST_TCC') or shutil.which('tcc'))
args = parser.parse_args()
if not args.tcc:
    parser.error('Pass --tcc with tcc.exe, or set TOUCH_TEST_TCC')
root = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env['TOUCH_TEST_TCC'] = str(Path(args.tcc).resolve())
tests = root / 'fpga/esp32S3/Guitar_Controller_R15/tests'
raise SystemExit(subprocess.call([sys.executable, '-m', 'unittest', 'discover',
                                 '-s', str(tests), '-p', '*runtime.py', '-v'], env=env))
