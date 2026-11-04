from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
WORKSPACE = PROJECT.parent
BASELINE = WORKSPACE / 'output/hall_link_v2_setup_failed_20261020_171348/source/drum_bass_pitch_20261013'
OUTPUT = ROOT / 'test_results/hall_timing_v3'
SIM = WORKSPACE / 'tmp/sim_tools/mingw64'


def main():
    OUTPUT.mkdir(exist_ok=True)
    environment = os.environ.copy()
    environment['PATH'] = str(SIM / 'bin') + os.pathsep + environment['PATH']
    generated = []
    for relative, module, declaration in (
        ('output_r12/audio_driver.v', 'audio_drive', '('),
        ('src/drums/drum_machine.v', 'drum_machine', ' #('),
        ('violin_r15/touch_legacy.v', 'touch_to_command_legacy', ' #('),
        ('violin_r15/master_space_fx.v', 'master_space_fx', '('),
    ):
        target = OUTPUT / (module + '_gold.v')
        source = (BASELINE / relative).read_text(encoding='utf-8')
        anchor = 'module ' + module + declaration
        assert source.count(anchor) == 1, relative
        target.write_text(source.replace(anchor, 'module ' + module + '_timing_gold' + declaration), encoding='utf-8')
        generated.append(str(target.relative_to(PROJECT)))
    sources = ['tests/tb_hall_timing_v3.sv', 'output_r12/audio_driver.v',
               'src/drums/drum_machine.v', 'violin_r15/touch_legacy.v',
               'src/guitar_note_params.v', 'violin_r15/note_params_banked.v',
               'violin_r15/master_space_fx.v', 'tests/tb_hall_timing_space.sv', *generated]
    suites = ['tb_hall_timing_audio', 'tb_hall_timing_params', 'tb_hall_timing_drums',
              'tb_hall_timing_drums_48k', 'tb_hall_timing_gates',
              'tb_hall_timing_gates_one', 'tb_hall_timing_gates_short', 'tb_hall_timing_space']
    proof = {'started': datetime.now(timezone(timedelta(hours=8))).isoformat(),
             'baseline': str(BASELINE), 'passed': False, 'suites': {}}
    proof_path = OUTPUT / 'proof.json'
    proof_path.write_text(json.dumps(proof, indent=2), encoding='utf-8')
    for top in suites:
        hashes = {source: hashlib.sha256((PROJECT / source).read_bytes()).hexdigest() for source in sources}
        executable = OUTPUT / (top + '.vvp')
        commands = [
            [str(SIM / 'bin/iverilog.exe'), '-B', str(SIM / 'lib/ivl'), '-g2012', '-Wall',
             '-s', top, '-o', str(executable), *sources],
            [str(SIM / 'bin/vvp.exe'), str(executable)],
        ]
        for phase, command in zip(('compile', 'run'), commands):
            result = subprocess.run(command, cwd=PROJECT, env=environment, capture_output=True, text=True, timeout=600)
            output = result.stdout + result.stderr
            (OUTPUT / (top + '_' + phase + '.log')).write_text(output, encoding='utf-8')
            print(output[-3500:], flush=True)
            assert result.returncode == 0 and 'FATAL' not in output and 'ERROR:' not in output, top
            if phase == 'run':
                assert 'PASS ' in output, top
        assert all(hashlib.sha256((PROJECT / source).read_bytes()).hexdigest() == value for source, value in hashes.items())
        proof['suites'][top] = hashes
        proof_path.write_text(json.dumps(proof, indent=2), encoding='utf-8')
    proof.update(finished=datetime.now(timezone(timedelta(hours=8))).isoformat(), passed=True)
    proof_path.write_text(json.dumps(proof, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
