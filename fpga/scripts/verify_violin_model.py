import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1] / 'violin_r15'
PROJECT = ROOT.parent
sys.path.insert(0, str(PROJECT / 'tests/violin_model'))
from fixed_model import Arithmetic, BowedVoice, BodyFilter, decimate_int, round_shift


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', type=int, default=5000)
    args = parser.parse_args()
    directory = ROOT / 'test_results'
    directory.mkdir(exist_ok=True)
    events = {
        0: (69, 100, 1), 800: (71, 80, 3), 1400: (69, 1, 0),
        2000: (55, 127, 1), 2700: (55, 1, 0), 3200: (100, 127, 1),
        4000: (100, 1, 0), 6000: (69, 100, 1), 21000: (72, 100, 3),
        25000: (72, 1, 0),
    }
    arithmetic = Arithmetic()
    voice = BowedVoice(arithmetic=arithmetic)
    body = BodyFilter(voice.tables, arithmetic)
    internal = []
    commands = []
    current_key = 69
    for frame in range(args.frames):
        event = events.get(frame)
        command = 0
        if event:
            key, velocity, action = event
            command = (1 << 17) | ((action == 3) << 15) | ((action != 0) << 14) | (key << 7) | velocity
            if action:
                voice.note_on(key, velocity, action == 3)
                current_key = key
            elif key == current_key:
                voice.note_off()
        commands.append(command)
        for substep in range(2):
            value = body.process(voice.process() << 4)
            internal.append(arithmetic.fit(round_shift(value * voice.tables.output_gain, 31), 24, 'output'))
    pcm = decimate_int(np.asarray(internal, dtype=np.int64), voice.tables, arithmetic)
    for name, values, width in [('internal.hex', internal, 24), ('expected.hex', pcm, 24), ('commands.hex', commands, 18)]:
        (directory / name).write_text(''.join(f'{int(value) & ((1 << width)-1):0{(width+3)//4}x}\n' for value in values), encoding='ascii')
    (directory / 'reference.json').write_text(json.dumps({'frames': args.frames, 'events': events, 'overflows': arithmetic.overflows}, indent=2) + '\n', encoding='utf-8')
    print(f'Generated {args.frames} frames, {len(internal)} internal samples; overflow={arithmetic.overflows}')


if __name__ == '__main__':
    main()
