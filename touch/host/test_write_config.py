import copy
import json
import tempfile
import unittest
from pathlib import Path

from generate_profiles import encode_hex, parse_hex, performance_config, validate_config
from write_config import FileJournal, Programmer, ProgrammingError, TransferError, configuration_matches, load_profiles


ROOT = Path(__file__).resolve().parents[1]


class MemoryBridge:
    def __init__(self, data):
        self.ram = bytearray(data)
        self.nonvolatile = bytes(data)
        self.commands = []
        self.writes = []
        self.armed = False
        self.previous = 0
        self.status = b"\x00\x00"
        self.bad_id = False
        self.fail_offset = None
        self.corrupt_staged = False
        self.save_error = False
        self.lose_save_ack = False
        self.drop_save = False
        self.fail_reset_number = None
        self.reset_count = 0
        self.runtime_disable = 0
        self.factory_default = False
        self.keep_busy = False
        self.missing_diagnostics = False

    def arm(self):
        self.armed = True

    def lock(self):
        self.armed = False

    def read(self, address, reg, length):
        if reg == 0x90:
            return b"\xFF\xFF" if self.bad_id else b"\x05\x0A"
        if reg == 0x86:
            return b"\x02" if self.keep_busy else b"\x00"
        if reg == 0x88:
            return self.status
        if reg == 0x8C:
            return bytes((self.previous,))
        if reg == 0x8A:
            return bytes((int(self.factory_default),))
        if reg == 0x97:
            if self.missing_diagnostics:
                return bytes(10)
            return bytes((0x80,)) + self.runtime_disable.to_bytes(2, "little") + bytes(7)
        result = bytes(self.ram[reg:reg + length])
        if self.corrupt_staged and self.writes and reg == 0x20:
            return bytes((result[0] ^ 1,)) + result[1:]
        return result

    def write(self, address, reg, data):
        if not self.armed:
            raise ProgrammingError("locked")
        if reg == 0x86:
            command = data[0]
            self.commands.append(command)
            if command == 255:
                self.reset_count += 1
                if self.reset_count == self.fail_reset_number:
                    raise ProgrammingError("reset ACK lost")
                self.ram[:] = self.nonvolatile
                enabled = int.from_bytes(self.ram[:2], "little") & ~self.runtime_disable
                self.ram[:2] = enabled.to_bytes(2, "little")
                self.previous = 0
                self.status = b"\x00\x00"
            elif command == 2:
                self.previous = 2
                if self.save_error:
                    self.status = b"\x01\xFE"
                elif self.drop_save:
                    raise ProgrammingError("SAVE never reached target")
                else:
                    self.nonvolatile = bytes(self.ram)
                if self.lose_save_ack:
                    raise ProgrammingError("SAVE ACK lost")
            return
        if reg == self.fail_offset:
            raise TransferError(0x108, 2, 2, 10000)
        self.writes.append((reg, bytes(data)))
        self.ram[reg:reg + len(data)] = data


class MemoryJournal:
    def __init__(self):
        self.events = []
        self.document = {}

    def record(self, stage, **values):
        self.events.append(stage)
        self.document.update(values)


