import hashlib
import json
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
BASELINE = PROJECT / "checkpoints/notes_v3_2_20261019_205732/source/main"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    current = PROJECT / "main"
    for saved in BASELINE.iterdir():
        if saved.is_file() and saved.name not in {"touch_serial.c", "cy8cmbr3116.c"}:
            assert digest(saved) == digest(current / saved.name), saved.name
    driver = (current / "cy8cmbr3116.c").read_text(encoding="utf-8")
    assert driver.replace("R15-I2C-GUARD-v3.3", "R15-I2C-NOTES-v3.2") == (
        BASELINE / "cy8cmbr3116.c").read_text(encoding="utf-8")
    polling = (current / "touch_serial.c").read_text(encoding="utf-8")
    polling = polling.replace("    uint32_t read_disagreements;\n", "")
    polling = polling.replace("    int64_t next_disagreement_log_us;\n", "")
    start = polling.index("static esp_err_t read_guarded_buttons(")
    end = polling.index("static esp_err_t poll_chip(", start)
    polling = polling[:start] + polling[end:]
    polling = polling.replace("    bool verified;\n", "").replace("    bool verified = true;\n", "")
    polling = polling.replace("read_guarded_buttons(chip, &current_state, &verified)",
                              "cy8cmbr3116_read_buttons(chip, &current_state)")
    polling = polling.replace("if (verified) accept_buttons(chip, current_state, s_chips[chip].sensor_enable);",
                              "accept_buttons(chip, current_state, s_chips[chip].sensor_enable);")
    polling = polling.replace("if (verified) accept_buttons(chip, current_state, state->sensor_enable);\n"
                              "            else state->probe.next_us = esp_timer_get_time() + CY8_PROBE_SLOT_US;",
                              "accept_buttons(chip, current_state, state->sensor_enable);")
    assert polling == (BASELINE / "touch_serial.c").read_text(encoding="utf-8"), "Unexpected polling changes"
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                             str(PROJECT / "tests"), "-p", "test_*.py", "-v"],
                            capture_output=True, text=True, encoding="utf-8")
    output = result.stdout + result.stderr
    (PROJECT / "tests/guard_runtime_validation.log").write_text(output, encoding="utf-8")
    assert result.returncode == 0 and "Ran 41 tests" in output, output
    binary_path = PROJECT / "build_r15/Guitar_Controller_S3_R15.bin"
    binary = binary_path.read_bytes()
    for marker in (b"R15-I2C-GUARD-v3.3", b"READ_DISAGREE", b"NOTE_KEY", b"NOTE_ACK"):
        assert marker in binary, marker
    for source in current.iterdir():
        if source.is_file():
            assert source.stat().st_mtime <= binary_path.stat().st_mtime, source
    assert "Project build complete" in (PROJECT / "build_r15_guard_v3_3_console.log").read_text(
        encoding="utf-8-sig", errors="replace")
    manifest = PROJECT.parent / "CY8_Performance_Config/profiles/source_hashes.json"
    for entry in json.loads(manifest.read_text(encoding="utf-8")):
        assert digest(Path(entry["source"])) == entry["sha256"]
    report = {"version": "R15-I2C-GUARD-v3.3", "application_size": len(binary),
              "application_sha256": digest(binary_path), "tests_passed": 41,
              "SPI_layout_filter_and_recovery_headers_unchanged": True,
              "only_added_change_pair_verification_and_version_marker": True,
              "D_original_HEX_unchanged": 32, "flashed": False,
              "cannot_authenticate_persistent_repeated_bad_button_words": True}
    (PROJECT / "tests/guard_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
