from pathlib import Path
import os,subprocess,shutil
r=Path(__file__).resolve().parents[1];out=r/'tests/results'
iv=os.environ.get('IVERILOG') or shutil.which('iverilog');vvp=os.environ.get('VVP') or shutil.which('vvp')
log=''
for top,file,module in [('tb_audio_timing_exact','audio_driver.v','audio_drive'),('tb_oversample_exact','effects/guitar_fx_oversample.v','guitar_fx_oversample')]:
 old=r/'tests/reference'/(Path(file).stem+'_before_samples.v');new=out/(module+'_updated.v')
 new.write_text((r/'src'/file).read_text().replace('module '+module+'(','module '+module+'_updated('))
 args=[iv]+(['-B',os.environ['IVERILOG_LIB']] if os.environ.get('IVERILOG_LIB') else [])
 args+=['-g2012','-s',top,'-o',str(out/(top+'.vvp')),str(old),str(new),str(r/'tests/tb_audio_timing_exact.sv')]
 for cmd in (args,[vvp,str(out/(top+'.vvp'))]):
  p=subprocess.run(cmd,cwd=r,capture_output=True,text=True,timeout=600);log+=p.stdout+p.stderr
  (out/'audio_timing_exact_log.txt').write_text(log,encoding='utf-8')
  if p.returncode:raise RuntimeError(log[-2500:])
print(log)
