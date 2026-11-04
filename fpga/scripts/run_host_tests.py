"""Run UI/protocol regressions with writable workspace temporary files."""
from pathlib import Path
import sys
import hashlib,json
import tempfile
import unittest

root = Path(__file__).resolve().parents[1]
temporary = root / 'tests' / 'runtime_temp'
temporary.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(temporary)
sys.path.insert(0, str(root / 'host'))
def source_hashes():
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root/'host').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.bin','.bat') and '__pycache__' not in p.parts}
source_before=source_hashes()
suite = unittest.defaultTestLoader.discover(str(root / 'host'), pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
if source_before!=source_hashes():raise RuntimeError('Host source changed during test run')
(root/'tests/results/host_source_validation.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,sources=source_before),indent=2),encoding='utf-8')
raise SystemExit(not result.wasSuccessful())
