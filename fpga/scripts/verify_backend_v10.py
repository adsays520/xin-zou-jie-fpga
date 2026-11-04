from datetime import datetime, timezone, timedelta
import json
import re
import subprocess
import sys

from backend_v10 import TCL, validate_tcl
from build_inputs_v10 import ROOT
from iverilog_runner import source_hashes, assert_source_hashes


def main():
    output = ROOT / 'tests/results/configuration_v10'
    output.mkdir(exist_ok=False)
    names = [TCL, 'scripts/backend_v10.py', 'scripts/backend_ddr_split_v9.py',
             'scripts/backend_options_v9.py', 'scripts/verify_backend_v10.py',
             'scripts/check_backend_options_v10.tcl', 'scripts/timing_report_v10.py',
             'tests/test_backend_v10.py',
             str(ROOT.parent / 'ensemble_hall_v7/impl/pnr/ensemble_hall_piano_v7_tr_content.html'),
             str(ROOT.parent / 'ensemble_daw_v9/impl/pnr/ensemble_daw_v9_ddr_split_tr_content.html')]
    proof = {'started': datetime.now(timezone(timedelta(hours=8))).isoformat(),
             'passed': False, 'sources': source_hashes(names)}
    try:
        validate_tcl((ROOT / TCL).read_text())
        with (output / 'unit_tests.log').open('w', encoding='utf-8') as stream:
            child = subprocess.run([sys.executable, '-B', '-X', 'utf8', 'tests/test_backend_v10.py'],
                                   cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        proof['unit_returncode'] = child.returncode
        assert child.returncode == 0
        match = re.search(r'Ran (\d+) tests?', (output / 'unit_tests.log').read_text())
        assert match and int(match.group(1)) == 12
        proof['unit_test_count'] = int(match.group(1))
        with (output / 'gowin_options.log').open('w', encoding='utf-8') as stream:
            child = subprocess.run(['D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe',
                                    'scripts/check_backend_options_v10.tcl'], cwd=ROOT,
                                   stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        proof['gowin_options_returncode'] = child.returncode
        assert child.returncode == 0
        assert 'PASS V10 backend options accepted' in (output / 'gowin_options.log').read_text()
        assert_source_hashes(proof['sources'])
        proof['passed'] = True
    except BaseException as error:
        proof['error'] = f'{type(error).__name__}: {error}'
    proof['finished'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    (output / 'proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps({name: value for name, value in proof.items() if name != 'sources'}, indent=2), flush=True)
    return 0 if proof['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
