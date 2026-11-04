from datetime import datetime, timedelta, timezone
import json
import re
import xml.etree.ElementTree as ET

from build_hall_piano_v4 import ROOT, digest, source_hashes, verify_baseline
from resume_hall_piano_v4 import ARCHIVE, OUTPUT as RUN_OUTPUT, NETLIST, PLACEMENT

OUTPUT = ROOT / 'tests/results/hall_piano_v4_build_verified'


def input_hashes(mode='resume1'):
    result = source_hashes()
    if mode == 'resume1':
        result['build_pnr_resume_v4.tcl'] = digest(ROOT / 'build_pnr_resume_v4.tcl')
        result['resume_placement.p'] = digest(PLACEMENT)
    elif mode != 'clean2':
        raise ValueError('Unknown build input mode: ' + mode)
    return result


def compare_synthesis_records():
    records = []
    for path in (ARCHIVE / 'synthesis/ensemble_hall_piano_v4.vg', NETLIST):
        lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
        assert lines[:3] == ['//\n', '//Written by GowinSynthesis\n', '//Tool Version "V1.9.12.03 (64-bit)"\n']
        lines[3] = '// GENERATED_TIMESTAMP\n'
        text = ''.join(lines)
        blocks = re.findall(r'(?ms)^`pragma protect begin_protected\n.*?^`pragma protect end_protected[^\n]*\n', text)
        assert blocks, 'Expected vendor protected netlist block'
        metadata = [[line for line in block.splitlines() if line.startswith('`pragma protect ')] for block in blocks]
        visible = re.sub(r'(?ms)^`pragma protect begin_protected\n.*?^`pragma protect end_protected[^\n]*\n',
                         'VENDOR_PROTECTED_BLOCK\n', text)
        records.append((visible, metadata))
    assert records[0][1] == records[1][1], 'Protected block metadata changed'
    options = []
    for path in (ARCHIVE / 'synthesis/ensemble_hall_piano_v4.prj', ROOT / 'impl/gwsynthesis/ensemble_hall_piano_v4.prj'):
        options.append({entry.attrib['type']: entry.attrib['value'] for entry in ET.parse(path).iter('Option')})
    assert options[0] == options[1], 'Synthesis options changed'
    return {'protected_block_count': len(records[0][1]),
            'protected_block_metadata_identical': True, 'synthesis_options_identical': True,
            'visible_netlist_byte_identical': records[0][0] == records[1][0],
            'gate_level_equivalence_claimed': False}


def main():
    run = json.loads((RUN_OUTPUT / 'proof.json').read_text(encoding='utf-8'))
    assert run.get('finished') and run['returncode'] == 0, 'Tool flow not successfully finished'
    actual_inputs = input_hashes()
    previous_inputs = {name: value for name, value in run['sources'].items() if name != 'verified_synthesis.vg'}
    assert actual_inputs == previous_inputs, 'A real source, constraint, script or placement input changed'
    assert run['sources']['verified_synthesis.vg'] == digest(ARCHIVE / 'synthesis/ensemble_hall_piano_v4.vg')
    synthesis_review = compare_synthesis_records()
    console = (RUN_OUTPUT / 'console.log').read_text(encoding='utf-8', errors='replace')
    for marker in ('GowinSynthesis finish', 'R10 Pro DDR PASS:', 'PASS minimum pulse width', 'Merged build timing PASS'):
        assert marker in console, marker
    bitstream = ROOT / 'impl/pnr/ensemble_hall_piano_v4.fs'
    assert digest(bitstream) == run['bitstream_sha256']
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {'started': run['started'], 'finished': run['finished'],
              'reviewed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'passed': True, 'sources': actual_inputs, 'sources_unchanged': True,
              'baseline_unchanged_files_checked': verify_baseline(),
              'place_option': 2, 'route_option': 1, 'FPGA_written': False,
              'bitstream_sha256': digest(bitstream), 'bitstream_size': bitstream.stat().st_size,
              'raw_run_proof_sha256': digest(RUN_OUTPUT / 'proof.json'),
              'generated_netlist_sha256': digest(NETLIST),
              'synthesis_review': synthesis_review,
              'protected_ciphertext_not_claimed_byte_or_plaintext_equivalent': True,
              'synthesis_options_identical': True,
              'raw_wrapper_passed': run['passed'],
              'review_reason': 'Gowin rebuilt synthesis; timestamp, generated names and vendor ciphertext are outputs; verify real inputs, tool options and fresh strict timing separately'}
    (OUTPUT / 'proof.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({name: value for name, value in report.items() if name != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
