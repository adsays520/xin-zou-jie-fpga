"""Gowin netlist comparison using installed Vivado/XSim official primitive models."""
from pathlib import Path
import os,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tests/results'
VIVADO=Path(os.environ.get('XILINX_VIVADO','D:/vivado/2025.2/Vivado'))
BINARY=VIVADO/'bin/unwrapped/win64.o'
ENV=os.environ.copy()
ENV['PATH']=';'.join(str(VIVADO/p) for p in ('lib/win64.o','tps/win64/jre21.0.5_11/bin/server','tps/win64/jre21.0.5_11/bin','tps/win64/python-3.13.0','tps/mingw/6.2.0/win64.o/nt/bin','tps/mingw/6.2.0/win64.o/nt/libexec/gcc/x86_64-w64-mingw32/6.2.0','tps/win64'))+';'+ENV['PATH']
ENV['RDI_BASEROOT']=str(VIVADO.parent)
ENV['RDI_INSTALLROOT']=str(VIVADO.parent.parent)
ENV['RDI_PLATFORM']='win64'
for key,value in {'RDI_DATADIR':'data','RDI_LIBDIR':'lib/win64.o','RDI_BINDIR':'bin','RDI_APPROOT':'','HDI_APPROOT':'','TCL_LIBRARY':'tps/tcl/tcl8.6','XILINX_VIVADO':''}.items():ENV[key]=str(VIVADO/value)
ENV['TMP']=ENV['TEMP']=str(ROOT/'tests/runtime_temp')
def run(exe,args,log,timeout=1800):
 with (OUT/log).open('w',encoding='utf-8') as f:
  p=subprocess.run([str(BINARY/exe),*args],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 text=(OUT/log).read_text(encoding='utf-8',errors='replace')
 if p.returncode:raise RuntimeError(f'{exe}: {p.returncode}\n{text[-6000:]}')
 return text
