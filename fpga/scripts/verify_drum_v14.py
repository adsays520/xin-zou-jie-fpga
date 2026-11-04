import json
import re
import subprocess
import sys

from iverilog_runner import ROOT, OUT, compile_sim, simulate


def run_script(name):
    subprocess.run([sys.executable, '-B', '-X', 'utf8', 'scripts/' + name], cwd=ROOT, check=True)


def metrics(log):
    pattern = r'DRUM k=(\d+) v=(\d+) raw_peak=(\d+) out_peak=(\d+) min_gain=(\d+) limited=(\d+) safety=(\d+) sticky=(\d+)'
    return {(int(kit), int(voice)): dict(zip(('raw_peak', 'out_peak', 'min_gain', 'limited', 'safety', 'sticky'),
                map(int, values))) for kit, voice, *values in re.findall(pattern, log)}


def main():
    executable = compile_sim('tb_drum_morph_v14', ['src/drums/drum_synth.v',
        'src/drums/kick_modal.v', 'src/performance_mixer.v', 'tests/tb_drum_morph_v14.sv'])
    log = simulate(executable, 'drum_morph_v14.log')
    assert 'PASS DRUM MORPH V14: 16388' in log
    print(log, flush=True)
    run_script('verify_drum_audio_v14.py')
    run_script('diagnose_drum_v14.py')
    before = metrics((OUT / 'drum_v13_baseline/drum_headroom_v14.log').read_text())
    after = metrics((OUT / 'drum_headroom_v14.log').read_text())
    assert set(before) == set(after) == {(kit, voice) for kit in range(3) for voice in range(13)}
    for key, current in after.items():
        assert current['safety'] == current['sticky'] == 0
        assert current['raw_peak'] <= 8388607
        if key[1] == 12:
            assert current['raw_peak'] < before[key]['raw_peak'] * 0.75
            assert current['min_gain'] > before[key]['min_gain']
        else:
            assert current['limited'] == 0 and current['min_gain'] == 32768
    payload = (ROOT / 'sd_card/DRUMS.BIN').read_bytes()
    (ROOT / 'tests/runtime_temp/drums_bytes.hex').write_text(
        ''.join(f'{value:02x}\n' for value in payload), encoding='utf-8')
    executable = compile_sim('tb_drum_bank_v7', ['src/drums/drum_parameter_bank.v', 'tests/tb_drum_bank_v7.sv'])
    log = simulate(executable, 'drum_bank_v7.log')
    assert 'PASS DRUM BANK V7:' in log
    print(log, flush=True)
    run_script('verify_drum_sd_v7.py')
    run_script('verify_drums_lifecycle.py')
    (OUT / 'drum_v14_result.json').write_text(json.dumps(
        {'passed': True, 'before': {str(key): value for key, value in before.items()},
         'after': {str(key): value for key, value in after.items()},
         'FPGA_written': False, 'board_listening_verified': False}, indent=2), encoding='utf-8')
    print('PASS DRUM V14 regression: math, preserved non-cymbal synthesis, headroom, SD/CRC, lifecycle', flush=True)


if __name__ == '__main__':
    main()
