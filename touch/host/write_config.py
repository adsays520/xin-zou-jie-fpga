import argparse
import hashlib
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

from generate_profiles import ACTIVE_MASK, config_crc, validate_config


class ProgrammingError(RuntimeError):
    pass


class TransferError(ProgrammingError):
    def __init__(self, code, before, after, elapsed_us):
        self.code = code
        self.before = before
        self.after = after
        self.elapsed_us = elapsed_us
        super().__init__(f"I2C error 0x{code:X}, pre={before:02b}, post={after:02b}, us={elapsed_us}")


class SerialBridge:
    def __init__(self, port):
        try:
            import serial
        except ImportError as error:
            raise ProgrammingError("Use the ESP-IDF Python environment; pyserial is required") from error
        self.serial = serial.Serial(port=None, baudrate=115200, timeout=0.1, write_timeout=1)
        self.serial.dtr = False
        self.serial.rts = False
        self.serial.port = port
        self.serial.open()
        self.sequence = 0

    def request(self, command, *arguments):
        self.sequence += 1
        sequence = str(self.sequence)
        message = ",".join((command, sequence, *arguments)) + "\n"
        if self.serial.write(message.encode("ascii")) != len(message):
            raise ProgrammingError("Incomplete USB command; not retrying an uncertain write")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            response = self.serial.readline().decode("ascii", errors="replace").strip()
            fields = response.split(",")
            if len(fields) < 3 or fields[1] != sequence:
                continue
            if fields[0] in ("OK", "PONG") and len(fields) == 3:
                return fields[2]
            if fields[0] == "ERR" and len(fields) == 6:
                raise TransferError(int(fields[2], 16), int(fields[3]), int(fields[4]), int(fields[5]))
        raise ProgrammingError("USB response timeout; command completion is uncertain")

    def hello(self):
        if self.request("PING") != "CY8CFG1":
            raise ProgrammingError("Not the CY8CFG1 configuration bridge")

    def read(self, address, reg, length):
        result = self.request("R", f"{address:02X}", f"{reg:02X}", str(length))
        try:
            data = bytes.fromhex(result)
        except ValueError as error:
            raise ProgrammingError("Invalid USB read payload") from error
        if len(data) != length:
            raise ProgrammingError("USB read length mismatch")
        return data

    def write(self, address, reg, data):
        if self.request("W", f"{address:02X}", f"{reg:02X}", data.hex().upper()) != "WRITTEN":
            raise ProgrammingError("Unexpected USB write acknowledgement")

    def arm(self):
        if self.request("ARM", "CY8CFG1") != "ARMED":
            raise ProgrammingError("Bridge did not unlock")

    def lock(self):
        if self.request("LOCK") != "LOCKED":
            raise ProgrammingError("Bridge did not lock")

    def close(self):
        self.serial.close()


class FileJournal:
    def __init__(self, directory, address):
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = directory / f"{stamp}_{address:02X}_{uuid.uuid4().hex[:8]}.json"
        self.document = {"address": address, "events": [], "status": "not_started"}

    def record(self, stage, **values):
        self.document.update(values)
        self.document["status"] = stage
        self.document["events"].append({"stage": stage, "time": datetime.now().isoformat()})
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(self.document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)


def snapshot(data):
    return {"data": data.hex(), "sha256": hashlib.sha256(data).hexdigest(),
            "crc_valid_for_readback": config_crc(data) == int.from_bytes(data[126:128], "little")}


def configuration_matches(actual, expected):
    if actual == expected:
        return True
    requested = int.from_bytes(expected[:2], "little")
    enabled = int.from_bytes(actual[:2], "little")
    return (actual[2:] == expected[2:] and bool(expected[0x4E] & 1) and
            enabled & ~requested == 0)


