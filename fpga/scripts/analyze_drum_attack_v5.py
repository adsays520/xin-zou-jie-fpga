"""Measure the second dark-onset revision against the listener-rejected v4."""
from pathlib import Path
import json
import numpy as np

from analyze_drum_attack import FRAMES, ROOT, VOICES, load, spectrum


def main():
    previous = json.loads((ROOT / "docs/drum_attack_v4_metrics.json").read_text(encoding="utf-8"))
    current = load(ROOT / "impl/drum_v5_voices_q23.txt")
    report = {"sample_rate": 48000, "source": "RTL 48 kHz outputs, no recorded input",
              "comparison": "v4 RTL listener-rejected onset", "voices": []}
    for old in previous["voices"]:
        kit, name = old["kit"], old["voice"]
        voice = next(index for index, label in VOICES.items() if label == name)
        length = 1440 if voice == 0 else 480
        samples = current[(current[:, 0] == kit) & (current[:, 1] == voice), 3]
        new = spectrum(samples[:length])
        old_centroid = old["after"]["spectral_centroid_hz"]
        if new["spectral_centroid_hz"] >= old_centroid:
            raise AssertionError(f"{name} kit {kit} did not darken further")
        report["voices"].append({"kit": kit, "voice": name,
            "onset_window_ms": length / 48,
            "v4_centroid_hz": old_centroid,
            "v5_centroid_hz": new["spectral_centroid_hz"],
            "v5_onset_rms_q23": new["rms_q23"]})
    old_preview = np.loadtxt(ROOT / "impl/drum_sim/drum_v4_rtl_preview_q23.txt", dtype=np.int32)
    new_preview = np.loadtxt(ROOT / "impl/drum_sim/drum_v5_rtl_preview_q23.txt", dtype=np.int32)
    if old_preview.shape != (240000, 2) or new_preview.shape != old_preview.shape:
        raise ValueError("Missing kit-1 RTL listening previews")
    tail = {}
    for segment, name in ((1, "closed_hat"), (2, "open_hat"), (3, "crash"), (4, "ride")):
        start = segment * 48000 + 1920
        stop = segment * 48000 + 48000
        old_rms = float(np.sqrt(np.mean(old_preview[start:stop].astype(float) ** 2)))
        new_rms = float(np.sqrt(np.mean(new_preview[start:stop].astype(float) ** 2)))
        tail[name] = new_rms / old_rms
        if not 0.95 <= tail[name] <= 1.05:
            raise AssertionError(f"{name} sustained level shifted: {tail[name]}")
    report["kit1_sustain_after_40ms_rms_ratio"] = tail
    out = ROOT / "docs/drum_attack_v5_metrics.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS v5 onset darker in all 15 kit/voice checks; v4 cymbal tails retained")


if __name__ == "__main__":
    main()
