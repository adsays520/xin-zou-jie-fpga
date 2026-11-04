import json
import os
import re
import shutil
import subprocess

from iverilog_runner import ROOT, OUT, TOOLS, ENV, run as compiler_run, source_hashes, assert_source_hashes
from xsim_runner import run


def main():
    run_name = os.environ.get('PANEL_V14_RUN', 'diagnostic')
    assert re.fullmatch(r'panel_v14_build(?:_retry[0-9]+)?|diagnostic', run_name)
    project = ROOT / 'tests/runtime_temp' / ('drum_gate_project_v14_' + run_name)
    project.mkdir(exist_ok=False)
    shutil.copytree(ROOT / 'src/drums', project / 'src/drums')
    shutil.copy2(ROOT / 'src/performance_mixer.v', project / 'src/performance_mixer.v')
    files = ('src/drums/kick_modal.v', 'src/drums/drum_synth.v', 'src/performance_mixer.v')
    file_list = ''.join(f'<File path="{name}" type="file.verilog" enable="1"/>' for name in files)
    (project / 'drum_gate.gprj').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE gowin-fpga-project>\n<Project><Template>FPGA</Template><Version>5</Version>'
        '<Device name="GW5AST-138B" pn="GW5AST-LV138FPG676AES">gw5ast138b-002</Device>'
        '<FileList>' + file_list + '</FileList></Project>\n', encoding='utf-8')
    (project / 'build.tcl').write_text('open_project drum_gate.gprj\n'
        'set_option -include_path [pwd]\nset_option -top_module drum_synth\n'
        'set_option -output_base_name drum_gate\nset_option -global_freq 50.000\nrun syn\nexit\n')
    with (OUT / 'drum_gate_v14_synthesis.log').open('w', encoding='utf-8') as stream:
        result = subprocess.run(['D:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe', 'build.tcl'],
            cwd=project, env=ENV, stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    assert result.returncode == 0
    synthesis_log = (OUT / 'drum_gate_v14_synthesis.log').read_text(errors='replace')
    assert 'GowinSynthesis finish' in synthesis_log and 'ERROR (' not in synthesis_log
    netlist = 'tests/results/drum_v14_functional_netlist.vg'
    shutil.copy2(project / 'impl/gwsynthesis/drum_gate.vg', ROOT / netlist)
    temporary = ROOT / 'tests/runtime_temp'
    raw = temporary / 'drums_v14_preprocessed.v'
    compiler_run([str(TOOLS / 'bin/iverilog.exe'), '-E', '-B', str(TOOLS / 'lib/ivl'),
        '-g2012', '-o', str(raw), 'src/drums/drum_synth.v', 'src/drums/kick_modal.v',
        'src/performance_mixer.v'], 'drum_gate_v14_preprocess.log')
    rtl = raw.read_text()
    for module in ('drum_synth', 'kick_modal', 'drum_parameter_bank', 'performance_peak_control', 'performance_mixer'):
        rtl = re.sub(r'\b' + module + r'\b', module + '_rtl', rtl)
    (temporary / 'drums_v14_rtl.v').write_text(rtl, encoding='utf-8')
    payload = (ROOT / 'sd_card/DRUMS.BIN').read_bytes()
    (temporary / 'drums_bytes.hex').write_text(''.join(f'{value:02x}\n' for value in payload), encoding='utf-8')
    primitive = os.environ.get('GOWIN_PRIM_SIM', 'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
    rtl_name = 'tests/runtime_temp/drums_v14_rtl.v'
    testbench = 'tests/tb_drum_sd_gate_v14.sv'
    binding = source_hashes([netlist, rtl_name, testbench, primitive,
        'src/drums/drum_synth.v', 'src/drums/kick_modal.v', 'src/performance_mixer.v',
        'tests/runtime_temp/drums_bytes.hex', 'scripts/verify_drum_gate_v14.py'])
    for path in (project / 'src').rglob('*'):
        if path.is_file():
            name = path.relative_to(project).as_posix()
            assert path.read_bytes() == (ROOT / name).read_bytes()
            binding.update(source_hashes([str(path)]))
    run('xvlog.exe', ['--sv', netlist, rtl_name, testbench, primitive], 'drum_gate_v14_compile.log')
    run('xelab.exe', ['tb_drum_sd_gate_v14', '-s', 'drum_gate_v14', '--relax', '--O2'], 'drum_gate_v14_elaborate.log')
    log = run('xsim.exe', ['drum_gate_v14', '-R', '-log', str(OUT / 'drum_gate_v14_internal.log')],
              'drum_gate_v14.log', timeout=3000)
    assert 'PASS DRUM SD GATE V14:' in log
    assert_source_hashes(binding)
    (OUT / 'drum_sd_gate_v14_result.json').write_text(json.dumps(
        {'passed': True, 'sources': binding, 'log': log, 'synthesis_returncode': result.returncode,
         'scope': 'fresh source-bound standalone Gowin mapped drum netlist vs RTL; no DDR IP simulation or board listening'}, indent=2), encoding='utf-8')
    print(log, flush=True)


if __name__ == '__main__':
    main()
