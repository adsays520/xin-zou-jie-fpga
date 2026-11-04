import json
import os

from iverilog_runner import ROOT, OUT, source_hashes, assert_source_hashes
from xsim_runner import run

netlist = "tests/runtime_temp/drum_gate_project/impl/gwsynthesis/drum_gate.vg"
sources = [netlist, "tests/runtime_temp/drums_rtl.v", "tests/tb_drum_sd_gate_v7.sv",
           "src/drums/drum_synth.v", "src/drums/drum_parameter_bank.v", "src/drums/kick_modal.v",
           "src/performance_mixer.v", "tests/runtime_temp/drums_bytes.hex",
           os.environ.get("GOWIN_PRIM_SIM", "D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v")]
binding = source_hashes(sources)
primitive = sources[-1]
run("xvlog.exe", ["--sv", netlist, "tests/runtime_temp/drums_rtl.v", "tests/tb_drum_sd_gate_v7.sv", primitive], "drum_sd_gate_v7_compile.log")
run("xelab.exe", ["tb_drum_sd_gate_v7", "-s", "drum_sd_gate_v7", "--relax", "--O2"], "drum_sd_gate_v7_elaborate.log")
log = run("xsim.exe", ["drum_sd_gate_v7", "-R", "-log", str(OUT / "drum_sd_gate_v7_internal.log")], "drum_sd_gate_v7.log")
assert "PASS DRUM SD GATE V7:" in log, log
assert_source_hashes(binding)
(OUT / "drum_sd_gate_v7_result.json").write_text(json.dumps({"passed": True, "sources": binding, "log": log}, indent=2), encoding="utf-8")
print(log, flush=True)
