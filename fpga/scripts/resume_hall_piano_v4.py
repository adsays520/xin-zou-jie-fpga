from datetime import datetime, timedelta, timezone
import json
import subprocess

from build_hall_piano_v4 import ROOT, GOWIN, digest, source_hashes, verify_baseline

ARCHIVE = ROOT / 'tests/results/hall_piano_v4_interrupted_20261020_1947'
OUTPUT = ROOT / 'tests/results/hall_piano_v4_build_resume1'
NETLIST = ROOT / 'impl/gwsynthesis/ensemble_hall_piano_v4.vg'
PLACEMENT = ARCHIVE / 'pnr/ensemble_hall_piano_v4.p'


def build_hashes():
    result = source_hashes()
    result['build_pnr_resume_v4.tcl'] = digest(ROOT / 'build_pnr_resume_v4.tcl')
    result['resume_placement.p'] = digest(PLACEMENT)
    result['verified_synthesis.vg'] = digest(NETLIST)
    return result


def main():
    prior = json.loads((ARCHIVE / 'build/proof.json').read_text())
    assert prior['sources'] == source_hashes(), 'Sources changed since synthesis'
    for entry in json.loads((ARCHIVE / 'sha256.json').read_text(encoding='utf-8-sig')):
        assert digest(ARCHIVE / entry['path']) == entry['sha256'], entry['path']
    assert digest(NETLIST) == digest(ARCHIVE / 'synthesis/ensemble_hall_piano_v4.vg')
    assert 'GowinSynthesis finish' in (ARCHIVE / 'build/console.log').read_text(encoding='utf-8')
    previous_log = (ARCHIVE / 'pnr/ensemble_hall_piano_v4.log').read_text(encoding='utf-8')
    assert '[50%] Placement Phase 3 completed' in previous_log and 'Running routing' in previous_log
    previous_command = (ARCHIVE / 'pnr/cmd.do').read_text(encoding='utf-8-sig')
    assert '-place_option 2' in previous_command and '-route_option 1' in previous_command
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assert not (OUTPUT / 'proof.json').exists(), 'Do not overwrite a prior attempt'
    proof = {'started': datetime.now(timezone(timedelta(hours=8))).isoformat(),
             'sources': build_hashes(), 'baseline_unchanged_files_checked': verify_baseline(),
             'passed': False, 'FPGA_written': False, 'place_option': 2, 'route_option': 1,
             'verified_netlist_reused': True, 'completed_timing_priority_placement_reused': True,
             'full_routing_restarted': True, 'prior_interruption_archive': str(ARCHIVE),
             'prior_timing_verdict': 'not_produced', 'prior_process_exit_reason': 'unknown'}
    (OUTPUT / 'proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print('Verified unchanged source/netlist and archived completed timing-priority placement; restarting routing', flush=True)
    with (OUTPUT / 'console.log').open('w', encoding='utf-8') as stream:
        result = subprocess.run([str(GOWIN), 'build_pnr_resume_v4.tcl'], cwd=ROOT,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=10800)
    output = (OUTPUT / 'console.log').read_text(encoding='utf-8', errors='replace')
    proof.update(finished=datetime.now(timezone(timedelta(hours=8))).isoformat(), returncode=result.returncode,
                 sources_unchanged=proof['sources'] == build_hashes())
    proof['passed'] = result.returncode == 0 and proof['sources_unchanged'] and all(
        marker in output for marker in ('R10 Pro DDR PASS:', 'PASS minimum pulse width', 'Merged build timing PASS'))
    bitstream = ROOT / 'impl/pnr/ensemble_hall_piano_v4.fs'
    if bitstream.exists():
        proof['bitstream_sha256'] = digest(bitstream)
        proof['bitstream_size'] = bitstream.stat().st_size
    (OUTPUT / 'proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(output[-6000:], flush=True)
    print(json.dumps({key: value for key, value in proof.items() if key != 'sources'}, indent=2), flush=True)
    if not proof['passed']:
        raise SystemExit('Resumed candidate did not pass strict original timing checks')


if __name__ == '__main__':
    main()
