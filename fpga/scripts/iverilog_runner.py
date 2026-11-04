"""Portable Icarus invocation; both Windows compiler stages must succeed."""
from pathlib import Path
import os, subprocess,hashlib,json,re
ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(os.environ.get('BASS_IVERILOG_HOME', str(ROOT.parent.parent / 'tmp/sim_tools/mingw64')))
ENV = os.environ.copy()
ENV['PATH'] = str(TOOLS / 'bin') + os.pathsep + ENV['PATH']
ENV['TMP'] = ENV['TEMP'] = str(ROOT / 'tests/runtime_temp')
Path(ENV['TMP']).mkdir(parents=True, exist_ok=True)
OUT = ROOT / 'tests/results'
OUT.mkdir(parents=True, exist_ok=True)
def run(command, name, timeout=1800):
    log=OUT/name
    if Path(command[0]).name.lower() not in ('vvp.exe','vvp'):
        child=subprocess.run(command,cwd=ROOT,env=ENV,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        text=child.stdout+child.stderr;code=child.returncode;log.write_text(text,encoding='utf-8')
    else:
        with log.open('w',encoding='utf-8') as stream:
            child=subprocess.Popen(command,cwd=ROOT,env=ENV,stdout=stream,stderr=subprocess.STDOUT)
            try:code=child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                child.kill();child.wait();raise
        text=log.read_text(encoding='utf-8',errors='replace')
    if code!=0:raise RuntimeError(f'{code}: {command}\n{text[-5000:]}')
    return text

def source_hashes(sources):
    pending=[Path(x) if Path(x).is_absolute() else ROOT/x for x in sources];seen=set();result={}
    while pending:
        p=pending.pop().resolve()
        if p in seen:continue
        seen.add(p)
        key=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()
        result[key]=hashlib.sha256(p.read_bytes()).hexdigest()
        code=p.read_text(encoding='utf-8',errors='replace')
        names=re.findall(r'`include\s+"([^"\n]+)"',code)+re.findall(r'\$readmem[hb]\s*\(\s*"([^"\n]+)"',code)
        pending.extend(ROOT/n for n in names if (ROOT/n).is_file())
    return result

def assert_source_hashes(record):
    for name,value in record.items():
        p=Path(name) if Path(name).is_absolute() else ROOT/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=value:raise RuntimeError('Test source changed: '+name)

def compile_sim(top, sources):
    record=source_hashes(sources)
    executable = f'tests/results/{top}.vvp'
    if os.name == 'nt':
        preprocessed = f'tests/runtime_temp/{top}.v'
        run([str(TOOLS / 'bin/iverilog.exe'), '-E', '-B', str(TOOLS / 'lib/ivl'),
             '-g2012', '-o', preprocessed, *sources], top + '_preprocess.log')
        config = [f'root:{top}', f'basedir:{TOOLS / "lib/ivl"}']
        config += [f'module:{TOOLS / "lib/ivl" / (name + ".vpi")}' for name in
                   ('system', 'vhdl_sys', 'vhdl_textio', 'v2005_math', 'va_math', 'v2009')]
        config += ['generation:2012', 'generation:xtypes', 'generation:io-range-error',
                   'generation:shared-loop-index', 'generation:icarus-misc',
                   'warnings:n', 'ignore_missing_modules:false', f'out:{executable}',
                   'iwidth:32', 'widthcap:65536']
        cfg = f'tests/runtime_temp/{top}.cfg'
        (ROOT / cfg).write_text('\n'.join(config) + '\n', encoding='utf-8')
        run([str(TOOLS / 'lib/ivl/ivl.exe'), '-C', cfg, '-C', str(TOOLS / 'lib/ivl/vvp.conf'),
             '--', preprocessed], top + '_compile.log')
    else:
        run([str(TOOLS / 'bin/iverilog'), '-g2012', '-s', top, '-o', executable, *sources],
            top + '_compile.log')
    assert_source_hashes(record)
    (OUT/(top+'_source_sha256.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
    return executable

def simulate(executable, name, *arguments, timeout=1800):
    record=json.loads((ROOT/Path(executable).with_name(Path(executable).stem+'_source_sha256.json')).read_text())
    assert_source_hashes(record)
    output=run([str(TOOLS / ('bin/vvp.exe' if os.name == 'nt' else 'bin/vvp')),executable,*arguments],name,timeout=timeout)
    assert_source_hashes(record)
    return output