class FailingJournal(MemoryJournal):
    def record(self, stage, **values):
        raise OSError("backup disk unavailable")


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.original = load_profiles(ROOT / "profiles/original_profiles.json")[0]
        self.target = performance_config(self.original)
        self.bridge = MemoryBridge(self.original)
        self.journal = MemoryJournal()
        self.programmer = Programmer(self.bridge, delay=lambda seconds: None, log=lambda message: None)

    def run_program(self):
        self.programmer.program(0x37, self.target, self.journal)

    def test_all_sources_and_profile_changes(self):
        old = load_profiles(ROOT / "profiles/original_profiles.json")
        new = load_profiles(ROOT / "profiles/profiles.json")
        for chip, target in new.items():
            self.assertEqual(target, performance_config(old[chip]))
            self.assertEqual(target[0x52], 1)
            self.assertEqual(target[0x1C] & 0x0F, 3)
            self.assertEqual(target[0x1F], 0x8A)
            self.assertEqual(target[0x4F] & 0x30, 0)
            self.assertEqual(target[12:28], old[chip][12:28])
            self.assertEqual(target[0x4D:0x4F], old[chip][0x4D:0x4F])
            self.assertEqual(target[0x4F] & ~0x30, old[chip][0x4F] & ~0x30)
            changes = {index for index in range(128) if old[chip][index] != target[index]}
            self.assertLessEqual(changes, {0x1C, 0x1F, 0x4F, 0x52, 0x7E, 0x7F})

    def test_hex_roundtrip_and_checksum_rejection(self):
        metadata = bytes.fromhex("010137370A059A")
        text = encode_hex(self.target, metadata)
        self.assertEqual(parse_hex(text), (self.target, metadata))
        with self.assertRaises(ValueError):
            parse_hex(text.replace(":80", ":81", 1))
        with self.assertRaises(ValueError):
            validate_config(self.target[:-1] + bytes((self.target[-1] ^ 1,)), 0x37)

    def test_success_and_backup_order(self):
        self.run_program()
        self.assertEqual(self.bridge.nonvolatile, self.target)
        self.assertEqual(self.bridge.commands, [255, 2, 255])
        self.assertEqual(len(self.bridge.writes), 8)
        self.assertEqual(self.journal.events[-1], "saved_reset_verified")
        self.assertEqual(self.journal.document["before"]["data"], self.original.hex())
        self.assertFalse(self.bridge.armed)

    def test_transient_corruption_requires_two_consecutive_equal_reads(self):
        corrupted = bytearray(self.original)
        corrupted[0x0A] ^= 1
        samples = iter((self.original, bytes(corrupted), self.original, self.original))
        reads = []

        def read_image(address):
            reads.append(address)
            return next(samples)

        self.programmer.image = read_image
        self.assertEqual(self.programmer.stable_image(0x37), self.original)
        self.assertEqual(reads, [0x37] * 4)
        self.assertEqual(self.bridge.commands, [])

    def test_unstable_readback_is_bounded_and_never_writes(self):
        corrupted = bytearray(self.original)
        corrupted[0x0A] ^= 1
        samples = iter((self.original, bytes(corrupted)) * 3)
        self.programmer.image = lambda address: next(samples)
        with self.assertRaisesRegex(ProgrammingError, "six reads"):
            self.run_program()
        self.assertEqual(self.bridge.commands, [])
        self.assertEqual(self.bridge.writes, [])
        self.assertEqual(self.journal.events, [])

    def test_wrong_readback_address_never_writes(self):
        wrong_address = bytearray(self.original)
        wrong_address[0x51] = 0x38
        self.programmer.image = lambda address: bytes(wrong_address)
        with self.assertRaisesRegex(ProgrammingError, "readback address"):
            self.run_program()
        self.assertEqual(self.bridge.commands, [])
        self.assertEqual(self.bridge.writes, [])

    def test_already_configured_skips_flash_save(self):
        self.bridge.ram[:] = self.target
        self.bridge.nonvolatile = self.target
        self.run_program()
        self.assertNotIn(2, self.bridge.commands)
        self.assertEqual(self.bridge.writes, [])
        self.assertEqual(self.journal.events[-1], "already_configured_no_flash_write")

    def test_wrong_device_id_never_writes(self):
        self.bridge.bad_id = True
        with self.assertRaises(ProgrammingError):
            self.run_program()
        self.assertEqual(self.bridge.commands, [])
        self.assertEqual(self.bridge.writes, [])

    def test_failed_backup_prevents_even_reset(self):
        with self.assertRaises(OSError):
            self.programmer.program(0x37, self.target, FailingJournal())
        self.assertEqual(self.bridge.commands, [])
        self.assertEqual(self.bridge.writes, [])

    def test_partial_ram_failure_never_saves(self):
        self.bridge.fail_offset = 0x30
        with self.assertRaises(TransferError):
            self.run_program()
        self.assertNotIn(2, self.bridge.commands)
        self.assertEqual(self.bridge.nonvolatile, self.original)
        self.assertFalse(self.bridge.armed)

    def test_bad_ram_readback_never_saves(self):
        self.bridge.corrupt_staged = True
        with self.assertRaises(ProgrammingError):
            self.run_program()
        self.assertNotIn(2, self.bridge.commands)
        self.assertEqual(self.bridge.nonvolatile, self.original)

    def test_crc_save_error_is_not_reset_or_retried(self):
        self.bridge.save_error = True
        with self.assertRaises(ProgrammingError):
            self.run_program()
        self.assertEqual(self.bridge.commands, [255, 2])
        self.assertEqual(self.bridge.nonvolatile, self.original)

    def test_lost_save_ack_can_be_verified_without_resending(self):
        self.bridge.lose_save_ack = True
        self.run_program()
        self.assertEqual(self.bridge.commands.count(2), 1)
        self.assertIn("save_ack_uncertain", self.journal.events)
        self.assertEqual(self.journal.events[-1], "saved_reset_verified")

    def test_dropped_save_is_caught_after_reset(self):
        self.bridge.drop_save = True
        with self.assertRaises(ProgrammingError):
            self.run_program()
        self.assertEqual(self.bridge.commands.count(2), 1)
        self.assertEqual(self.bridge.nonvolatile, self.original)
        self.assertEqual(self.journal.events[-1], "failed_or_uncertain")

    def test_unconfirmed_reset_never_reports_success(self):
        self.bridge.fail_reset_number = 2
        with self.assertRaises(ProgrammingError):
            self.run_program()
        self.assertNotIn("saved_reset_verified", self.journal.events)

    def test_runtime_sensor_disable_does_not_cause_repeated_saves(self):
        self.bridge.ram[:] = self.target
        self.bridge.nonvolatile = self.target
        self.bridge.runtime_disable = 9
        self.run_program()
        self.assertNotIn(2, self.bridge.commands)
        self.assertTrue(configuration_matches(bytes(self.bridge.ram), self.target))
        self.assertFalse(configuration_matches(bytes(self.bridge.ram), self.original))

    def test_command_busy_is_bounded_and_never_writes(self):
        self.bridge.keep_busy = True
        with self.assertRaises(ProgrammingError):
            self.run_program()
        self.assertEqual(self.bridge.commands, [])
        self.assertEqual(self.bridge.writes, [])

    def test_unexplained_sensor_disable_is_not_accepted(self):
        self.bridge.ram[:] = self.target
        self.bridge.nonvolatile = self.target
        self.bridge.runtime_disable = 9
        self.bridge.missing_diagnostics = True
        with self.assertRaises(ProgrammingError):
            self.run_program()
        self.assertNotIn(2, self.bridge.commands)
        self.assertNotIn("already_configured_no_flash_write", self.journal.events)

    def test_returned_chip2_is_programmed_and_verified(self):
        original = load_profiles(ROOT / "profiles/original_profiles.json")[2]
        target = load_profiles(ROOT / "profiles/profiles.json")[2]
        bridge = MemoryBridge(original)
        programmer = Programmer(bridge, delay=lambda seconds: None, log=lambda message: None)
        programmer.program(0x39, target, self.journal)
        self.assertEqual(bridge.nonvolatile, target)
        self.assertEqual(bridge.commands, [255, 2, 255])
        self.assertEqual(self.journal.events[-1], "saved_reset_verified")

    def test_outside_address_is_rejected_before_access(self):
        with self.assertRaises(ProgrammingError):
            self.programmer.program(0x36, self.target, self.journal)
        self.assertEqual(self.bridge.commands, [])

    def test_fast_error_retries_but_low_bus_does_not(self):
        attempts = []

        def operation():
            attempts.append(1)
            if len(attempts) < 3:
                raise TransferError(0x108, 3, 3, 300)
            return b"OK"

        self.assertEqual(self.programmer.bounded(operation), b"OK")
        self.assertEqual(len(attempts), 3)
        attempts.clear()

        def low_bus():
            attempts.append(1)
            raise TransferError(0x108, 2, 2, 10000)

        with self.assertRaises(TransferError):
            self.programmer.bounded(low_bus)
        self.assertEqual(len(attempts), 1)

    def test_file_journal_preserves_full_images(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(ROOT.resolve()))
            journal = FileJournal(Path(directory), 0x37)
            self.programmer.program(0x37, self.target, journal)
            document = json.loads(journal.path.read_text(encoding="utf-8"))
            self.assertEqual(document["before"]["data"], self.original.hex())
            self.assertEqual(document["after_reset"]["data"], self.original.hex())
            self.assertEqual(document["result"]["data"], self.target.hex())
            self.assertEqual(document["status"], "saved_reset_verified")

    def test_profile_tampering_is_rejected(self):
        document = json.loads((ROOT / "profiles/profiles.json").read_text(encoding="utf-8"))
        document = copy.deepcopy(document)
        document["images"][2]["enabled"] = False
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(ROOT.resolve()))
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(ProgrammingError):
                load_profiles(path)


if __name__ == "__main__":
    unittest.main()
