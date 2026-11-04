import json
from iverilog_runner import OUT, compile_sim, simulate


sources = ['src/drums/drum_synth.v', 'src/drums/kick_modal.v',
           'src/performance_mixer.v', 'tests/tb_drum_headroom_v14.sv']
executable = compile_sim('tb_drum_headroom_v14', sources)
log = simulate(executable, 'drum_headroom_v14.log', timeout=1800)
assert 'PASS DRUM HEADROOM V14' in log
binding = json.loads((OUT / 'tb_drum_headroom_v14_source_sha256.json').read_text())
(OUT / 'drum_headroom_v14.json').write_text(json.dumps(
    {'passed': True, 'scope': 'RTL arithmetic and peak measurement, not board listening',
     'sources': binding, 'log': log}, indent=2), encoding='utf-8')
print(log, flush=True)
