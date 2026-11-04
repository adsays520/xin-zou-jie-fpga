"""Compare independently synthesized kick/peak kernels with current RTL."""
from pathlib import Path
import os,sys,re,shutil,hashlib,json,subprocess
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'scripts'))
from xsim_runner import run as xrun
out=r/'tests/results'
inputs=['src/drums/drum_synth.v','src/performance_mixer.v','src/drums/rom/sine.hex','src/drums/rom/params.hex','src/drums/kick_modal.v','src/drums/rom/kick_modal_coeffs.hex','src/drums/rom/kick_force.hex']
proof={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in inputs}
all_logs=[];net_hash={}
for kind,top,source in [('kick','kick_modal','src/drums/kick_modal.v'),('peak','performance_peak_control','src/performance_mixer.v')]:
 probe=r/('tests/runtime_temp/'+kind+'_gate_project')
 if '--reuse-netlist' in sys.argv:
  assert proof=={n:hashlib.sha256((probe/n).read_bytes()).hexdigest() for n in inputs},kind+' source changed'
 else:
  for name in inputs:
   (probe/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/name,probe/name)
  xml=(r/'guitar_audio_low_speed.gprj').read_text()
  xml=re.sub(r'<FileList>[\s\S]*?</FileList>',f'<FileList><File path="{source}" type="file.verilog" enable="1"/></FileList>',xml)
  (probe/'gate.gprj').write_text(xml)
  (probe/'build.tcl').write_text(f'open_project gate.gprj\nset_option -top_module {top}\nset_option -output_base_name {kind}_gate\nset_option -global_freq 50.000\nrun syn\nexit\n')
  with (out/(kind+'_gate_synthesis.log')).open('w',encoding='utf-8') as f:
   p=subprocess.run([os.environ.get('GOWIN_SH','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe'),'build.tcl'],cwd=probe,stdout=f,stderr=subprocess.STDOUT,timeout=900)
  assert p.returncode==0,kind+' synthesis'
 net=probe/f'impl/gwsynthesis/{kind}_gate.vg'
 if '--synth-only' in sys.argv:
  print('Prepared netlist:',kind,flush=True);continue
 rtl=(r/source).read_text()
 if kind=='peak':rtl='module performance_peak_control('+rtl.split('module performance_peak_control(')[1]
 rtl=rtl.replace('module '+top+'(','module '+top+'_rtl(')
 rtlfile=r/f'tests/runtime_temp/{kind}_gate_rtl.v';rtlfile.write_text(rtl)
 prim=os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
 xrun('xvlog.exe',['--sv',str(net),str(rtlfile),f'tests/tb_{kind}_gate.sv',prim],kind+'_gate_xvlog.log')
 xrun('xelab.exe',[f'tb_{kind}_gate','-s',kind+'_gate','--relax','--O2','--mt','off','--debug','off'],kind+'_gate_xelab.log')
 log=xrun('xsim.exe',[kind+'_gate','-R','-log',str(out/(kind+'_gate_internal.log'))],kind+'_gate_run.log')
 assert 'PASS post-synthesis '+kind in log,log[-4000:]
 all_logs.append(log);net_hash[kind]=hashlib.sha256(net.read_bytes()).hexdigest();print(log[-2000:],flush=True)
if '--synth-only' in sys.argv:raise SystemExit(0)
assert proof=={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in inputs}
proof['gate_netlist_sha256']=net_hash
(out/'drums_gate_hashes.json').write_text(json.dumps(proof,indent=2))
all_logs.append('PASS post-synthesis audio kernels: kick and linked peak control; no waveform substitutions.\n')
(out/'drums_gate_log.txt').write_text('\n'.join(all_logs),encoding='utf-8')
print(all_logs[-1],flush=True)