def load_profiles(path):
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != 1 or document.get("active_mask") != ACTIVE_MASK:
        raise ProgrammingError("Unsupported profile schema or active mask")
    images = document.get("images", [])
    if len(images) != 8:
        raise ProgrammingError("Eight distinct address profiles are required")
    result = {}
    for entry in images:
        chip = entry["chip"]
        if chip in result or chip not in range(8) or entry["address"] != 0x37 + chip:
            raise ProgrammingError("Duplicate or mismatched address profile")
        if entry["enabled"] != bool(ACTIVE_MASK & (1 << chip)):
            raise ProgrammingError("Profile enabled mask mismatch")
        data = bytes.fromhex(entry["data"])
        validate_config(data, entry["address"])
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ProgrammingError("Profile SHA256 mismatch")
        result[chip] = data
    return result


class Programmer:
    def __init__(self, bridge, delay=time.sleep, log=print):
        self.bridge = bridge
        self.delay = delay
        self.log = log

    def bounded(self, operation):
        for attempt in range(3):
            try:
                return operation()
            except TransferError as error:
                if (attempt == 2 or error.code != 0x108 or error.before != 3 or
                        error.after != 3 or error.elapsed_us > 2000):
                    raise
                self.delay(0.01)

    def read(self, address, reg, length):
        return self.bounded(lambda: self.bridge.read(address, reg, length))

    def identity(self, address):
        for unused in range(2):
            device_id = int.from_bytes(self.read(address, 0x90, 2), "little")
            if device_id != 0x0A05:
                raise ProgrammingError(f"0x{address:02X}: wrong DEVICE_ID 0x{device_id:04X}")
            self.delay(0.01)

    def image(self, address):
        return b"".join(self.read(address, offset, 16) for offset in range(0, 128, 16))

    def stable_image(self, address):
        first = self.image(address)
        for attempt in range(5):
            if first[0x51] != address:
                raise ProgrammingError(f"0x{address:02X}: readback address 0x{first[0x51]:02X}; verification stopped")
            self.delay(0.01)
            second = self.image(address)
            if second[0x51] != address:
                raise ProgrammingError(f"0x{address:02X}: readback address 0x{second[0x51]:02X}; verification stopped")
            if first == second:
                return second
            changes = ",".join(f"{offset:02X}:{first[offset]:02X}>{second[offset]:02X}"
                               for offset in range(128) if first[offset] != second[offset])
            self.log(f"  READBACK_RETRY 0x{address:02X} pair={attempt + 1}/5"
                     f" CRC_valid={snapshot(first)['crc_valid_for_readback']}/"
                     f"{snapshot(second)['crc_valid_for_readback']} differences={changes}")
            first = second
        raise ProgrammingError(f"0x{address:02X}: no two consecutive matching snapshots in six reads; verification stopped")

    def idle(self, address):
        for unused in range(24):
            try:
                if self.read(address, 0x86, 1) == b"\x00":
                    return
            except TransferError as error:
                if error.code != 0x108 or error.before != 3 or error.after != 3:
                    raise
            self.delay(0.05)
        raise ProgrammingError("CTRL_CMD did not become idle; not issuing another command")

    def reset(self, address):
        self.idle(address)
        self.bridge.write(address, 0x86, b"\xFF")
        self.delay(1.5)
        self.identity(address)

    def checked_match(self, address, actual, expected):
        if not configuration_matches(actual, expected):
            return False
        if actual[:2] != expected[:2]:
            disabled = int.from_bytes(expected[:2], "little") & ~int.from_bytes(actual[:2], "little")
            diagnostics = self.read(address, 0x97, 10)
            faults = 0
            for offset in (1, 3, 5, 7):
                faults |= int.from_bytes(diagnostics[offset:offset + 2], "little")
            if not diagnostics[0] & 0x80 or disabled & ~faults:
                raise ProgrammingError("Reduced SENSOR_EN is not explained by startup diagnostics")
            self.log(f"  WARNING: SENSOR_EN={int.from_bytes(actual[:2], 'little'):04X},"
                     f" startup sensor faults={faults:04X}; configuration match is not a sensor repair")
        return True

    def inspect(self, address):
        self.identity(address)
        data = self.stable_image(address)
        return {"address": address, "configuration": snapshot(data),
                "sensor_enable": int.from_bytes(data[:2], "little"),
                "button_auto_reset": (data[0x4F] >> 4) & 3,
                "look_for_touch_ms": (data[0x52] & 63) * 20}

    def program(self, address, expected, journal):
        if address not in range(0x37, 0x3F):
            raise ProgrammingError("Address is not an enabled chip")
        validate_config(expected, address)
        self.identity(address)
        before = self.stable_image(address)
        journal.record("backed_up_before_reset", before=snapshot(before), target=snapshot(expected))
        try:
            self.bridge.arm()
            self.reset(address)
            persisted = self.stable_image(address)
            journal.record("backed_up_after_reset", after_reset=snapshot(persisted))
            if self.checked_match(address, persisted, expected):
                journal.record("already_configured_no_flash_write", result=snapshot(persisted))
                self.log(f"0x{address:02X}: already configured; no SAVE issued")
                return
            self.idle(address)
            for offset in range(0, 128, 16):
                block = expected[offset:offset + 16]
                self.bounded(lambda: self.bridge.write(address, offset, block))
            if self.stable_image(address) != expected:
                raise ProgrammingError("RAM readback differs; SAVE not issued; power cycle before retry")
            journal.record("ram_verified")
            self.idle(address)
            journal.record("save_about_to_be_sent")
            try:
                self.bridge.write(address, 0x86, b"\x02")
            except ProgrammingError as error:
                journal.record("save_ack_uncertain", save_error=str(error))
            self.delay(0.3)
            self.idle(address)
            status = self.read(address, 0x88, 2)
            previous = self.read(address, 0x8C, 1)
            if status != b"\x00\x00" or previous != b"\x02":
                raise ProgrammingError(f"SAVE not verified: status/error={status.hex()}, previous={previous.hex()}")
            journal.record("save_status_verified")
            self.reset(address)
            result = self.stable_image(address)
            if not self.checked_match(address, result, expected):
                raise ProgrammingError("Post-reset configuration mismatch; persistent SAVE not confirmed")
            if self.read(address, 0x8A, 1)[0] & 1:
                raise ProgrammingError("Device reports factory-default fallback after reset")
            journal.record("saved_reset_verified", result=snapshot(result))
            self.log(f"0x{address:02X}: SAVE/reset/readback verified; CRC=0x{config_crc(expected):04X}")
            if result[:2] != expected[:2]:
                self.log(f"  WARNING: runtime SENSOR_EN={int.from_bytes(result[:2], 'little'):04X}; inspect startup diagnostics")
        except Exception as error:
            journal.record("failed_or_uncertain", error=str(error))
            raise
        finally:
            try:
                self.bridge.lock()
            except ProgrammingError:
                self.log("WARNING: LOCK unconfirmed; stop and power cycle; no automatic command retries")


