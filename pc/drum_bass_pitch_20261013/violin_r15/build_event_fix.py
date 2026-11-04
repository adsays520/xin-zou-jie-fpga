import hashlib
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

from build import GOWIN, PROJECT, source_hashes


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--hall', action='store_true')
    mode.add_argument('--hall-link', action='store_true')
    mode.add_argument('--hall-timing', action='store_true')
    arguments = parser.parse_args()
    output_base = 'guitar_audio_hall_timing_v3' if arguments.hall_timing else 'guitar_audio_hall_link_v2' if arguments.hall_link else 'guitar_audio_hall_v1' if arguments.hall else 'guitar_audio_events_v1'
    output = PROJECT / ('tests/results/hall_timing_v3_build' if arguments.hall_timing else 'tests/results/hall_link_v2_build' if arguments.hall_link else 'tests/results/hall_v1_build' if arguments.hall else 'tests/results/event_fix_build')
    output.mkdir(parents=True, exist_ok=True)
    sources = source_hashes()
    script = PROJECT / ('build_hall_timing_v3.tcl' if arguments.hall_timing else 'build_hall_link_v2.tcl' if arguments.hall_link else 'build_hall_v1.tcl' if arguments.hall else 'build_event_fix_v1.tcl')
    sources[script.name] = hashlib.sha256(script.read_bytes()).hexdigest()
    proof = {"started": datetime.now().astimezone().isoformat(), "sources": sources,
             "passed": False, "FPGA_written": False, "output_base": output_base}
    (output / "proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    with (output / "console.log").open("w", encoding="utf-8") as log:
        result = subprocess.run([str(GOWIN), str(script)], cwd=PROJECT,
                                stdout=log, stderr=subprocess.STDOUT, timeout=5400)
    console = (output / "console.log").read_text(encoding="utf-8", errors="replace")
    current = source_hashes()
    current[script.name] = hashlib.sha256(script.read_bytes()).hexdigest()
    passed = result.returncode == 0 and sources == current and "R10 Pro DDR PASS:" in console
    passed = passed and "pulse" in console.lower() and "GowinSynthesis finish" in console
    proof.update(finished=datetime.now().astimezone().isoformat(), returncode=result.returncode,
                 sources_unchanged=sources == current, passed=passed)
    bitstream = PROJECT / f"impl/pnr/{output_base}.fs"
    if passed:
        proof["bitstream_sha256"] = hashlib.sha256(bitstream.read_bytes()).hexdigest()
        proof["bitstream_size"] = bitstream.stat().st_size
    (output / "proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(console[-5000:], flush=True)
    if not passed:
        raise RuntimeError(f"Candidate timing/build did not pass; inspect {output}")


if __name__ == "__main__":
    main()
