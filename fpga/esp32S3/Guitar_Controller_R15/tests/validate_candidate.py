import hashlib
import json
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
BASELINE = PROJECT / "checkpoints/pre_i2c_v3_20261019_163241"
WORKSPACE = PROJECT.parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    changed = {"cy8cmbr3116.c", "cy8cmbr3116.h", "touch_serial.c", "touch_filter.h", "CMakeLists.txt"}
    baseline = json.loads((BASELINE / "source_baseline.json").read_text(encoding="utf-8-sig"))
    protected = []
    for entry in baseline:
        path = Path(entry["path"])
        if path.parent == PROJECT / "main" and path.name in changed:
            continue
        assert digest(path) == entry["sha256"], f"Unrelated source changed: {path}"
        protected.append(str(path))
    saved = json.loads((BASELINE / "manifest.json").read_text(encoding="utf-8-sig"))
    for entry in saved:
        assert digest(BASELINE / entry["path"]) == entry["sha256"], entry["path"]
    for name in ("sdkconfig", "sdkconfig.defaults", "CMakeLists.txt", "build_r15.ps1", "build_r15.cmd"):
        assert digest(PROJECT / name) == digest(BASELINE / name), name
    source_manifest = WORKSPACE / "esp32S3/CY8_Performance_Config/profiles/source_hashes.json"
    originals = json.loads(source_manifest.read_text(encoding="utf-8"))
    for entry in originals:
        assert digest(Path(entry["source"])) == entry["sha256"], entry["source"]
    commands = json.loads((PROJECT / "build_r15/compile_commands.json").read_text(encoding="utf-8"))
    for name in ("cy8cmbr3116.c", "touch_serial.c", "touch_output.c"):
        selected = [entry for entry in commands if Path(entry["file"]).name == name]
        assert len(selected) == 1 and Path(selected[0]["file"]).resolve() == PROJECT / "main" / name, name
    binary_path = PROJECT / "build_r15/Guitar_Controller_S3_R15.bin"
    binary = binary_path.read_bytes()
    for marker in (b"R15-I2C-RESPONSIVE-v3", b"STALE_RELEASE", b"BUS_RECOVERY", b"QUEUE_OVERFLOW"):
        assert marker in binary, marker
    for source in (PROJECT / "main").glob("*.[ch]"):
        assert source.stat().st_mtime <= binary_path.stat().st_mtime, source
    for name in ("cy8cmbr3116.c", "touch_serial.c"):
        assert "uart_write_bytes" not in (PROJECT / "main" / name).read_text(encoding="utf-8"), name
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                             str(PROJECT / "tests"), "-p", "test_*.py", "-v"],
                            capture_output=True, text=True)
    output = result.stdout + result.stderr
    (PROJECT / "tests/runtime_validation.log").write_text(output, encoding="utf-8")
    assert result.returncode == 0 and "Ran 15 tests" in output, output
    build_log = (PROJECT / "build_r15_i2c_responsive_v3_console.log").read_text(
        encoding="utf-8-sig", errors="replace")
    assert "Project build complete" in build_log
    report = {
        "version": "R15-I2C-RESPONSIVE-v3",
        "status": "build_and_15_native_C_polling_simulations_passed_hardware_unverified",
        "application_size": len(binary),
        "application_sha256": digest(binary_path),
        "previous_application_sha256": digest(BASELINE / "build_r15/Guitar_Controller_S3_R15.bin"),
        "verified_backup_files": len(saved),
        "protected_sources": protected,
        "unchanged_D_drive_originals": len(originals),
        "active_mask": "0xFB",
        "i2c_attempts_per_register": 1,
        "stale_key_release_us": 60000,
        "probe_backoff_max_us": 200000,
        "master_bus_recovery_min_interval_us": 500000,
        "native_C_polling_simulations_passed": 15,
        "simulation_limits": ["mock I2C and clock", "mock UART and log enqueue", "no real RTOS scheduling or electrical validation"],
        "hardware_verified": False,
        "flashed_by_agent": False,
        "CY8_configuration_written": False,
    }
    (PROJECT / "tests/validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
