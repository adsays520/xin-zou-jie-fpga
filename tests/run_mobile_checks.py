from pathlib import Path
import sys,json,subprocess,binascii,os,shutil
ROOT=Path(__file__).resolve().parents[1]
HOST=ROOT/'pc/drum_bass_pitch_20261013'
sys.path[:0]=[str(HOST/'violin_r15'),str(HOST/'host')]
from arrangement_model import Project
from arrangement_playback import compile_plan
from drawn_synth import prepare_wave
ASSETS=ROOT/'android/app/src/main/assets'
NODE=os.environ.get('NODE_EXE') or shutil.which('node')
if not NODE:raise RuntimeError('Node.js is required; install it or set NODE_EXE')
def packets(data):
    result=[]
    while data:
        if data[0]!=165:raise ValueError('bad SOF')
        n=266 if data[1]==176 else 38 if data[1] in (17,33,49) else 6
        if len(data)<n:raise ValueError('truncated packet')
        result.append(data[:n].hex());data=data[n:]
    return result
def main():
    for p in ASSETS.glob('*.js'):
        subprocess.run([NODE,'--check',p],check=True,capture_output=True)
    projects=list((ROOT/'pc/Music_Demos/projects').glob('*.tang.json'))
    fixtures=[];expected=[]
    for path in projects:
        p=Project.load(path);plan=compile_plan(p,True,ensemble=True)
        prep=[b for blob,_ in plan.preparation for b in packets(blob)]
        setup=[b for e in plan.events if e.at==0 and e.priority<3 for b in packets(e.data)]
        notes=[(e.at,b) for e in plan.events if not(e.at==0 and e.priority<3) for b in packets(e.data)]
        expected.append((path.name,prep+setup,notes));fixtures.append(p.to_dict())
    wave=[__import__('math').sin(i*.037)+.2*__import__('math').sin(i*.13) for i in range(1024)]
    payload=dict(projects=fixtures,wave=wave)
    (ROOT/'tests/mobile_fixtures.json').write_text(json.dumps(payload),encoding='utf-8')
    script='''const fs=require('fs'),vm=require('vm');const p=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));const context={console,crypto:globalThis.crypto,TextEncoder,Uint8Array,window:{addEventListener(){}},document:{getElementById(){return {innerHTML:'',textContent:''};}},setTimeout,clearTimeout,setInterval,clearInterval,performance};vm.createContext(context);for(const name of ['protocol.js','tang.js','tang_core.js','app.js'])vm.runInContext(fs.readFileSync(process.argv[3]+'/'+name,'utf8'),context);context.input=p;process.stdout.write(vm.runInContext('JSON.stringify({plans:input.projects.map(p=>Tang.compile(p)),wave:waveBanks(input.wave)})',context));'''
    (ROOT/'tests/mobile_runner.cjs').write_text(script)
    proc=subprocess.run([NODE,ROOT/'tests/mobile_runner.cjs',ROOT/'tests/mobile_fixtures.json',ASSETS],capture_output=True,text=True,encoding='utf-8',check=True)
    actual=json.loads(proc.stdout);errors=[]
    for (name,prep,events),got in zip(expected,actual['plans']):
        gp=[b for e in got['preparation'] for b in packets(bytes.fromhex(e['hex']))]
        ge=[(e['at'],b) for e in got['events'] for b in packets(bytes.fromhex(e['hex']))]
        if prep!=gp:
            index=next((i for i,(a,b) in enumerate(zip(prep,gp)) if a!=b),min(len(prep),len(gp)))
            errors.append((name,'preparation',index,prep[index:index+1],gp[index:index+1]))
        if len(events)!=len(ge) or any(abs(a[0]-b[0])>1e-8 or a[1]!=b[1] for a,b in zip(events,ge)):
            index=next((i for i,(a,b) in enumerate(zip(events,ge)) if abs(a[0]-b[0])>1e-8 or a[1]!=b[1]),min(len(events),len(ge)))
            errors.append((name,'events',index,events[index:index+1],ge[index:index+1]))
    want=prepare_wave(wave);signed=lambda v:v-65536 if v>=32768 else v
    max_wave_error=max(abs(signed(a)-signed(b)) for a,b in zip(want,actual['wave']))
    if max_wave_error>1:errors.append(('wave','Q15 error',max_wave_error))
    report=dict(projects=len(projects),errors=errors,wave_max_lsb_error=max_wave_error)
    (ROOT/'tests/mobile_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False)[:4000])
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
