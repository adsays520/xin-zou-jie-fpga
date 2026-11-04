"""Synthesize and compare kick/peak cores using official Gowin primitives."""
from pathlib import Path
import subprocess, sys
r = Path(__file__).resolve().parents[1]
if '--reuse-netlist' not in sys.argv:
    subprocess.run([sys.executable, str(r/'tests/run_audio_kernels_gate.py'), '--synth-only'], cwd=r, check=True)
subprocess.run([sys.executable, str(r/'tests/run_kernels_iverilog.py')], cwd=r, check=True)
