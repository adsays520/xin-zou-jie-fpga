import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
rom = ROOT / "src/drums/rom"
words = [0] * 1024
for filename, start, count in (("params.hex", 0, 512), ("kick_modal_coeffs.hex", 512, 108),
                               ("kick_force.hex", 640, 120)):
    values = [int(value, 16) for value in (rom / filename).read_text().split()]
    assert len(values) == count, filename
    words[start:start + count] = values
payload = struct.pack("<768I", *words[:768])
checksum = zlib.crc32(payload)
(ROOT / "sd_card/DRUMS.BIN").write_bytes(payload)
(rom / "drum_bank.hex").write_text("".join(f"{value:08x}\n" for value in words + [0] * 1024), encoding="utf-8")
(rom / "drum_bank_config.vh").write_text(
    f"`ifndef DRUM_BANK_CONFIG_VH\n`define DRUM_BANK_CONFIG_VH\n`define DRUM_BANK_CRC32 32'h{checksum:08x}\n`endif\n",
    encoding="utf-8")
manifest = {"file": "DRUMS.BIN", "bytes": len(payload), "word_endian": "little",
            "CRC32": f"{checksum:08X}", "SHA256": hashlib.sha256(payload).hexdigest(),
            "word_ranges": {"drum_parameters": [0, 511], "kick_coefficients": [512, 619],
                            "force_shape": [640, 759]}, "recorded_audio": False}
(ROOT / "sd_card/DRUMS_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
