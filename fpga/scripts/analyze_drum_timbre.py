"""Check the cymbal spectrum of actual 48 kHz RTL frames (no recorded input)."""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRAMES = 2048
RATE = 48000
VOICES = {2: "closed_hat", 3: "open_hat", 5: "crash", 6: "ride"}


def read(path):
    rows = np.loadtxt(path, dtype=np.int32)
    if rows.shape != (3 * 12 * FRAMES, 5):
        raise ValueError(f"Incomplete RTL audio dump: {rows.shape}")
    return rows


def metrics(rows, kit, voice):
    samples = rows[(rows[:, 0] == kit) & (rows[:, 1] == voice), 3:5]
    if samples.shape != (FRAMES, 2):
        raise ValueError(f"Missing samples for kit {kit}, voice {voice}")
    centered = samples[:, 0].astype(np.float64) - samples[:, 0].mean()
    power = np.abs(np.fft.rfft(centered * np.hanning(FRAMES))) ** 2
    freqs = np.fft.rfftfreq(FRAMES, 1 / RATE)
    total = power.sum()
    if total == 0:
        raise ValueError(f"Silent cymbal: kit {kit}, voice {voice}")
    return {
        "peak_q23": int(np.max(np.abs(samples))),
        "energy_above_3khz": float(power[freqs >= 3000].sum() / total),
        "energy_below_1_5khz": float(power[freqs < 1500].sum() / total),
    }


def main():
    after = read(ROOT / "impl/drum_sim/drum_voices_q23.txt")
    before_path = ROOT / "impl/drum_timbre_before_q23.txt"
    before = read(before_path) if before_path.exists() else None
    report = {"sample_rate": RATE, "frames_per_voice": FRAMES,
              "source": "RTL sample_valid output; algorithmic synthesis, no recorded samples",
              "cymbals": []}
    for kit in range(3):
        for voice, name in VOICES.items():
            current = metrics(after, kit, voice)
            # Reject a pitched sine/square-dominated cymbal or an inaudible fix.
            if current["energy_above_3khz"] < 0.75 or current["energy_below_1_5khz"] > 0.15:
                raise AssertionError(f"Low tonal leakage remains in {name}, kit {kit}: {current}")
            if current["peak_q23"] < 10000:
                raise AssertionError(f"Cymbal too quiet: {name}, kit {kit}")
            item = {"kit": kit, "voice": name, "after": current}
            if before is not None:
                item["before"] = metrics(before, kit, voice)
            report["cymbals"].append(item)
    if before is not None:
        for voice in (0, 1, 4, 7, 8, 9, 10, 11):
            if not np.array_equal(before[before[:, 1] == voice, 3:5],
                                  after[after[:, 1] == voice, 3:5]):
                raise AssertionError(f"Non-cymbal voice {voice} changed")
        report["non_cymbal_stereo_bit_exact"] = True
    path = ROOT / "docs/drum_timbre_v3_metrics.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS cymbal spectra: {len(report['cymbals'])} kit/voice combinations; "
          f"other voices bit exact={report.get('non_cymbal_stereo_bit_exact', 'not compared')}")


if __name__ == "__main__":
    main()
