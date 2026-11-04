from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

from build import checksum, source_hashes

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent


def main():
    for name, arguments in [('timing',['--strict']),('audit',[])]:
        with (ROOT/f'test_results/seal_{name}.log').open('w',encoding='utf-8') as log:
            subprocess.run([sys.executable,'-B',str(ROOT/f'{name}.py'),*arguments],cwd=PROJECT,stdout=log,stderr=subprocess.STDOUT,check=True)
    report=json.loads((ROOT/'test_results/audit.json').read_text(encoding='utf-8'))
    if not all(result['complete'] and not result['failure'] for result in report['tests'].values()) or len(report['tests'])!=6:
        raise RuntimeError('Not all six RTL validation groups completed successfully')
    for name in ['core_proof.json','integration_proof.json']:
        proof=json.loads((ROOT/'test_results'/name).read_text(encoding='utf-8'))
        for sources in proof.values():
            for relative,digest in sources.items():
                if checksum(PROJECT/relative)!=digest:
                    raise RuntimeError(f'Validated source changed: {relative}')
    destination=ROOT/'checkpoints'/datetime.now().strftime('timing_passed_%Y%m%d_%H%M%S')
    destination.mkdir(parents=True,exist_ok=False)
    files={}
    def copy(source,relative):
        target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        files[relative]={'sha256':checksum(target),'source':str(source)}
    base='guitar_audio_violin_r15'
    for suffix in ['.fs','.rpt.txt','_tr_content.html']:
        copy(PROJECT/'impl/pnr'/(base+suffix),'fpga/'+base+suffix)
    for path in ROOT.glob('*'):
        if path.is_file():
            copy(path,'source/violin_r15/'+path.name)
    for path in (ROOT/'rom').iterdir():
        if path.is_file():
            copy(path,'source/violin_r15/rom/'+path.name)
    for name in ['guitar_ddr_violin_r15.gprj','build_ddr_violin_r15.tcl','pnr_ddr_violin_r15.tcl']:
        copy(PROJECT/name,'source/'+name)
    for path in (ROOT/'test_results').iterdir():
        if path.suffix in {'.json','.log'}:
            copy(path,'validation/'+path.name)
    firmware=PROJECT.parent/'esp32S3/Guitar_Controller_R15/build_r15'
    for relative in ['Guitar_Controller_S3_R15.bin','bootloader/bootloader.bin','partition_table/partition-table.bin','flasher_args.json']:
        copy(firmware/relative,'controller_s3/'+relative)
    acceptance={'status':'rtl_and_constrained_timing_pass_hardware_unverified','sources':source_hashes(),'files':files,'hardware_listening_verified':False,'source_snapshot_is_standalone':False}
    (destination/'ACCEPTED.json').write_text(json.dumps(acceptance,indent=2)+'\n',encoding='utf-8')
    print(f'Preserved validated R15 checkpoint: {destination}')


if __name__=='__main__':
    main()
