"""Selected phrases from the user's two violin PNGs, not a complete edition.

Durations use sixteenths. Repeats/endings are not expanded. Mappings to the
different piano layout live in fuji_score_bow.py. ~ merges equal-pitch ties.
"""
from fractions import Fraction
from fuji_score import midi

EXCERPTS = {
    9: '0:4 0:2 C4:2 D4:2 F4:2 G4:2 F4:2',
    10: 'G4:2 A4:4 A4:4 A4:2 G4:2 F4:2',
    11: 'G4:2 A4:4 A4:4 A4:2 G4:2 F4:2',
    12: 'G4:3 F4:1 ~F4:2 D4:2 F4:3 G4:1 ~G4:2 A4:2',
    13: 'A4:6 C4:2 D4:2 F4:2 G4:2 F4:2',
    16: 'G4:3 G4:1 ~G4:2 G4:2 G4:3 F4:1 ~F4:2 D4:2',
    20: 'G4:3 F4:1 ~F4:2 D4:2 G4:3 G4:1 ~G4:2 A4:2',
    24: 'G4:3 G4:1 ~G4:2 G4:2 G4:3 F4:1 ~F4:2 D4:2',
    25: 'F4:6 F4:2 F5:2 E5:2 D5:2 C5:2',
    26: 'F5:3 E5:1 ~E5:2 D5:2 E5:2 D5:2 A4:2 G4:2',
    27: 'A4:2 C5:2 D5:2 C5:2 0:2 C5:2 D5:2 C5:2',
    30: 'C5:2 A4:2 G4:2 F4:2 0:2 F4:2 G4:2 A4:2',
    31: 'D5:2 A4:2 G4:2 F4:2 0:2 F4:2 F4:2 F4:2',
    34: 'F5:2 E5:2 D5:2 C5:2 D5:2 C5:2 A4:2 G4:2',
    35: 'A4:2 C5:2 D5:2 C5:2 0:2 C5:2 D5:2 C5:2',
    38: 'C5:2 A4:2 G4:2 F4:2 0:2 F4:2 G4:2 A4:2',
    39: 'D5:2 A4:2 G4:2 F4:2 F5:8',
    40: '~F5:8 0:2 F5:2 D5:2 F5:2',
    41: 'D5:2 C5:4 C5:2 D5:2 C5:2 A4:2 G4:2',
    57: 'C5:2 A4:6 0:2 F4:2 G4:2 A4:2',
    62: 'A4:2 G4:4 F4:2 D4:8/3 F4:8/3 G4:8/3',
    63: 'F4:16',
    64: '0:4 0:2 F4:2 D4:2 F4:2',
    67: 'F5:16',
}

def phrase_notes(first, last=None):
    """Notes relative to first printed bar; retain provenance and merge ties."""
    last = first if last is None else last
    result, position, previous = [], Fraction(0), None
    for bar in range(first, last + 1):
        local = Fraction(0)
        for token in EXCERPTS[bar].split():
            symbol, length = token.split(':')
            duration = Fraction(length)
            if symbol != '0':
                tied, name = symbol.startswith('~'), symbol.lstrip('~')
                pitch, start = midi(name), position + local
                if tied and previous and previous['pitch'] == pitch and previous['end'] == start:
                    previous['end'] += duration
                    previous['source_bars'].append(bar)
                else:
                    if tied and local != 0:
                        raise ValueError(f'Broken source tie at {bar}: {token}')
                    previous = {'start': start, 'end': start + duration, 'pitch': pitch,
                                'name': name, 'source_bars': [bar]}
                    result.append(previous)
            local += duration
        expected = 12 if bar == 64 else 16
        if local != expected:
            raise ValueError(f'Violin bar {bar}: {local}, expected {expected}')
        position += local
    return result
