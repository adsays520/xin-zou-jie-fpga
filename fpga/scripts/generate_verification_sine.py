"""Generate exactly one mathematical sine period; no audio files are read."""
from pathlib import Path
import math,sys
target=Path(__file__).resolve().parent.parent/'src/verification/sine1024.hex'
content=''.join('%04x\n' % (round(32767*math.sin(2*math.pi*n/1024)) & 65535) for n in range(1024))
if '--check' in sys.argv:
    assert target.read_text(encoding='ascii').lower()==content,'Sine ROM differs from mathematical table'
    print('PASS: DDS ROM is exactly one 1024-point mathematical sine period, not recorded audio')
else:
    target.write_text(content,encoding='ascii')
    print('Generated',target)
