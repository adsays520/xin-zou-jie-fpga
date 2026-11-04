import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(relative):
    manifest_path = PROJECT / relative
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    entries = manifest['files']
    if isinstance(entries, dict):
        entries = [{'path':path, 'sha256':value} for path, value in entries.items()]
    changed = []
    for entry in entries:
        candidates = [PROJECT / entry['path'], manifest_path.parent / entry['path']]
        path = next((candidate for candidate in candidates if candidate.is_file() and digest(candidate)==entry['sha256']), None)
        if path is None:
            changed.append(entry['path'])
    if changed:
        raise RuntimeError(f'Preservation failure in {relative}: {changed}')
    return len(entries)


def main():
    preserved = {name:check_manifest(name) for name in ['S3_R13_BRAM_SHA256.json','experiments/violin_v2/V2B_SHA256.json','experiments/violin_v3/V3C_SHA256.json']}
    zipper = PROJECT.parent / 'output/R13_Complete_20261017.zip'
    expected = '8cc4d5e3620b9e97220c6f628fa1c7d191f6a072a4507f66e30c88210bb5218d'
    if digest(zipper) != expected:
        raise RuntimeError('Preserved R13 complete package changed')
    resource_path = PROJECT / 'impl/gwsynthesis/guitar_audio_violin_r15_syn_rsc.xml'
    resource = ET.parse(resource_path).getroot()
    violin = resource.find(".//SubModule[@name='u_violin_channel']")
    logs = {}
    for name in ['tb_violin_core_run','tb_violin_controls_run','tb_violin_switch_run','tb_violin_space_equivalence_run','tb_excitation_cache_hazards_run','tb_violin_board_run']:
        path = ROOT / f'test_results/{name}.log'
        if path.exists():
            text = path.read_text(encoding='utf-8',errors='replace')
            marker = 'PASS R15 whole-board' if name=='tb_violin_board_run' else 'PASS '
            logs[name] = {'complete':marker in text, 'pass_lines':[line for line in text.splitlines() if line.startswith('PASS ')], 'failure':bool(re.search('FATAL|ERROR:',text))}
    firmware = PROJECT.parent / 'esp32S3/Guitar_Controller_R15/build_r15/Guitar_Controller_S3_R15.bin'
    firmware_result = {'built':firmware.is_file(),'sha256':digest(firmware) if firmware.is_file() else None}
    report = {'preserved_files':preserved,'r13_package_sha256':expected,'synthesis_total':resource.attrib,'violin_synthesis':violin.attrib if violin is not None else {},'tests':logs,'s3_firmware':firmware_result,'hardware_listening_verified':False}
    (ROOT / 'test_results/audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
