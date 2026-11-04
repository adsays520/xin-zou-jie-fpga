from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
BASE = APP.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = HERE / 'test_results'
    result.mkdir(exist_ok=True)
    temporary = result / 'temporary'
    temporary.mkdir(exist_ok=True)
    environment = dict(os.environ)
    environment['PYTHONPATH'] = os.pathsep.join((str(APP), str(BASE / 'host'), str(BASE / 'tools/python_deps')))
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['TMP'] = environment['TEMP'] = str(temporary)
    paths = [*HERE.glob('*.py'), *HERE.glob('*.ps1'), *HERE.glob('*.cmd'),
             APP / 'arrangement_model.py', APP / 'arrangement_playback.py', APP / 'arrangement_panel.py',
             APP / 'ensemble_protocol.py', APP / 'host_controller.py', APP / 'test_arrangement.py',
             APP / 'test_arrangement_ui.py', APP / 'melody_player.py',
             BASE / 'host/drum_patterns.py', BASE / 'host/guitar_effects.py', BASE / 'host/master_space_effects.py']
    before = {str(path): digest(path) for path in paths}
    fpga = BASE / 'ensemble_daw_v10'
    physical = json.loads((fpga / 'tests/results/physical_v10/proof.json').read_text())
    assert physical['passed'] and physical['returncode'] == 0
    assert all(digest(fpga / name) == value for name, value in physical['sources'].items())
    bitstream = fpga / physical['generated_bitstream']['path']
    assert digest(bitstream) == physical['generated_bitstream']['sha256']
    proof = {'started': datetime.now(timezone(timedelta(hours=8))).isoformat(),
             'passed': False, 'source_sha256': before, 'groups': [],
             'FPGA_written': False, 'real_serial_connected': False, 'board_listening_validated': False}
    try:
        for label, command, working in (
            ('generate', [sys.executable, '-B', '-X', 'utf8', 'build_demo.py'], HERE),
            ('demo_tests', [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', '-v', 'test_demo'], HERE),
            ('arranger_regression', [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', '-v', 'test_arrangement'], APP),
        ):
            with (result / (label + '.log')).open('w', encoding='utf-8') as stream:
                child = subprocess.run(command, cwd=working, env=environment, stdout=stream,
                                       stderr=subprocess.STDOUT, timeout=240)
            log = (result / (label + '.log')).read_text(encoding='utf-8', errors='replace')
            record = {'name': label, 'returncode': child.returncode}
            match = re.search(r'Ran (\d+) tests?', log)
            if match:
                record['test_count'] = int(match.group(1))
            proof['groups'].append(record)
            assert child.returncode == 0, f'{label} failed: {log[-5000:]}'
            print(label + ' PASS', flush=True)
        proof['sources_unchanged'] = all(digest(Path(name)) == value for name, value in before.items())
        proof['v10_frozen_inputs_unchanged'] = all(digest(fpga / name) == value for name, value in physical['sources'].items())
        proof['v10_bitstream_unchanged'] = digest(bitstream) == physical['generated_bitstream']['sha256']
        proof['projects'] = {path.name: digest(path) for path in HERE.glob('*.tang.json')}
        proof['passed'] = proof['sources_unchanged'] and proof['v10_frozen_inputs_unchanged'] and proof['v10_bitstream_unchanged']
    except BaseException as error:
        proof['error'] = f'{type(error).__name__}: {error}'
    proof['finished'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    (result / 'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({name: value for name, value in proof.items() if name != 'source_sha256'}, ensure_ascii=False, indent=2))
    return 0 if proof['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
