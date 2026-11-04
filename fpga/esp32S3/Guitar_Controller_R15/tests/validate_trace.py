import hashlib
import json
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
BASELINE = PROJECT / "checkpoints/i2c_responsive_v3_20261019_165054"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def erase_block(text, token):
    start = text.index(token)
    opening = text.index("{", start)
    depth = 1
    cursor = opening + 1
    while depth:
        if text[cursor] == "{":
            depth += 1
        elif text[cursor] == "}":
            depth -= 1
        cursor += 1
    if text[cursor:cursor + 1] == "\n":
        cursor += 1
    return text[:start] + text[cursor:]


def main():
    original = BASELINE / "source/main"
    current = PROJECT / "main"
    for saved in original.iterdir():
        if saved.name not in {"touch_serial.c", "cy8cmbr3116.c", "fpga_link.c"}:
            assert digest(saved) == digest(current / saved.name), saved.name
    driver = (current / "cy8cmbr3116.c").read_text(encoding="utf-8")
    assert driver.replace("R15-I2C-TRACE-v3.1", "R15-I2C-RESPONSIVE-v3") == (
        original / "cy8cmbr3116.c").read_text(encoding="utf-8")
    polling = (current / "touch_serial.c").read_text(encoding="utf-8")
    for line in ("    uint16_t last_raw;\n", "    uint32_t samples;\n", "    bool raw_seen;\n"):
        polling = polling.replace(line, "")
    start = polling.index("    bool raw_changed =")
    end = polling.index("    state->sensor_enable = sensor_enable;", start)
    polling = polling[:start] + polling[end:]
    polling = erase_block(polling, "    if (raw_changed) {")
    polling = erase_block(polling, "    if (changed != 0) {")
    polling = polling.replace("fast_poll=1 released=0x%04X;", "fast_poll=1;")
    polling = polling.replace("chip, cy8cmbr3116_address(chip), released);", "chip, cy8cmbr3116_address(chip));")
    assert polling == (original / "touch_serial.c").read_text(encoding="utf-8"), "Polling logic changed beyond tracing"
    link = (current / "fpga_link.c").read_text(encoding="utf-8")
    for line in ("#include \"touch_output.h\"\n", "    bool pending_trace = false;\n",
                 "    bool trace_initialized = false;\n", "    uint8_t traced_keys[16] = {0};\n",
                 "    uint8_t traced_online = 0;\n"):
        link = link.replace(line, "")
    link = erase_block(link, "            if (!trace_initialized ||")
    link = erase_block(link, "            if (pending_trace) {")
    assert link == (original / "fpga_link.c").read_text(encoding="utf-8"), "SPI logic changed beyond tracing"
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                             str(PROJECT / "tests"), "-p", "test_*.py", "-v"],
                            capture_output=True, text=True)
    output = result.stdout + result.stderr
    (PROJECT / "tests/trace_runtime_validation.log").write_text(output, encoding="utf-8")
    assert result.returncode == 0 and "Ran 17 tests" in output, output
    binary_path = PROJECT / "build_r15/Guitar_Controller_S3_R15.bin"
    binary = binary_path.read_bytes()
    for marker in (b"R15-I2C-TRACE-v3.1", b"TOUCH_TRACE", b"FPGA_TRACE", b"RAW chip=", b"EDGE chip="):
        assert marker in binary, marker
    for source in current.glob("*.[ch]"):
        assert source.stat().st_mtime <= binary_path.stat().st_mtime, source
    assert "Project build complete" in (PROJECT / "build_r15_trace_v3_1_console.log").read_text(
        encoding="utf-8-sig", errors="replace")
    manifest = PROJECT.parent / "CY8_Performance_Config/profiles/source_hashes.json"
    for entry in json.loads(manifest.read_text(encoding="utf-8")):
        assert digest(Path(entry["source"])) == entry["sha256"]
    report = {"version": "R15-I2C-TRACE-v3.1", "application_size": len(binary),
              "application_sha256": digest(binary_path), "native_C_tests_passed": 17,
              "polling_filter_recovery_and_SPI_logic_match_v3_after_removing_trace_only": True,
              "CY8_IO_logic_unchanged_except_version_marker": True,
              "D_drive_original_files_unchanged": 32, "flashed_by_agent": False,
              "purpose": "Trace spontaneous notes without changing recognition or register configuration"}
    (PROJECT / "tests/trace_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
