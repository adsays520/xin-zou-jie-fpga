from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from backend_options_v9 import validate_requested_tcl


ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def main():
    assert not (ROOT / 'tests/results/physical_v9/proof.json').exists(), 'Do not change an active physical experiment'
    output = ROOT / 'tests/results/backend_config_reroute_v9'
    output.mkdir(exist_ok=False)
    proof = {'started': now(), 'passed': False, 'scope': 'configuration_validation_not_physical_build',
             'FPGA_written': False, 'S3_written': False}
    names = ('build_merged.tcl', 'scripts/backend_options_v9.py', 'scripts/check_backend_options_v9.tcl',
             'scripts/verify_backend_config_v9.py', 'scripts/build_physical_v9.py',
             'scripts/check_functional_v9.py', 'tests/test_backend_options_v9.py')

    def sources():
        return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}

    proof['sources'] = sources()
    try:
        proof['requested'] = validate_requested_tcl((ROOT / 'build_merged.tcl').read_text())
        with (output / 'unit_tests.log').open('w', encoding='utf-8') as stream:
            child = subprocess.run([sys.executable, '-B', '-X', 'utf8', 'tests/test_backend_options_v9.py'],
                                   cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        proof['unit_returncode'] = child.returncode
        assert child.returncode == 0
        match = re.search(r'Ran (\d+) tests?', (output / 'unit_tests.log').read_text())
        assert match and int(match.group(1)) == 10
        proof['unit_test_count'] = int(match.group(1))
        with (output / 'gowin_option_acceptance.log').open('w', encoding='utf-8') as stream:
            child = subprocess.run(['D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe',
                                    'scripts/check_backend_options_v9.tcl'], cwd=ROOT,
                                   stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        proof['gowin_options_returncode'] = child.returncode
        assert child.returncode == 0
        log = (output / 'gowin_option_acceptance.log').read_text(encoding='utf-8', errors='replace')
        assert 'PASS V9 backend options accepted; no synthesis or PnR launched' in log and 'ERROR' not in log
        proof['sources_unchanged'] = proof['sources'] == sources()
        assert proof['sources_unchanged']
        proof['passed'] = True
    except BaseException as error:
        proof['error'] = f'{type(error).__name__}: {error}'
    proof['finished'] = now()
    (output / 'proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps({name: value for name, value in proof.items() if name != 'sources'}, indent=2), flush=True)
    return 0 if proof['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
