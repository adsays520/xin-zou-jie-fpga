from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from backend_ddr_split_v9 import EXPECTED, STEM, TCL, validate_command, validate_tcl
from build_inputs_v9 import ROOT, digest, sources


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def main():
    previous = ROOT / 'tests/results/physical_v9/proof.json'
    old = json.loads(previous.read_text())
    assert old['finished'] and old['returncode'] == 1 and old['sources_unchanged']
    assert 'ERROR  (CT1135)' in (previous.parent / 'console.log').read_text()
    for name, expected in old['sources'].items():
        assert digest(ROOT / name) == expected, name
    output = ROOT / 'tests/results/physical_v9_ddr_split'
    output.mkdir(exist_ok=False)
    config = {'started': now(), 'passed': False}
    names = (TCL, 'scripts/backend_ddr_split_v9.py', 'scripts/run_ddr_split_v9.py',
             'scripts/check_ddr_split_gate_v9.py', 'scripts/check_ddr_split_options_v9.tcl',
             'tests/test_backend_ddr_split_v9.py')
    config['sources'] = {name: digest(ROOT / name) for name in names}
    try:
        validate_tcl((ROOT / TCL).read_text())
        with (output / 'configuration_tests.log').open('w', encoding='utf-8') as stream:
            child = subprocess.run([sys.executable, '-B', '-X', 'utf8', 'tests/test_backend_ddr_split_v9.py'],
                                   cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        config['unit_returncode'] = child.returncode
        assert child.returncode == 0
        match = re.search(r'Ran (\d+) tests?', (output / 'configuration_tests.log').read_text())
        assert match and int(match.group(1)) == 8
        config['unit_test_count'] = int(match.group(1))
        with (output / 'configuration_gowin.log').open('w', encoding='utf-8') as stream:
            child = subprocess.run(['D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe',
                                    'scripts/check_ddr_split_options_v9.tcl'], cwd=ROOT,
                                   stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        config['gowin_options_returncode'] = child.returncode
        assert child.returncode == 0
        assert 'PASS V9 DDR-split backend options accepted' in (output / 'configuration_gowin.log').read_text()
        assert all(digest(ROOT / name) == value for name, value in config['sources'].items())
        config['passed'] = True
    except BaseException as error:
        config['error'] = f'{type(error).__name__}: {error}'
    config['finished'] = now()
    (output / 'configuration.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    assert config['passed'], config
    from check_ddr_split_gate_v9 import verify
    functional = verify()
    frozen = sources()
    frozen[TCL] = digest(ROOT / TCL)
    proof = {'started': now(), 'passed': False, 'physical_build_only': True,
             'sources': frozen, 'functional_gate': functional, 'backend_requested': dict(EXPECTED),
             'place_option': 2, 'route_option': 2, 'incremental': False,
             'reason': 'Preserve fixed DDR FIFO names/locations after native-wide CT1135',
             'FPGA_written': False, 'S3_written': False}
    proof_path = output / 'proof.json'
    proof_path.write_text(json.dumps(proof, indent=2), encoding='utf-8')
    environment = dict(os.environ)
    environment['V9_PYTHON'] = sys.executable
    try:
        with (output / 'console.log').open('w', encoding='utf-8') as stream:
            child = subprocess.run(['D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe', TCL],
                                   cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=21600)
        proof['returncode'] = child.returncode
        current = sources()
        current[TCL] = digest(ROOT / TCL)
        proof['sources_unchanged'] = frozen == current
        command = ROOT / 'impl/pnr/cmd.do'
        if command.exists() and command.stat().st_mtime >= datetime.fromisoformat(proof['started']).timestamp():
            proof['backend_actual'] = validate_command(command.read_text(), ROOT)
            proof['backend_command_sha256'] = digest(command)
            proof['backend_options_verified'] = True
        else:
            proof['backend_options_verified'] = False
        log = (output / 'console.log').read_text(encoding='utf-8', errors='replace')
        proof['passed'] = child.returncode == 0 and proof['sources_unchanged'] and proof['backend_options_verified'] and all(
            marker in log for marker in ('PASS V9 DDR-split functional gate:', 'R10 Pro DDR PASS:',
                                         'PASS minimum pulse width', 'V9 DDR-split timing PASS: setup=0 hold=0'))
        if proof['passed']:
            bitstream = ROOT / f'impl/pnr/{STEM}.fs'
            assert bitstream.exists() and bitstream.stat().st_mtime >= datetime.fromisoformat(proof['started']).timestamp()
            proof.update(bitstream_sha256=digest(bitstream), bitstream_size=bitstream.stat().st_size)
    except BaseException as error:
        proof.update(passed=False, error=f'{type(error).__name__}: {error}')
    proof['finished'] = now()
    proof_path.write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps({name: value for name, value in proof.items() if name != 'sources'}, indent=2), flush=True)
    return 0 if proof['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
