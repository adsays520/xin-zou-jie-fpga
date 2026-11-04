"""Generate mathematical oscillator/parameter ROMs; contains no recorded audio."""
from pathlib import Path
import math
import json

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000
# ID order is shared by RTL and the host. Frequencies are modal oscillator Hz.
VOICES = [
    ("kick", [0, 0, 0, 0, 0, 0], 0, 0, 0, 0),
    ("snare", [185, 330, 589, 770, 1040, 1370], 45, 12, 12, 8),
    ("closed_hat", [828, 1080, 1214, 1480, 1600, 2100], 0, 9, 9, 8),
    ("open_hat", [828, 1080, 1214, 1480, 1600, 2100], 0, 13, 13, 8),
    ("clap", [190, 370, 620, 980, 1510, 2100], 0, 10, 12, 8),
    ("crash", [1360, 1847, 2459, 3383, 4621, 6173], 0, 12, 15, 8),
    ("ride", [920, 1527, 2189, 2917, 4363, 5813], 0, 11, 13, 8),
    ("low_tom", [91, 147, 221, 287, 379, 491], 65, 13, 9, 10),
    ("mid_tom", [132, 211, 318, 414, 546, 711], 75, 12, 9, 10),
    ("high_tom", [183, 293, 441, 569, 758, 984], 85, 12, 9, 10),
    ("rim", [780, 1730, 2460, 3140, 4210, 5500], 0, 9, 7, 8),
    ("cowbell", [540, 800, 1140, 1590, 2350, 3100], 0, 12, 8, 8),
]

def write_rom(out, name, values, width):
    """Keep existing HDL inputs unchanged when only exporting IP init files."""
    digits = (width + 3) // 4
    hex_data = "".join(f"{x & ((1 << width) - 1):0{digits}x}\n" for x in values)
    hex_path = out / f"{name}.hex"
    if not hex_path.exists() or hex_path.read_text() != hex_data:
        hex_path.write_text(hex_data, encoding="ascii")
    # Explicit addresses avoid relying on an IP editor's display order.
    mi_data = (f"#File_format=AddrHex\n#Address_depth={len(values)}\n"
               f"#Data_width={width}\n")
    mi_data += "".join(f"{i:x}:{x & ((1 << width) - 1):0{digits}x}\n"
                       for i, x in enumerate(values))
    (out / f"{name}.mi").write_text(mi_data, encoding="ascii")


def main():
    out = ROOT / "src/drums/rom"
    out.mkdir(parents=True, exist_ok=True)
    sine = [round(32767 * math.sin(2 * math.pi * i / 1024)) for i in range(1024)]
    write_rom(out, "sine", sine, 16)
    # Each kit has 16 voice slots, each with 8 words: six frequencies,
    # pitch excursion, and packed exponential leak/filter parameters.
    words = [0] * 512
    for kit in range(3):
        for voice, (name, freqs, sweep, body, noise, pitch) in enumerate(VOICES):
            tune = [1.0, 1.0, 1.07][kit]
            b = body
            n = noise
            if kit != 0:
                # Acoustic-inspired shell/click/rattle decay, in 48 kHz samples.
                body = [12, 11, 9, 12, 10, 12, 11, 12, 12, 11, 9, 11][voice]
                noise = [6, 12, 9, 12, 12, 14, 13, 8, 8, 8, 7, 8][voice]
                sweep = [95, 18, 0, 0, 0, 0, 0, 55, 65, 75, 0, 0][voice]
                pitch = [8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 8, 8][voice]
                b, n = body, noise
                if kit == 2:
                    n = max(6, n - (voice in (1, 3, 5, 6)))
            if voice == 0:
                b, n, sweep, pitch = 0, 0, 0, 0  # Dedicated kick_modal owns this voice.
            lp = 2 if voice in (7, 8, 9, 10) else 1
            hp = 3 if voice in (0, 2, 3, 5, 6) else 5
            base = (kit * 16 + voice) * 8
            values = [round(f * tune * 2**32 / RATE) for f in freqs]
            values += [round(sweep * tune * 2**32 / RATE), b | (n << 4) | (pitch << 8) | (lp << 12) | (hp << 16)]
            words[base:base + 8] = values
    write_rom(out, "params", words, 32)
    (out / "manifest.json").write_text(json.dumps({"sample_rate": RATE, "algorithm": "modal oscillators + filtered PRNG noise + exponential envelopes", "recorded_samples": False, "voices": [v[0] for v in VOICES], "kits": ["Natural modal", "Tight pop", "Bright rock"]}, indent=2))
    print("Generated mathematical sine and synthesis parameters as HDL .hex and Gowin IP .mi (no PCM).")

if __name__ == "__main__":
    main()
