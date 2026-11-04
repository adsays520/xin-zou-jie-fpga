"""Compare actual RTL cymbal/kick onset spectra against the last board build."""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRAMES = 2048
RATE = 48000
VOICES = {0: "kick", 2: "closed_hat", 3: "open_hat", 5: "crash", 6: "ride"}


def load(path):
    rows = np.loadtxt(path, dtype=np.int32)
    if rows.shape != (3 * 12 * FRAMES, 5):
        raise ValueError(f"Incomplete RTL dump {path}: {rows.shape}")
    return rows


def spectrum(samples):
    centered = samples.astype(float) - samples.mean()
    power = abs(np.fft.rfft(centered * np.hanning(len(samples)))) ** 2
    freqs = np.fft.rfftfreq(len(samples), 1 / RATE)
    total = power.sum()
    return {
        "rms_q23": float(np.sqrt(np.mean(samples.astype(float) ** 2))),
        "energy_above_3khz": float(power[freqs >= 3000].sum() / total),
        "spectral_centroid_hz": float((power * freqs).sum() / total),
    }


def main():
    before = load(ROOT / "impl/drum_v3_before_timing_q23.txt")
    after = load(ROOT / "impl/drum_sim/drum_voices_q23.txt")
    report = {"sample_rate": RATE, "source": "48 kHz RTL output; no recorded samples",
              "prior": "v3_r0 board build", "voices": []}
    for kit in range(3):
        for voice, name in VOICES.items():
            old = before[(before[:, 0] == kit) & (before[:, 1] == voice), 3]
            new = after[(after[:, 0] == kit) & (after[:, 1] == voice), 3]
            n = 1440 if voice == 0 else 480
            a, b = spectrum(old[:n]), spectrum(new[:n])
            entry = {"kit": kit, "voice": name,
                     "window_ms": n * 1000 / RATE,
                     "before": a, "after": b}
            if voice == 0:
                if b["spectral_centroid_hz"] >= a["spectral_centroid_hz"]:
                    raise AssertionError(f"Kick got brighter: kit {kit}: {a} -> {b}")
            else:
                if b["spectral_centroid_hz"] >= a["spectral_centroid_hz"]:
                    raise AssertionError(f"Cymbal onset got brighter: {name}, kit {kit}: {a} -> {b}")
                tail_before = spectrum(old[480:1920])
                tail_after = spectrum(new[480:1920])
                ratio = tail_after["rms_q23"] / tail_before["rms_q23"]
                entry["tail_10_40ms_rms_ratio"] = ratio
                if not 0.95 <= ratio <= 1.05:
                    raise AssertionError(f"Cymbal sustain changed: {name}, kit {kit}: {ratio}")
            report["voices"].append(entry)
    out = ROOT / "docs/drum_attack_v4_metrics.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS onset spectrum darkened: {len(report['voices'])} kit/voice combinations")


if __name__ == "__main__":
    main()
