"""Run software-only regressions and record source-bound evidence."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    result = ROOT / 'test_results' / ('arranger_' + stamp)
    result.mkdir(parents=True)
    sources = [*ROOT.glob('arrangement_*.py'), ROOT / 'host_controller.py',
               ROOT / 'ensemble_protocol.py', ROOT / 'test_ensemble_arrangement.py',
               *ROOT.glob('test_arrangement*.py'), ROOT / 'validate_arranger.py']
    before = {str(path.relative_to(BASE)): digest(path) for path in sources}
    bitstream = BASE / 'ensemble_hall_v7' / 'impl' / 'pnr' / 'ensemble_hall_piano_v7.fs'
    bitstream_before = digest(bitstream) if bitstream.exists() else None
    environment = dict(os.environ)
    environment['PYTHONPATH'] = os.pathsep.join((str(BASE / 'host'), str(ROOT), str(BASE / 'tools' / 'python_deps')))
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    temporary = result / 'temporary'
    temporary.mkdir()
    environment['TMP'] = environment['TEMP'] = str(temporary)
    groups = [('arranger', ROOT, ['test_arrangement', 'test_ensemble_arrangement', 'test_arrangement_ui']),
              ('r15_regression', ROOT, ['test_host', 'test_ui', 'test_mario_player', 'test_mario_ui']),
              ('host_regression', BASE / 'host', None)]
    records = []
    for name, directory, modules in groups:
        command = [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest']
        command += ['-v', *modules] if modules else ['discover', '-v', '-p', 'test_*.py']
        completed = subprocess.run(command, cwd=directory, env=environment, capture_output=True, timeout=300)
        (result / (name + '.log')).write_bytes(completed.stdout + completed.stderr)
        records.append({'name': name, 'returncode': completed.returncode})
        print(name, completed.returncode, flush=True)
    unchanged = all(path.exists() and digest(path) == before[str(path.relative_to(BASE))] for path in sources)
    bitstream_unchanged = not bitstream_before or digest(bitstream) == bitstream_before
    proof = {'finished_at': datetime.now().astimezone().isoformat(),
             'passed': all(record['returncode'] == 0 for record in records) and unchanged and bitstream_unchanged,
             'groups': records, 'sources_unchanged': unchanged, 'source_sha256': before,
             'fpga_bitstream_sha256': bitstream_before, 'fpga_bitstream_unchanged': bitstream_unchanged,
             'hardware_connected': False, 'flashed': False, 'board_listening_validated': False}
    (result / 'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(result / 'proof.json', flush=True)
    return 0 if proof['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
