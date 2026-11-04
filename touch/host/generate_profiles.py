import argparse
import binascii
import hashlib
import json
import re
import shutil
from pathlib import Path


NAMES = ("01", "02", "03", "03a", "03B", "03C", "03D", "03E")
ACTIVE_MASK = 0xFF
BUTTON_LBR_SAMPLES = 10


def config_crc(data):
    return binascii.crc_hqx(data[:126], 0xFFFF)


def validate_config(data, address):
    if len(data) != 128 or data[0x51] != address:
        raise ValueError("Configuration length or address mismatch")
    if config_crc(data) != int.from_bytes(data[126:128], "little"):
        raise ValueError("Configuration CRC mismatch")
    if data[0x50] != 0:
        raise ValueError("Configuration is not for internally regulated 3.3 V operation")


def parse_hex(text):
    memory = {}
    base = 0
    ended = False
    for line in text.splitlines():
        if not line.strip():
            continue
        if ended or not line.startswith(":"):
            raise ValueError("Unexpected Intel HEX record")
        record = bytes.fromhex(line[1:])
        if len(record) < 5 or len(record) != record[0] + 5 or sum(record) & 0xFF:
            raise ValueError("Intel HEX record length/checksum mismatch")
        offset = int.from_bytes(record[1:3], "big")
        kind = record[3]
        payload = record[4:-1]
        if kind == 0:
            for index, value in enumerate(payload):
                absolute = base + offset + index
                if absolute in memory:
                    raise ValueError("Overlapping Intel HEX data")
                memory[absolute] = value
        elif kind == 4 and len(payload) == 2 and offset == 0:
            base = int.from_bytes(payload, "big") << 16
        elif kind == 1 and not payload and offset == 0:
            ended = True
        else:
            raise ValueError("Unsupported Intel HEX record")
    if not ended:
        raise ValueError("Missing Intel HEX EOF")
    expected = set(range(128)) | {0x90300000, 0x90300001} | set(range(0x90500000, 0x90500007))
    if set(memory) != expected:
        raise ValueError("Unexpected EZ-Click metadata or incomplete register data")
    data = bytes(memory[index] for index in range(128))
    metadata = bytes(memory[0x90500000 + index] for index in range(7))
    stored_sum = (memory[0x90300000] << 8) | memory[0x90300001]
    if stored_sum != sum(data) & 0xFFFF:
        raise ValueError("EZ-Click configuration checksum mismatch")
    if metadata[2:4] != bytes((data[0x51], data[0x51])) or metadata[4:] != bytes.fromhex("0A059A"):
        raise ValueError("EZ-Click device/address metadata mismatch")
    return data, metadata


def hex_record(offset, kind, payload):
    raw = bytes((len(payload), offset >> 8, offset & 255, kind)) + payload
    return ":" + (raw + bytes((-sum(raw) & 255,))).hex().upper()


def encode_hex(data, metadata):
    return "\n".join((
        hex_record(0, 0, data),
        hex_record(0, 4, bytes.fromhex("9030")),
        hex_record(0, 0, (sum(data) & 0xFFFF).to_bytes(2, "big")),
        hex_record(0, 4, bytes.fromhex("9050")),
        hex_record(0, 0, metadata),
        hex_record(0, 1, b""),
    )) + "\n"


def performance_config(original):
    data = bytearray(original)
    data[0x1C] = (data[0x1C] & 0xF0) | 3
    # Trial: rebuild a low baseline after 10 qualifying samples. Bit 7
    # enables the override; zero would retain SmartSense's default.
    data[0x1F] = 0x80 | BUTTON_LBR_SAMPLES
    data[0x4F] &= ~0x30
    data[0x52] = 1
    data[126:128] = config_crc(data).to_bytes(2, "little")
    return bytes(data)


