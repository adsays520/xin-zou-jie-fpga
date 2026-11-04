import hashlib
import json
from pathlib import Path

from iverilog_runner import ROOT, OUT, compile_sim, simulate

reference = ROOT.parent / "ensemble_hall_v4/src/drums/drum_synth.v"
source = reference.read_text(encoding="utf-8")
snapshot = ROOT / "tests/runtime_temp/drum_synth_v4_reference.v"
snapshot.write_text(source.replace("module drum_synth(", "module drum_synth_v4_reference(", 1), encoding="utf-8")
sources = ["src/drums/drum_synth.v", str(snapshot), "src/drums/kick_modal.v",
           "src/performance_mixer.v", "tests/tb_drum_routing_v6.sv"]
executable = compile_sim("tb_drum_routing_v6", sources)
log = simulate(executable, "drum_routing_v6.log", timeout=1800)
assert "PASS DRUM ROUTING V6:" in log, log
assert reference.read_text(encoding="utf-8") == source
proof = {
    "passed": True,
    "reference": str(reference),
    "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256((ROOT / sources[0]).read_bytes()).hexdigest(),
    "scope": "RTL cycle-exact stereo PCM, schedule, phase and square-mode reference comparison",
    "physical_timing_accepted": False,
    "log": log,
}
(OUT / "drum_routing_v6.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
print(log, flush=True)
