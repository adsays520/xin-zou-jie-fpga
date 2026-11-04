import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
OUTPUT = ROOT / 'test_results'
SIM = PROJECT.parent / 'tmp/sim_tools/mingw64'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--board', action='store_true')
    parser.add_argument('--hall-board', action='store_true')
    parser.add_argument('--touch-hall', action='store_true')
    parser.add_argument('--touch-hall-backpressure', action='store_true')
    parser.add_argument('--esp-wire', action='store_true')
    parser.add_argument('--core', type=int, default=0)
    parser.add_argument('--repair-units', action='store_true')
    args = parser.parse_args()
    if (args.touch_hall or args.touch_hall_backpressure or args.esp_wire) and (args.board or args.hall_board or args.core or args.repair_units):
        parser.error('Touch/Hall link suites run independently of the other suites')
    if sum((args.touch_hall, args.touch_hall_backpressure, args.esp_wire)) > 1:
        parser.error('Choose the normal or backpressure Touch/Hall link suite')
    OUTPUT.mkdir(exist_ok=True)
    environment = os.environ.copy()
    environment['PATH'] = str(SIM / 'bin') + os.pathsep + environment['PATH']
    environment['TMP'] = environment['TEMP'] = str(OUTPUT)
    def run(command, name, timeout=1800):
        with (OUTPUT / (name + '.log')).open('w', encoding='utf-8') as log:
            result = subprocess.run([str(value) for value in command], cwd=PROJECT, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        output = (OUTPUT / (name + '.log')).read_text(encoding='utf-8', errors='replace')
        print(output[-5000:], flush=True)
        if result.returncode or 'FATAL' in output or 'ERROR:' in output:
            raise RuntimeError(f'{name} failed')
        return output
    suites = []
    if args.touch_hall or args.touch_hall_backpressure or args.esp_wire:
        if args.esp_wire:
            run([sys.executable, '-B', ROOT / 'export_esp_hall_vectors.py'], 'esp_hall_wire_export')
        link_sources = ['violin_r15/s3_spi_link.v','violin_r15/touch_to_command.v',
            'violin_r15/touch_legacy.v','violin_r15/violin_touch_control.v','src/s3_control_ingress.v',
            'violin_r15/guitar_uart_trigger.v','tests/tb_touch_hall_link.sv']
        link_tops = ['tb_touch_hall_esp_vectors'] if args.esp_wire else ['tb_touch_hall_link'] if args.touch_hall else ['tb_touch_hall_backpressure',
            'tb_touch_hall_piano_backpressure','tb_touch_hall_bass_backpressure','tb_touch_hall_violin_backpressure']
        suites.extend((top, link_sources, []) for top in link_tops)
    elif args.repair_units:
        suites.extend([
            ('tb_violin_space_equivalence',['violin_r15/master_space_fx.v','violin_r15/space_gold.v','violin_r15/tb_space.sv'],[]),
            ('tb_excitation_cache_hazards',['violin_r15/scratch_cache.v','tests/tb_excitation_cache_hazards.sv','tests/results/excitation_ddr_r7/prim_sim_data_only.v'],[]),
        ])
    elif args.core:
        run([sys.executable, '-B', ROOT / 'verify_core.py', '--frames', args.core], 'golden')
        suites.append(('tb_violin_core', ['violin_r15/violin_core.v', 'violin_r15/tb_violin_core.v'], ['-P', f'tb_violin_core.FRAMES={args.core}']))
    else:
        suites.extend([
            ('tb_pluck_event_queue', ['violin_r15/pluck_event_queue.v','tests/tb_pluck_event_queue.sv'], []),
            ('tb_touch_to_command', ['violin_r15/touch_to_command.v','violin_r15/touch_legacy.v','violin_r15/violin_touch_control.v','tests/tb_touch_to_command.sv'], []),
            ('tb_s3_ingress', ['src/s3_control_ingress.v','violin_r15/guitar_uart_trigger.v','tests/tb_s3_ingress.sv'], []),
            ('tb_s3_link', ['violin_r15/s3_spi_link.v','tests/tb_s3_link.sv'], []),
            ('tb_violin_controls', ['violin_r15/guitar_uart_trigger.v','violin_r15/touch_to_command.v','violin_r15/touch_legacy.v','violin_r15/violin_touch_control.v','violin_r15/tb_controls.sv'], []),
        ])
    if args.board or args.hall_board:
        entries = ET.parse(PROJECT / 'guitar_ddr_violin_r15.gprj').getroot().find('FileList')
        sources = [entry.attrib['path'] for entry in entries if entry.attrib['type']=='file.verilog' and 'TangMega-138KPro-example-main' not in entry.attrib['path']]
        sources = [('tests/drum_sample_rom_model.v' if source=='src/drums/drum_sample_rom.v' else 'tests/piano_loop_rom_model.v' if source=='src/piano_loop/piano_loop.v' else source) for source in sources]
        sources.extend(['tests/results/bram_r13/board/guitar_audio_top_r5.v','tests/results/bram_r13/board/guitar_poly32_tdm_r5.v','tests/results/bram_r13/board/guitar_voice_tdm_core_r5.v','tests/results/bram_r13/board/context_gold.v','src/poly32/poly32_scratch_bank.v','src/poly32/poly32_road_bank.v','tests/ddr_app_model.sv','tests/results/bram_r13/board/mock.sv','tests/results/excitation_ddr_r7/prim_sim_data_only.v','tests/tb_pt8211_output.sv','violin_r15/tb_board.sv'])
        suites.append(('tb_violin_switch', sources+['violin_r15/tb_switch.sv'], []))
        suites.append(('tb_violin_board', sources, ['-P', 'tb_violin_board.HALL_ONLY=1'] if args.hall_board else []))
    proof = {}
    for top, sources, options in suites:
        executable = f'violin_r15/test_results/{top}.vvp'
        hashes = {source:hashlib.sha256((PROJECT/source).read_bytes()).hexdigest() for source in sources}
        if args.esp_wire:
            hashes.update(json.loads((OUTPUT / 'esp_hall_wire_vectors.json').read_text())['source_sha256'])
            for extra in ('violin_r15/export_esp_hall_vectors.py', 'violin_r15/test_results/esp_hall_wire_vectors.hex'):
                hashes[extra] = hashlib.sha256((PROJECT / extra).read_bytes()).hexdigest()
        run([SIM/'bin/iverilog.exe','-B',SIM/'lib/ivl','-g2012','-Wall','-s',top,*options,'-o',executable,*sources],top+'_compile')
        output = run([SIM/'bin/vvp.exe',executable],top+'_run')
        if 'PASS ' not in output:
            raise RuntimeError(f'{top} did not confirm completion')
        if any(hashlib.sha256((PROJECT/source).read_bytes()).hexdigest()!=value for source,value in hashes.items()):
            raise RuntimeError(f'{top} source changed during validation')
        proof[top] = hashes
    (OUTPUT / ('esp_hall_wire_proof.json' if args.esp_wire else 'touch_hall_backpressure_proof.json' if args.touch_hall_backpressure else 'touch_hall_link_proof.json' if args.touch_hall else 'core_proof.json' if args.core else 'hall_integration_proof.json' if args.hall_board else 'integration_proof.json')).write_text(json.dumps(proof, indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