def save_image(directory, data, metadata):
    directory.mkdir(parents=True, exist_ok=True)
    address = data[0x51]
    stem = f"addr_{address:02X}"
    (directory / f"{stem}.bin").write_bytes(data)
    (directory / f"{stem}.hex").write_text(encode_hex(data, metadata), encoding="ascii")
    rows = ["    " + ", ".join(f"0x{value:02X}" for value in data[start:start + 8]) + ","
            for start in range(0, 128, 8)]
    header = "#pragma once\n#include <stdint.h>\n\n"
    header += f"static const uint8_t cy8_config_{address:02x}[128] = {{\n"
    header += "\n".join(rows) + "\n};\n"
    (directory / f"{stem}.h").write_text(header, encoding="ascii")
    attention = f"[SPEED=100K] [VCC=3.3V]\nr {address:02x} x p [delay=10] r {address:02x} x p [delay=10]\n"
    stage = attention + f"w {address:02x} 00 " + data.hex(" ") + " p\n"
    stage += f"w {address:02x} 00 r {address:02x} " + "x " * 128 + "p\n"
    save = attention + f"w {address:02x} 86 02 p [delay=300]\n"
    for reg, count in ((0x86, 1), (0x88, 2), (0x8C, 1)):
        save += f"w {address:02x} {reg:02x} r {address:02x} " + "x " * count + "p\n"
    verify = attention + f"w {address:02x} 86 ff p [delay=1500]\n"
    verify += f"w {address:02x} 00 r {address:02x} " + "x " * 128 + "p\n"
    verify += f"w {address:02x} 90 r {address:02x} x x p\n"
    for name, contents in (("01_stage_readback", stage), ("02_save_check", save), ("03_reset_verify", verify)):
        (directory / f"{stem}_{name}.iic").write_text(contents, encoding="ascii")


def generate(source, output):
    profiles = []
    originals = []
    sources = []
    for chip, name in enumerate(NAMES):
        directory = source / name
        data, metadata = parse_hex((directory / f"{name}.hex").read_text(encoding="ascii"))
        address = 0x37 + chip
        validate_config(data, address)
        header = bytes(int(value, 16) for value in re.findall(
            r"0x([0-9a-fA-F]{2})u", (directory / f"{name}.h").read_text(encoding="utf-8-sig")))
        script = (directory / f"{name}.iic").read_text(encoding="utf-8-sig")
        match = re.search(rf"^w {address:02x} 00 ([0-9a-fA-F ]+) p$", script, re.MULTILINE)
        if header != data or match is None or bytes.fromhex(match[1]) != data:
            raise ValueError(f"HEX/header/IIC disagree: {name}")
        changed = performance_config(data)
        validate_config(changed, address)
        original_dir = output / "originals" / name
        original_dir.mkdir(parents=True, exist_ok=True)
        for suffix in ("hex", "h", "iic", "cprj"):
            origin = directory / f"{name}.{suffix}"
            shutil.copyfile(origin, original_dir / origin.name)
            sources.append({"source": str(origin), "sha256": hashlib.sha256(origin.read_bytes()).hexdigest()})
        entry = {"chip": chip, "address": address, "enabled": bool(ACTIVE_MASK & (1 << chip)),
                 "data": changed.hex(), "sha256": hashlib.sha256(changed).hexdigest(),
                 "changes": [{"register": offset, "old": before, "new": after}
                             for offset, (before, after) in enumerate(zip(data, changed)) if before != after]}
        profiles.append(entry)
        originals.append({**entry, "data": data.hex(), "sha256": hashlib.sha256(data).hexdigest(), "changes": []})
        if entry["enabled"]:
            save_image(output / "performance" / f"chip{chip}_{address:02X}", changed, metadata)
    for name, mode, entries in (("profiles.json", "performance", profiles),
                                ("original_profiles.json", "original_template", originals)):
        (output / name).write_text(json.dumps({"schema": 1, "mode": mode, "active_mask": ACTIVE_MASK,
            "device_id": 0x0A05, "images": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "source_hashes.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validated 8 HEX/header/IIC sets; generated {ACTIVE_MASK.bit_count()} active performance profiles in {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("D:/EZ_CLIK2"))
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "profiles")
    args = parser.parse_args()
    generate(args.source, args.output)


if __name__ == "__main__":
    main()
