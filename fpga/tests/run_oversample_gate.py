from pathlib import Path
import os,subprocess,shutil,hashlib,json
r=Path(__file__).resolve().parents[1];out=r/'tests/results';net=r/'impl/gwsynthesis/guitar_audio_verification.vg';s=net.read_text()
inputs=[net,r/'src/audio_driver.v',r/'src/effects/guitar_fx_oversample.v',r/'tests/tb_oversample_gate.sv'];proof={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
a=s.index('module guitar_fx_oversample (');b=s.index('endmodule',a)+len('endmodule');(out/'oversample_gate.v').write_text(s[a:b])
(out/'oversample_rtl.v').write_text((r/'src/effects/guitar_fx_oversample.v').read_text().replace('module guitar_fx_oversample(','module guitar_fx_oversample_rtl('))
iv=os.environ.get('IVERILOG') or shutil.which('iverilog');vvp=os.environ.get('VVP') or shutil.which('vvp');args=[iv]+(['-B',os.environ['IVERILOG_LIB']] if os.environ.get('IVERILOG_LIB') else [])
args+=['-g2012','-s','tb_oversample_gate','-s','GSR','-o',str(out/'oversample_gate.vvp'),str(out/'oversample_gate.v'),str(out/'oversample_rtl.v'),str(r/'tests/tb_oversample_gate.sv'),'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v']
log=''
for cmd in (args,[vvp,str(out/'oversample_gate.vvp')]):
 p=subprocess.run(cmd,cwd=r,capture_output=True,text=True,timeout=900);log+=p.stdout+p.stderr;(out/'oversample_gate_log.txt').write_text(log)
 if p.returncode:raise RuntimeError(log[-2500:])
assert proof=={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
(out/'oversample_gate_hashes.json').write_text(json.dumps(proof,indent=2));print(log)
