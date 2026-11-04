import json

from iverilog_runner import ROOT, OUT, compile_sim, simulate
from make_sd_v7_fixture import make_image

for selected_case in range(7):
    make_image(selected_case)
executable = compile_sim("tb_drum_sd_v7", ["src/storage/piano_sd_boot.v", "src/drums/drum_parameter_bank.v",
                                         "tests/tb_drum_sd_v7.sv"])
logs = []
for selected_case in range(7):
    log = simulate(executable, f"drum_sd_v7_case{selected_case}.log", f"+CASE={selected_case}")
    assert "PASS DRUM SD V7" in log and "ERROR" not in log, log
    print(log, flush=True)
    logs.append(log)
(OUT / "drum_sd_v7_result.json").write_text(json.dumps({"passed": True, "cases": 7, "logs": logs}, indent=2), encoding="utf-8")
