"""Independently synthesize current drum core, then compare actual Gowin gates."""
from pathlib import Path
import os,sys,re,shutil,json,hashlib,subprocess
r=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(r/'scripts'))
from iverilog_runner import compile_sim,simulate
out=r/'tests/results';probe=r/'tests/runtime_temp/drum_gate_project'
inputs=['src/drums/drum_synth.v','src/performance_mixer.v','src/drums/rom/sine.hex','src/drums/rom/params.hex','src/drums/kick_modal.v','src/drums/rom/kick_modal_coeffs.hex','src/drums/rom/kick_force.hex']
inputs+=['src/drums/drum_parameter_bank.v','src/drums/rom/drum_bank.hex','src/drums/rom/drum_bank_config.vh']
proof={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in inputs}
if '--reuse-netlist' not in sys.argv:
 for n in inputs:
  (probe/n).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/n,probe/n)
 xml=(r/'guitar_audio_low_speed.gprj').read_text()
 xml=re.sub(r'<FileList>[\s\S]*?</FileList>','<FileList><File path="src/drums/kick_modal.v" type="file.verilog" enable="1"/><File path="src/drums/drum_synth.v" type="file.verilog" enable="1"/><File path="src/performance_mixer.v" type="file.verilog" enable="1"/></FileList>',xml)
 (probe/'drum_gate.gprj').write_text(xml)
 (probe/'build.tcl').write_text('open_project drum_gate.gprj\nset_option -include_path [pwd]\nset_option -top_module drum_synth\nset_option -output_base_name drum_gate\nset_option -global_freq 50.000\nrun syn\nexit\n')
 p=subprocess.run([os.environ.get('GOWIN_SH','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe'),'build.tcl'],cwd=probe,capture_output=True,text=True,errors='replace',timeout=900)
 (out/'drums_gate_synthesis.log').write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0
assert proof=={n:hashlib.sha256((probe/n).read_bytes()).hexdigest() for n in inputs}
net=probe/'impl/gwsynthesis/drum_gate.vg'
rtl=(r/inputs[0]).read_text().replace('module drum_synth(','module drum_synth_rtl(').replace('performance_peak_control u_peak','performance_peak_control_rtl u_peak')
# Keep only the limiter module from the mixer file, with a unique name.
rtl=(r/inputs[0]).read_text().replace('module drum_synth(','module drum_synth_rtl(').replace('performance_peak_control u_peak','performance_peak_control_rtl u_peak')+'\nmodule performance_peak_control_rtl('+(r/inputs[1]).read_text().split('module performance_peak_control(')[1]
rtl=rtl.replace('`include "src/drums/drum_parameter_bank.v"','').replace('drum_parameter_bank u_parameters','drum_parameter_bank_rtl u_parameters')
rtl=rtl.replace('kick_modal #','kick_modal_rtl #')+'\n'+(r/'src/drums/kick_modal.v').read_text().replace('module kick_modal #','module kick_modal_rtl #')
rtl+='\n'+(r/'src/drums/drum_parameter_bank.v').read_text().replace('module drum_parameter_bank(','module drum_parameter_bank_rtl(')
(r/'tests/runtime_temp/drums_rtl.v').write_text(rtl)
from xsim_runner import run as xrun
prim=os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
xrun('xvlog.exe',['--sv',str(net),'tests/runtime_temp/drums_rtl.v','tests/tb_drums_gate.sv',prim],'drums_gate_xvlog.log')
xrun('xelab.exe',['tb_drums_gate','-s','drums_gate_synth','--relax','--O2'],'drums_gate_xelab.log')
log=xrun('xsim.exe',['drums_gate_synth','-R','-log',str(out/'drums_gate_xsim_internal.log')],'drums_gate_log.txt')
assert 'PASS post-synthesis drums' in log
assert proof=={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in inputs}
proof['gate_netlist_sha256']=hashlib.sha256(net.read_bytes()).hexdigest()
(out/'drums_gate_hashes.json').write_text(json.dumps(proof,indent=2))
print(log,flush=True)