def main():
    parser = argparse.ArgumentParser(description="CY8 performance configuration; default is read-only inspection")
    parser.add_argument("--port", required=True)
    parser.add_argument("--profiles", type=Path,
                        default=Path(__file__).resolve().parents[1] / "profiles/profiles.json")
    parser.add_argument("--backup-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "device_backups")
    parser.add_argument("--chip", type=int, choices=tuple(range(8)))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    images = load_profiles(args.profiles)
    chips = [args.chip] if args.chip is not None else [chip for chip in range(8) if ACTIVE_MASK & (1 << chip)]
    bridge = SerialBridge(args.port)
    try:
        bridge.hello()
        programmer = Programmer(bridge)
        for chip in chips:
            address = 0x37 + chip
            print(f"chip{chip} 0x{address:02X}: {'WRITE' if args.write else 'READ ONLY'}", flush=True)
            if args.write:
                journal = FileJournal(args.backup_dir, address)
                print(f"Backup/journal: {journal.path}", flush=True)
                programmer.program(address, images[chip], journal)
            else:
                print(json.dumps(programmer.inspect(address), ensure_ascii=False, indent=2))
        print("Complete. all eight addresses enabled.")
    finally:
        bridge.close()


if __name__ == "__main__":
    try:
        main()
    except (ProgrammingError, ValueError, OSError) as error:
        raise SystemExit(f"STOP: {error}") from error
