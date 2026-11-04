"""Verify the current algorithmic drum core."""
import sys,runpy
from pathlib import Path
scripts=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(scripts))
runpy.run_path(str(scripts/"verify_synth_drums.py"),run_name="__main__")
