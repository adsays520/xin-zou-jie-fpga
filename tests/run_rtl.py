from pathlib import Path
import os, subprocess, json, zipfile, shutil
ROOT=Path(__file__).resolve().parent
TOOLS=Path(os.environ['IVERILOG_ROOT']) if 'IVERILOG_ROOT' in os.environ else Path(shutil.which('iverilog') or 'iverilog').resolve().parent.parent
if not (TOOLS/'bin/iverilog.exe').is_file():raise RuntimeError('Install Icarus Verilog or set IVERILOG_ROOT to its root (bin/ and lib/ivl/).')
ENV=os.environ.copy();ENV['PATH']=str(TOOLS/'bin')+os.pathsep+ENV['PATH'];ENV['TEMP']=ENV['TMP']=str(ROOT)
def run(cmd,name):
 p=subprocess.run([str(x) for x in cmd],cwd=ROOT,env=ENV,capture_output=True,timeout=90)
 out=p.stdout+p.stderr;(ROOT/name).write_bytes(out)
 if p.returncode:raise RuntimeError(f'{p.returncode}: '+out.decode(errors='replace')[-3000:])
 return out.decode(errors='replace')
def compile_sim(top,sources):
 pre=ROOT/(top+'.pre.v');exe=ROOT/(top+'.vvp');cfg=ROOT/(top+'.cfg')
 run([TOOLS/'bin/iverilog.exe','-E','-B',TOOLS/'lib/ivl','-g2012','-o',pre,*sources],top+'_pre.log')
 config=['root:'+top,'basedir:'+str(TOOLS/'lib/ivl')]+['module:'+str(TOOLS/'lib/ivl'/(n+'.vpi')) for n in ('system','vhdl_sys','vhdl_textio','v2005_math','va_math','v2009')]+['generation:2012','generation:xtypes','generation:io-range-error','generation:shared-loop-index','generation:icarus-misc','warnings:n','ignore_missing_modules:false','out:'+str(exe),'iwidth:32','widthcap:65536']
 cfg.write_text('\n'.join(config)+'\n')
 run([TOOLS/'lib/ivl/ivl.exe','-C',cfg,'-C',TOOLS/'lib/ivl/vvp.conf','--',pre],top+'_compile.log')
 return exe
if __name__=='__main__':
 src=ROOT.parent/'fpga/src'
 exe=compile_sim('tb_s3_bulk',[ROOT/'tb_s3_bulk.v',src/'s3_bulk_buffer.v'])
 print(run([TOOLS/'bin/vvp.exe',exe],'bulk_test.log'))
