from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'drum_bass_pitch_20261013'
APP = BASE / 'violin_r15'
sys.path[:0] = [str(APP), str(BASE / 'host'), str(BASE / 'tools/python_deps')]
from arrangement_model import Project
from demo_headroom import with_headroom


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    results = ROOT / 'test_results' / ('headroom_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    results.mkdir(parents=True, exist_ok=False)
    temporary = results / 'temporary'
    temporary.mkdir(exist_ok=True)
    environment = dict(os.environ)
    environment['PYTHONPATH'] = os.pathsep.join((str(ROOT), str(APP), str(BASE / 'host'), str(BASE / 'tools/python_deps')))
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['TMP'] = environment['TEMP'] = str(temporary)
    paths = [*ROOT.glob('*.py'), *ROOT.glob('*.ps1'), *ROOT.glob('*.md'),
             ROOT.parent / '打开音乐Demo.cmd', ROOT.parent / '打开钢琴Demo.cmd',
             ROOT.parent / '打开失真摇滚Demo.cmd', ROOT.parent / '打开失真摇滚短试听.cmd',
             ROOT / 'headroom_baseline.json',
             APP / 'arrangement_model.py', APP / 'arrangement_playback.py', APP / 'arrangement_panel.py',
             APP / 'host_controller.py', APP / 'ensemble_protocol.py']
    before = {str(path): digest(path) for path in paths}
    previous_projects = {str(path): digest(path) for path in (ROOT / 'projects').glob('*.tang.json')}
    original = APP / 'demos/neon_runway_20261024'
    preserved = {str(path): digest(path) for path in original.rglob('*') if path.is_file()}
    fpga = BASE / 'ensemble_daw_v10'
    physical = json.loads((fpga / 'tests/results/physical_v10/proof.json').read_text(encoding='utf-8'))
    panel_fpga = BASE / 'ensemble_panel_v13'
    panel_proof = json.loads((panel_fpga / 'tests/results/panel_v13_build/proof.json').read_text(encoding='utf-8'))
    receipt = json.loads((ROOT / 'headroom_baseline.json').read_text(encoding='utf-8'))
    original_projects = Path(receipt['backup']) / 'Music_Demos/projects'
    proof = {'started': datetime.now(timezone(timedelta(hours=8))).isoformat(), 'passed': False,
             'source_sha256': before, 'groups': [], 'FPGA_written': False, 'ESP_written': False,
             'real_serial_connected': False, 'board_listening_validated': False}
    try:
        assert physical['passed'] and physical['returncode'] == 0
        bitstream = fpga / physical['generated_bitstream']['path']
        assert digest(bitstream) == physical['generated_bitstream']['sha256']
        assert all(digest(fpga / name) == value for name, value in physical['sources'].items())
        assert panel_proof['passed'] and panel_proof['returncode'] == 0
        assert all(digest(panel_fpga / name) == value for name, value in panel_proof['sources'].items())
        for label, command, working in (
            ('generate', [sys.executable, '-B', '-X', 'utf8', 'build_library.py'], ROOT),
            ('library_tests', [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', '-v', 'test_library', 'test_demo_headroom'], ROOT),
            ('arranger_regression', [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', '-v', 'test_arrangement', 'test_ensemble_arrangement'], APP),
            ('launcher_imports', ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                  str(ROOT / 'launch_library.ps1'), '-CheckOnly'], ROOT),
        ):
            path = results / (label + '.log')
            with path.open('w', encoding='utf-8') as stream:
                process = subprocess.run(command, cwd=working, env=environment, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=240)
            log = path.read_text(encoding='utf-8', errors='replace')
            record = {'name': label, 'returncode': process.returncode}
            match = re.search(r'Ran (\d+) tests?', log)
            if match:
                record['test_count'] = int(match.group(1))
            proof['groups'].append(record)
            assert process.returncode == 0, f'{label} failed: {log[-5000:]}'
            print(label + ' PASS', flush=True)
        proof['sources_unchanged'] = all(digest(Path(name)) == value for name, value in before.items())
        proof['previous_neon_demo_unchanged'] = all(digest(Path(name)) == value for name, value in preserved.items())
        proof['previous_library_project_count'] = len(previous_projects)
        proof['previous_library_projects_unchanged'] = all(digest(Path(name)) == value for name, value in previous_projects.items())
        proof['demo_changes_only_bus_gain'] = len(receipt['original_projects']) == 20 and all(
            digest(original_projects / name) == value and
            Project.load(ROOT / 'projects' / name) == with_headroom(Project.load(original_projects / name))
            for name, value in receipt['original_projects'].items())
        proof['v13_frozen_inputs_unchanged'] = all(digest(panel_fpga / name) == value for name, value in panel_proof['sources'].items())
        proof['v13_bitstream_unchanged'] = digest(panel_fpga / panel_proof['generated_bitstream']['path']) == panel_proof['generated_bitstream']['sha256']
        proof['v10_frozen_inputs_count'] = len(physical['sources'])
        proof['v10_frozen_inputs_unchanged'] = all(digest(fpga / name) == value for name, value in physical['sources'].items())
        proof['v10_bitstream_sha256'] = digest(bitstream)
        proof['v10_bitstream_unchanged'] = proof['v10_bitstream_sha256'] == physical['generated_bitstream']['sha256']
        proof['projects'] = {path.name: digest(path) for path in (ROOT / 'projects').glob('*.tang.json')}
        proof['passed'] = all(proof[name] for name in ('sources_unchanged', 'previous_neon_demo_unchanged',
                                                      'demo_changes_only_bus_gain', 'v13_frozen_inputs_unchanged',
                                                      'v13_bitstream_unchanged', 'v10_frozen_inputs_unchanged', 'v10_bitstream_unchanged'))
    except BaseException as error:
        proof['error'] = f'{type(error).__name__}: {error}'
    proof['finished'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    (results / 'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in proof.items() if key not in ('source_sha256', 'projects')}, ensure_ascii=False, indent=2))
    return 0 if proof['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
