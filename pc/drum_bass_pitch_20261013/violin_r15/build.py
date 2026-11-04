import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
BASE = 'guitar_audio_violin_r15'
GOWIN = Path('D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe')


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    project = PROJECT / 'guitar_ddr_violin_r15.gprj'
    paths = {project}
    for entry in ET.parse(project).getroot().find('FileList'):
        paths.add((PROJECT/entry.attrib['path']).resolve())
    for directory in [PROJECT/'src', ROOT/'rom']:
        paths.update(path for path in directory.rglob('*') if path.is_file() and path.suffix in {'.hex','.vh','.mi','.bin'})
    return {str(path.relative_to(PROJECT)) if path.is_relative_to(PROJECT) else str(path):checksum(path) for path in sorted(paths)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['archive-initial','archive-current','syn','pnr'])
    args = parser.parse_args()
    if args.phase.startswith('archive-'):
        label='initial_diagnostic' if args.phase=='archive-initial' else datetime.now().strftime('setup_failed_%Y%m%d_%H%M%S')
        destination=ROOT/'checkpoints'/label
        destination.mkdir(parents=True,exist_ok=False)
        for directory in ['gwsynthesis','pnr']:
            for path in (PROJECT/'impl'/directory).glob(BASE+'*'):
                if path.is_file():
                    target=destination/directory/path.name
                    target.parent.mkdir(exist_ok=True)
                    shutil.copy2(path,target)
        for name in ['synthesis_console.log','pnr_console.log']:
            shutil.copy2(ROOT/'test_results'/name,destination/name)
        if args.phase=='archive-current':
            for path in ROOT.glob('*'):
                if path.is_file():
                    (destination/'source').mkdir(exist_ok=True)
                    shutil.copy2(path,destination/'source'/path.name)
            for path in (ROOT/'test_results').glob('*'):
                if path.suffix in {'.log','.json'}:
                    (destination/'validation').mkdir(exist_ok=True)
                    shutil.copy2(path,destination/'validation'/path.name)
            shutil.copy2(PROJECT/'guitar_ddr_violin_r15.gprj',destination/'guitar_ddr_violin_r15.gprj')
        print(f'Preserved initial diagnostic: {destination}')
        return
    paths=source_hashes()
    record=ROOT/'test_results/final_synthesis.json'
    if args.phase=='pnr':
        proof=json.loads(record.read_text(encoding='utf-8'))
        if not proof['passed'] or proof['sources']!=paths:
            raise RuntimeError('Current sources do not match the successful final synthesis')
    log_path=ROOT/f'test_results/final_{args.phase}_console.log'
    command=GOWIN
    script='build_ddr_violin_r15.tcl' if args.phase=='syn' else 'pnr_ddr_violin_r15.tcl'
    started=datetime.now().astimezone().isoformat()
    with log_path.open('w',encoding='utf-8') as log:
        result=subprocess.run([str(command),script],cwd=PROJECT,stdout=log,stderr=subprocess.STDOUT,timeout=5400)
    text=log_path.read_text(encoding='utf-8',errors='replace')
    completed='GowinSynthesis finish' in text if args.phase=='syn' else 'R10 Pro DDR PASS:' in text and 'pulse' in text.lower()
    passed=result.returncode==0 and completed and paths==source_hashes()
    proof={'phase':args.phase,'started':started,'finished':datetime.now().astimezone().isoformat(),'passed':passed,'returncode':result.returncode,'sources':paths}
    (ROOT/f'test_results/final_{"synthesis" if args.phase=="syn" else "pnr"}.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(text[-5000:])
    if not passed:
        raise RuntimeError(f'R15 final {args.phase} did not pass; inspect {log_path}')


if __name__=='__main__':
    main()
