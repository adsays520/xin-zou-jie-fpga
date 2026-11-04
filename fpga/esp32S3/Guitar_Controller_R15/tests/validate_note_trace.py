import hashlib
import json
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
BASELINE = PROJECT / "checkpoints/trace_v3_1_20261019_203802/source/main"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    current = PROJECT / "main"
    allowed = {"touch_serial.c", "fpga_link.c", "cy8cmbr3116.c", "CMakeLists.txt"}
    for saved in BASELINE.iterdir():
        if saved.name not in allowed:
            assert digest(saved) == digest(current / saved.name), saved.name
    polling = (current / "touch_serial.c").read_text(encoding="utf-8")
    polling = polling.replace('#include "note_trace.h"\n', "")
    polling = polling.replace(', const char *reason)', ')')
    polling = polling.replace('        if (key != 0) {\n'
                              '            host_send_key(key, (buttons & mask) != 0);\n'
                              '            note_trace_key(key, (buttons & mask) != 0, reason);\n'
                              '        }',
                              '        if (key != 0) host_send_key(key, (buttons & mask) != 0);')
    for reason in ("OFFLINE", "STALE", "FILTER"):
        polling = polling.replace(f', "{reason}");', ');')
    assert polling == (BASELINE / "touch_serial.c").read_text(encoding="utf-8"), "Polling changed beyond logging"
    link = (current / "fpga_link.c").read_text(encoding="utf-8")
    for addition in ('#include "note_trace.h"\n', '    note_trace_state_t note_trace = {0};\n',
                     '            note_trace_ack(&note_trace, sequence, rx + 16, rx[7], rx[38] != 0, tx[30] != 0);\n'):
        link = link.replace(addition, "")
    assert link == (BASELINE / "fpga_link.c").read_text(encoding="utf-8"), "SPI changed beyond logging"
    driver = (current / "cy8cmbr3116.c").read_text(encoding="utf-8")
    assert driver.replace("R15-I2C-NOTES-v3.2", "R15-I2C-TRACE-v3.1") == (
        BASELINE / "cy8cmbr3116.c").read_text(encoding="utf-8")
    cmake = (current / "CMakeLists.txt").read_text(encoding="utf-8").replace(' "note_trace.c"', '')
    assert cmake == (BASELINE / "CMakeLists.txt").read_text(encoding="utf-8")
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                             str(PROJECT / "tests"), "-p", "test_*.py", "-v"],
                            capture_output=True, text=True, encoding="utf-8")
    output = result.stdout + result.stderr
    (PROJECT / "tests/note_trace_runtime_validation.log").write_text(output, encoding="utf-8")
    assert result.returncode == 0 and "Ran 30 tests" in output, output
    binary_path = PROJECT / "build_r15/Guitar_Controller_S3_R15.bin"
    binary = binary_path.read_bytes()
    for marker in (b"R15-I2C-NOTES-v3.2", b"NOTE_KEY", b"NOTE_ACK", b"NOTE_MODE", b"TOUCH_TRACE", b"FPGA_TRACE"):
        assert marker in binary, marker
    for source in current.iterdir():
        if source.is_file():
            assert source.stat().st_mtime <= binary_path.stat().st_mtime, source
    assert "Project build complete" in (PROJECT / "build_r15_notes_v3_2_console.log").read_text(
        encoding="utf-8-sig", errors="replace")
    manifest = PROJECT.parent / "CY8_Performance_Config/profiles/source_hashes.json"
    for entry in json.loads(manifest.read_text(encoding="utf-8")):
        assert digest(Path(entry["source"])) == entry["sha256"]
    report = {"version": "R15-I2C-NOTES-v3.2", "application_size": len(binary),
              "application_sha256": digest(binary_path), "tests_passed": 30,
              "polling_filter_recovery_and_SPI_match_v3_1_after_removing_logs": True,
              "D_original_HEX_unchanged": 32, "flashed_by_validation": False,
              "note_ack_is_received_key_mapping_not_audio_engine_event": True}
    (PROJECT / "tests/note_trace_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
