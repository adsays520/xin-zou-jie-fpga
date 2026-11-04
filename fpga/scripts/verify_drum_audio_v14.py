import json
from iverilog_runner import OUT, compile_sim, simulate


sources = ['src/drums/drum_synth.v', 'tests/reference_v13/drum_synth.v',
           'src/drums/kick_modal.v', 'src/performance_mixer.v', 'tests/tb_drum_audio_v14.sv']
executable = compile_sim('tb_drum_audio_v14', sources)
log = simulate(executable, 'drum_audio_v14.log', timeout=2400)
assert 'PASS DRUM AUDIO V14:' in log
(OUT / 'drum_audio_v14.json').write_text(json.dumps(
    {'passed': True, 'scope': 'RTL comparison to v13, not physical board listening',
     'sources': json.loads((OUT / 'tb_drum_audio_v14_source_sha256.json').read_text()),
     'log': log}, indent=2), encoding='utf-8')
print(log, flush=True)
