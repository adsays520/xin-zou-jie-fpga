import argparse
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import re

from build import source_hashes

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
BASE = PROJECT / 'impl/pnr/guitar_audio_violin_r15'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strict', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--hall-link', action='store_true')
    mode.add_argument('--hall-timing', action='store_true')
    args = parser.parse_args()
    candidate = 'hall_timing_v3' if args.hall_timing else 'hall_link_v2' if args.hall_link else None
    base = PROJECT / ('impl/pnr/guitar_audio_' + candidate) if candidate else BASE
    content = Path(str(base)+'_tr_content.html').read_text(encoding='utf-8',errors='replace')
    resources_text = Path(str(base)+'.rpt.txt').read_text(encoding='utf-8',errors='replace')
    timing = {}
    for kind in ['Setup','Hold']:
        match = re.search('Numbers of '+kind+r' Violated Endpoints</td>\s*<td>(\d+)</td>',content)
        timing[kind.lower()+'_violated_endpoints'] = int(match[1]) if match else None
    for clock,frequency in [('sys_clk',50),('ddr_user100',100),('mem400',400),('ddr_ref100',100)]:
        match = re.search('<td>'+clock+r'</td>\s*<td>'+f'{frequency:.3f}'+r'\(MHz\)</td>\s*<td[^>]*>([\d.]+)\(MHz\)</td>',content)
        timing[clock+'_fmax_mhz'] = float(match[1]) if match else None
    for kind,following in [('Setup','Hold_Slack_Table'),('Hold','Recovery_Slack_Table'),('Recovery','Removal_Slack_Table'),('Removal','MIN_PULSE_WIDTH_TABLE')]:
        section = content.split('name="'+kind+'_Slack_Table"',1)[1].split('name="'+following+'"',1)[0]
        values = [float(value) for value in re.findall(r'<tr[^>]*>\s*<td>\d+</td>\s*<td>([-\d.]+)</td>',section)]
        timing[kind.lower()+'_worst_slack_ns'] = min(values) if values else None
    section = content.split('name="MIN_PULSE_WIDTH_TABLE"',1)[1].split('</table>',1)[0]
    pulses = [float(value) for value in re.findall(r'<tr[^>]*>\s*<td>\d+</td>\s*<td>([-\d.]+)</td>',section)]
    timing['minimum_pulse_slack_ns'] = min(pulses) if pulses else None
    resources = {}
    for name in ['BSRAM','DSP','Register','Logic']:
        match = re.search(r'\b'+name+r'\s*\|\s*([\d.]+)/([\d.]+)',resources_text)
        if match:
            resources[name] = {'used':float(match[1]),'available':float(match[2])}
    paths = []
    for block in re.split(r'<h3>Path\d+</h3>',content)[1:]:
        fields = {}
        for name in ['Slack','From','To','Launch Clk','Latch Clk']:
            match = re.search('<td class="label">'+re.escape(name)+r'</td>\s*<td>([^<]+)</td>',block)
            if match:
                fields[name] = html.unescape(match[1])
        if 'Slack' in fields and 'From' in fields:
            fields['Slack'] = float(fields['Slack'])
            paths.append(fields)
    proof_path = PROJECT/('tests/results/' + candidate + '_build/proof.json') if candidate else ROOT/'test_results/final_pnr.json'
    proof = json.loads(proof_path.read_text(encoding='utf-8')) if proof_path.exists() else {}
    sources = source_hashes()
    if candidate:
        script = 'build_' + candidate + '.tcl'
        sources[script] = hashlib.sha256((PROJECT / script).read_bytes()).hexdigest()
    current = proof.get('sources')==sources
    fresh = bool(proof) and Path(str(base)+'_tr_content.html').stat().st_mtime>=datetime.fromisoformat(proof['started']).timestamp()
    passing = current and fresh and proof.get('passed',False)
    passing = passing and all(timing.get(kind+'_violated_endpoints')==0 for kind in ['setup','hold'])
    passing = passing and all(timing.get(clock+'_fmax_mhz',0)>=frequency for clock,frequency in [('sys_clk',50),('ddr_user100',100),('mem400',400),('ddr_ref100',100)])
    passing = passing and all(value is not None and value>=0 for key,value in timing.items() if key.endswith('_slack_ns'))
    bitstream = Path(str(base)+'.fs')
    result = {'passed':bool(passing),'current_sources_match':current,'fresh_outputs':fresh,'timing':timing,'resources':resources,'worst_paths':sorted(paths,key=lambda entry:entry['Slack'])[:12], 'bitstream_sha256':hashlib.sha256(bitstream.read_bytes()).hexdigest() if bitstream.exists() else None,'hardware_listening_verified':False}
    output = PROJECT/('tests/results/' + candidate + '_build/timing.json') if candidate else ROOT/'test_results/timing.json'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if args.strict and not passing:
        raise SystemExit('R15 constrained timing has not passed')


if __name__=='__main__':
    main()
