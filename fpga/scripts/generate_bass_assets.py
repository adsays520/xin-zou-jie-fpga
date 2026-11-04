"""Generate original analytic bass tables, not sampled/copyrighted recordings."""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[1]
SIZE = 2048
FS = 48000


def tables():
    # Pickup-position notches, strong fundamental, audible second/third partials.
    def wave(weights):
        raw = [sum(w * math.sin(2 * math.pi * h * n / SIZE)
                   for h, w in enumerate(weights, 1)) for n in range(SIZE)]
        scale = 30000 / max(abs(x) for x in raw)
        return [round(x * scale) for x in raw]
    bright = wave([1, .52, .32, .17, .085, .055, .034, .026, .018, .012, .008, .005])
    dark = wave([1, .32, .13, .047, .018, .007])
    pitch = [0] * 128
    for row, base in enumerate((98, 73.415, 55, 41.205)):
        for fret in range(21):
            pitch[row * 32 + fret] = round(base * 2**(fret / 12) / FS * 2**32)
    return bright, dark, pitch


if __name__ == '__main__':
    bright, dark, pitch = tables()
    folder = ROOT / 'src' / 'bass'
    folder.mkdir(exist_ok=True)
    (folder / 'bass_wave.hex').write_text(''.join(
        f'{((b & 65535) << 16) | (d & 65535):08x}\n' for b, d in zip(bright, dark)), encoding='ascii')
    (folder / 'bass_pitch.hex').write_text(''.join(f'{p:08x}\n' for p in pitch), encoding='ascii')
    print('Generated 2048 packed wave samples and 84 valid Bass note steps.')
