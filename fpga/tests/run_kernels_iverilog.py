from pathlib import Path
import os,sys,hashlib,json
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'scripts'))
from iverilog_runner import compile_sim,run,TOOLS
out=r/'tests/results'
inputs=['src/drums/drum_synth.v','src/performance_mixer.v','src/drums/rom/sine.hex','src/drums/rom/params.hex','src/drums/kick_modal.v','src/drums/rom/kick_modal_coeffs.hex','src/drums/rom/kick_force.hex']
proof={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in inputs};logs=[];nets={}
for kind,top,source in [('kick','kick_modal','src/drums/kick_modal.v'),('peak','performance_peak_control','src/performance_mixer.v')]:
 probe=r/f'tests/runtime_temp/{kind}_gate_project'
 assert proof=={n:hashlib.sha256((probe/n).read_bytes()).hexdigest() for n in inputs}
 net=probe/f'impl/gwsynthesis/{kind}_gate.vg';nets[kind]=hashlib.sha256(net.read_bytes()).hexdigest()
 rtl=(r/source).read_text()
 if kind=='peak':rtl='module performance_peak_control('+rtl.split('module performance_peak_control(')[1]
 rtl=rtl.replace('module '+top+'(','module '+top+'_rtl(')
 rf=r/f'tests/runtime_temp/{kind}_gate_rtl.v';rf.write_text(rtl)
 exe=compile_sim('tb_'+kind+'_gate',[str(net),str(rf),'tests/tb_'+kind+'_gate.sv',os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')])
 log=run([str(TOOLS/('bin/vvp.exe' if os.name=='nt' else 'bin/vvp')),'-v',exe],kind+'_gate_run.log',timeout=300)
 assert 'PASS post-synthesis '+kind in log
 logs.append(log);print(log[-3000:],flush=True)
assert proof=={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in inputs}
proof['gate_netlist_sha256']=nets
(out/'drums_gate_hashes.json').write_text(json.dumps(proof,indent=2))
logs.append('PASS post-synthesis audio kernels: kick and linked peak control; no waveform substitutions.\n')
(out/'drums_gate_log.txt').write_text('\n'.join(logs));print(logs[-1],flush=True)
