"""Export the actual RTL output as a normalized listening file, not a ROM input."""
from pathlib import Path
import wave
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "impl/drum_sim/drum_v5_rtl_preview_q23.txt"
OUTPUT = ROOT / "previews/drums_v5/rtl_dry_rock_kick_ch_oh_crash_ride.wav"


def main():
    q23 = np.loadtxt(INPUT, dtype=np.int32)
    if q23.shape != (240000, 2):
        raise ValueError(f"Expected five seconds of stereo RTL audio: {q23.shape}")
    peak = int(np.abs(q23.astype(np.int64)).max())
    if peak <= 0:
        raise ValueError("Silent RTL output")
    # One common gain across the whole preview preserves the relative levels.
    pcm16 = np.round(q23.astype(np.float64) * (28000.0 / peak)).clip(-32768, 32767).astype('<i2')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        wav.writeframes(pcm16.tobytes())
    print(f"RTL preview: {OUTPUT} (common normalization from peak {peak} Q23)")


if __name__ == '__main__':
    main()
