from datetime import datetime, timedelta, timezone
import json
import os
import subprocess
import sys
import time

from build_hall_piano_v4 import ROOT, GOWIN, digest, source_hashes
from iverilog_runner import assert_source_hashes

OUTPUT = ROOT / "tests/results/routing_v7_build"
STATE = OUTPUT / "pipeline_state.json"


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def inputs():
    result = source_hashes()
    for name in ("scripts/run_routing_v7.py", "scripts/check_routing_v7_netlist.py", "sd_card/DRUMS.BIN"):
        result[name] = digest(ROOT / name)
    return result


def verify_scope():
    changed = []
    reference = ROOT.parent / "ensemble_hall_v6"
    for directory in ("src", "ip", "constraints", "violin_r15"):
        for path in (ROOT / directory).rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            name = path.relative_to(ROOT).as_posix()
            if not (reference / name).exists() or digest(path) != digest(reference / name):
                changed.append(name)
    allowed = {"src/drums/drum_synth.v", "src/drums/drum_machine.v", "src/drums/kick_modal.v",
               "src/drums/drum_parameter_bank.v", "src/drums/rom/drum_bank.hex",
               "src/drums/rom/drum_bank_config.vh", "src/storage/piano_sd_boot.v", "src/guitar_audio_top.v"}
    assert set(changed) == allowed, changed
    for name in ("sd_card/PIANOSMS.BIN", "host/assets/piano_sms_ddr.bin", "guitar_audio_low_speed.gprj"):
        assert digest(ROOT / name) == digest(reference / name), name
    return {"changed_files": sorted(changed), "baseline": "v6",
            "clocks_constraints_IP_piano_data_unchanged": True}


def verify_tests():
    for name in ("drum_v7_result.json", "drum_sd_v7_result.json", "drum_sd_gate_v7_result.json"):
        result = json.loads((ROOT / "tests/results" / name).read_text(encoding="utf-8"))
        assert result["passed"], name
        if "sources" in result:
            assert_source_hashes(result["sources"])
    for top in ("tb_drum_bank_v7", "tb_drum_audio_v7", "tb_drum_sd_v7", "tb_sd_boot",
                "tb_ensemble_board", "tb_ensemble_hall_piano"):
        binding = json.loads((ROOT / f"tests/results/{top}_source_sha256.json").read_text(encoding="utf-8"))
        assert_source_hashes(binding)
    for name, marker in (("ensemble_board.log", "PASS ENSEMBLE BOARD"),
                         ("ensemble_hall_piano.log", "PASS ENSEMBLE HALL PIANO:"),
                         ("drums_gate_log.txt", "PASS post-synthesis drums")):
        log = (ROOT / "tests/results" / name).read_text(encoding="utf-8")
        assert marker in log and not any(error in log for error in ("ERROR", "FATAL", "Unable to open")), name
    gate = json.loads((ROOT / "tests/results/drums_gate_hashes.json").read_text(encoding="utf-8"))
    for name, value in gate.items():
        if name != "gate_netlist_sha256":
            assert digest(ROOT / name) == value, name
    assert digest(ROOT / "tests/runtime_temp/drum_gate_project/impl/gwsynthesis/drum_gate.vg") == gate["gate_netlist_sha256"]
    sd = json.loads((ROOT / "tests/results/sd_boot_summary.json").read_text(encoding="utf-8"))
    assert sd["cases"] == 8 and all("PASS SD BOOT" in log for log in sd["results"])
    return {"drum_PCM_frames": 26655, "default_gate_frames": 2688, "SD_cases": 7, "piano_SD_cases": 8,
            "loaded_RAM_gate_comparison": True, "whole_board_and_Hall_DAC": True,
            "hardware_listening": False}


def save(state):
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assert not STATE.exists(), "Preserve previous attempt"
    frozen = inputs()
    state = {"started": now(), "phase": "waiting_for_regressions", "scope": verify_scope(),
             "FPGA_written": False, "S3_written": False}
    save(state)
    print("V7 pipeline: waiting for actual regression passes; then new full 2/1 build", flush=True)
    try:
        deadline = time.monotonic() + 7200
        required = {"ensemble_board.log": "PASS ENSEMBLE BOARD", "ensemble_hall_piano.log": "PASS ENSEMBLE HALL PIANO:",
                    "drum_sd_gate_v7.log": "PASS DRUM SD GATE V7:"}
        while True:
            assert frozen == inputs(), "Production inputs changed while awaiting regressions"
            ready = True
            for name, marker in required.items():
                path = ROOT / "tests/results" / name
                log = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
                assert not any(error in log for error in ("ERROR", "FATAL", "Unable to open")), name
                ready = ready and marker in log
            ready = ready and (ROOT / "tests/results/drum_sd_gate_v7_result.json").exists()
            if ready:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("Functional regressions did not complete in two hours")
            time.sleep(5)
        verified = verify_tests()
        state.update(phase="full_build_running", functional_finished=now(), tests=verified)
        save(state)
        proof = {"started": now(), "passed": False, "physical_build_only": True,
                 "sources": frozen, "scope": state["scope"], "functional_tests": verified,
                 "place_option": 2, "route_option": 1, "incremental_placement": False,
                 "timeout_seconds": 21600, "FPGA_written": False, "S3_written": False}
        proof_path = OUTPUT / "proof.json"
        proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
        environment = os.environ.copy()
        environment["V7_PYTHON"] = sys.executable
        with (OUTPUT / "console.log").open("w", encoding="utf-8") as stream:
            try:
                process = subprocess.run([str(GOWIN), "build_merged.tcl"], cwd=ROOT, env=environment,
                                         stdout=stream, stderr=subprocess.STDOUT, timeout=21600)
                proof["returncode"] = process.returncode
            except subprocess.TimeoutExpired:
                proof.update(returncode=None, failure_kind="timeout_not_a_timing_verdict")
        log = (OUTPUT / "console.log").read_text(encoding="utf-8", errors="replace")
        proof.update(finished=now(), sources_unchanged=frozen == inputs())
        proof["passed"] = proof["returncode"] == 0 and proof["sources_unchanged"] and all(
            marker in log for marker in ("PASS V7 routing structure:", "R10 Pro DDR PASS:",
                                         "PASS minimum pulse width", "Merged build timing PASS"))
        bitstream = ROOT / "impl/pnr/ensemble_hall_piano_v7.fs"
        if bitstream.exists():
            proof.update(bitstream_sha256=digest(bitstream), bitstream_size=bitstream.stat().st_size)
        proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
        state.update(phase="physical_build_passed" if proof["passed"] else "physical_build_failed", finished=now())
        save(state)
        print(log[-5000:], flush=True)
        if not proof["passed"]:
            raise RuntimeError("Physical build was not accepted; inspect actual proof/log")
    except BaseException as error:
        state.update(phase="stopped_with_error", finished=now(), error=f"{type(error).__name__}: {error}")
        save(state)
        raise


if __name__ == "__main__":
    main()
