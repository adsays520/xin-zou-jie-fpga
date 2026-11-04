import json
import time

import build_routing_v6 as build

ROOT = build.ROOT
OUTPUT = ROOT / "tests/results/routing_v6_ready_build"
STATE = OUTPUT / "pipeline_state.json"


def save(state):
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assert not STATE.exists(), "Preserve prior continuation evidence"
    first = json.loads((ROOT / "tests/results/routing_v6_build/proof.json").read_text(encoding="utf-8"))
    first_log = (ROOT / "tests/results/routing_v6_build/console.log").read_text(encoding="utf-8")
    assert first["returncode"] == 1 and first["sources_unchanged"]
    assert "PASS V6 routing structure:" in first_log and "FileNotFoundError" in first_log
    assert "tb_ensemble_hall_piano_source_sha256.json" in first_log
    assert first["sources"] == build.inputs()
    original_inputs = build.inputs

    def current_inputs():
        result = original_inputs()
        result["scripts/continue_routing_v6.py"] = build.digest(ROOT / "scripts/continue_routing_v6.py")
        return result

    frozen = current_inputs()
    state = {"started": build.now(), "phase": "waiting_for_functional_regressions",
             "first_attempt": "synthesis_passed_then_integration_gate_missing_unfinished_Hall_test",
             "first_proof_sha256": build.digest(ROOT / "tests/results/routing_v6_build/proof.json"),
             "sources": frozen, "FPGA_written": False, "S3_written": False}
    save(state)
    print("V6 pipeline waits for current whole-board/Hall regressions, then runs a fresh 2/1 build.", flush=True)
    try:
        deadline = time.monotonic() + 7200
        targets = {"ensemble_board.log": "PASS ENSEMBLE BOARD",
                   "ensemble_hall_piano.log": "PASS ENSEMBLE HALL PIANO:"}
        while True:
            assert frozen == current_inputs(), "Inputs changed while awaiting regressions"
            complete = True
            for name, marker in targets.items():
                path = ROOT / "tests/results" / name
                log = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
                assert "FATAL" not in log and "ERROR" not in log and "Unable to open" not in log, name
                complete = complete and marker in log
            if complete:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("Functional prerequisites did not finish within two hours")
            time.sleep(5)
        verified = build.verify_tests()
        state.update(phase="full_build_running", tests=verified, functional_finished=build.now())
        save(state)
        build.OUTPUT = OUTPUT
        build.inputs = current_inputs
        build.main()
        state.update(phase="physical_build_passed", finished=build.now())
        save(state)
    except BaseException as error:
        state.update(phase="stopped_with_error", finished=build.now(),
                     error=f"{type(error).__name__}: {error}")
        save(state)
        raise


if __name__ == "__main__":
    main()
