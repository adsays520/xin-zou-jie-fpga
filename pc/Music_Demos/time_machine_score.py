"""Working transcription of the user's three-page Time Machine piano PDF.

Five flats, 6/8, 72 printed bars. Symbols are sounding pitches, including all
8va passages; durations are eighths, ^ rolls chords, ~ continues a same-pitch
tie, and 0 denotes rest. The PDF does not specify a tempo. Ambiguous ornamental
spacing is regularized; this is an editable performance transcription.
"""
from fractions import Fraction

from fuji_score import midi


RIGHT = [
    '^F5,Bb5,Eb6:1/2 F6:1/2 Eb6:1/2 F6:1/2 Eb6:1/2 F6:1/2 Ab6:3',
    '^Eb5,Ab5,Eb6:1/2 F6:1/2 Eb6:1/2 F6:1/2 Eb6:1/2 F6:1/2 Ab6:1 F6:1 Eb6:1',
    '^Db5,Gb5,Bb5:1 F6:2 ^C5,Eb5,Ab5:1 Eb6:1 C6:1',
    '^F5,Ab5,Db6:6',
    'Bb4:1 Db5:1 Eb5:1 F5:3',
    'Bb4:1 Db5:1 Eb5:1 F5:3',
    'Bb4:1 Db5:1 Eb5:1 F5:1 Eb5:1/3 F5:1/3 Eb5:1/3 Db5:1',
    'F5:1 Ab5:1 F5:1 Eb5:3',
    'Bb4:1 Db5:1 Eb5:1 F5:2 Bb4:1',
    'Bb4:1 Db5:1 Eb5:1 F5:2 Bb4:1',
    'Bb4:1 Db5:1 Eb5:1 Bb4,F5:1 Eb5:1/3 F5:1/3 Eb5:1/3 Db5:1',
    'F5:1 Ab5:1 F5:1/2 Eb5:1/2 Eb5:3',
    'Bb5:1 Ab5:1 Bb5:1 F5:1 Eb5:1/3 F5:1/3 Eb5:1/3 Db5:1',
    'Bb5:1 Ab5:1 Bb5:1 F5:2 Db5:1',
    'Bb5:1 Ab5:1 Bb5:1 F5:1 Eb5:1 Db5:1',
    'Ab5:1 Ab5:1 Bb5:1 F5:3',
    'Bb4:1 Db5:1 Eb5:1 F5:1 Eb5:1/3 F5:1/3 Eb5:1/3 Db5:1',
    'Bb5:1 Ab5:1 Bb5:1 F5:2 Bb4:1',
    'Bb4:1 Db5:1 Eb5:1 Bb4,F5:1 Eb5:1/3 F5:1/3 Eb5:1/3 Db5:1',
    'Db5:3 0:3',
    '^Bb4,Eb5:1/2 F5:1/2 Eb5:1/2 F5:1/2 Eb5:1/2 F5:1/2 Ab5:3',
    '^Ab4,Eb5:1/2 F5:1/2 Eb5:1/2 F5:1/2 Eb5:1/2 F5:1/2 Ab5:1 F5:1 Eb5:1',
    '^Gb4,Bb4:1 F5:2 ^Eb4,Ab4:1 Eb5:1 C5:1',
    '^Ab4,Db5:3 Ab4:3',
    'Bb4:1 Db5:1 Eb5:1 F5:1 Eb5:1 Db5:1',
    'Bb4:1 Db5:1 Eb5:1 F5:2 Bb4:1',
    'Bb4:1 Db5:1 Eb5:1 Bb4,F5:1 Eb5:1 Db5:1',
    'F5:1 Ab5:1 F5:1 Eb5:3',
    'Bb4:1 Db5:1 Eb5:1 F5:1 Eb5:1 Db5:1',
    'Bb4:1 Db5:1 Eb5:1/2 Db5:1/2 F5:2 Bb4:1/2 Bb4:1/2',
    'Bb4:1 Db5:1 Eb5:1 ^Bb4,F5:1 Eb5:1 Db5:1',
    'F5:1 Ab5:1 F5:1/2 Eb5:1/2 Eb5:3',
    '^F5,Bb5:1 Ab5:1 Bb5:1 F5:1 Eb5:1 Db5:1',
    '^Eb5,Bb5:1 Ab5:1 Bb5:1 F5:2 Db5:1',
    '^Gb5,Bb5:1 Ab5:1 Bb5:1 F5:1 Eb5:1 Db5:1',
    '^C5,Ab5:1 Ab5:1 Bb5:1 F5:3',
    'Bb4:1 Db5:1 Eb5:1 F5:1 Eb5:1 Db5:1',
    '^Eb5,Bb5:1 Ab5:1 Bb5:1 F5:2 Bb4:1',
    '^Gb4,Bb4:1 Db5:1 Eb5:1 ^Bb4,F5:1 Eb5:1 Db5:1/2 Bb4:1/2',
    '^Ab4,Db5:3 Ab4,Db5:1 Eb5:1 F5:1',
    'F5:2 Eb5:1 Bb4:3',
    'Eb5:1 F5:1 Eb5:1 Ab5:1 F5:1 Eb5:1',
    'F5:2 Eb5:1/2 Db5:1/2 Db5:2 Db5:1',
    'Eb5:1 F5:1 F5:1 Bb5:1 F5:1 Eb5:1',
    'F5:2 Eb5:1 Bb4:2 Db5:1',
    'Eb5:1 F5:1 Eb5:1 Ab5:1 F5:1 Eb5:1',
    'F5:2 Eb5:1 Db5:2 Eb5:1/2 F5:1/2',
    'F5:2 Eb5:1/2 Db5:1/2 Db5:1 Eb5:1 F5:1',
    '^Bb4,F5:2 Eb5:1 Bb4:2 Db5:1',
    '^Ab4,Eb5:1 F5:1 Eb5:1 Ab5:1 F5:1 Eb5:1',
    '^Bb4,F5:2 Eb5:1/2 Db5:1/2 Ab4,Db5:2 Db5:1',
    '^Ab4,Eb5:1 F5:1 Eb5:1 Eb5,Ab5:1/2 Bb5:1/2 Ab5:1 F5:1',
    '^Bb4,F5:2 Eb5:1 Bb4:2 Db5:1',
    '^Ab4,F5:2 Eb5:1 D4,Bb4:2 F4,Db5:1',
    '^Gb4,Bb4:2 F5:1 Ab4,Eb5:1 Db5:1 C5:1',
    '^Ab4,Db5:3 Ab5:2 Db6:1',
    '^Bb5,F6:2 Eb6:1 Eb6,Ab6:2 Db6:1',
    '^Ab5,F6:2 Eb6:1 Eb6,Ab6:2 Db6:1',
    '^Bb5,F6:2 Eb6:1 Db6,Ab6:2 Eb6,Ab6:1/2 F6:1/2',
    '^C6,F6:2 Eb6:1 Ab5,Eb6:1 F5:1 Eb5:1',
    '^Bb4,Eb5:1/2 F5:1/2 Eb5:1/2 F5:1/2 Eb5:1/2 F5:1/2 Ab5:3',
    '^Ab4,F5:1 Eb5:1 Db5:1 ^D4,F4,Bb4:2 Db5:1',
    '^Db4,Gb4,Bb4:1 Db5:1 F5:1 ^Gb4,Db5,F5:1 Eb5:2',
    'Eb5:1 Eb5:2 Eb6:1 F6:1 Ab6:1',
    '^Bb5,Db6,F6:2 Eb6:1 Bb5:3',
    '^Ab5,C6,Eb6:1 F6:1 Eb6:1 Ab6:1 F6:1 Eb6:1',
    '^Gb5,Bb5,Db6:2 Eb6:1 ^Ab5,C6,Eb6:3',
    '^Ab5,Eb6:1 F6:1 Eb6:1 Ab6:1/2 Bb6:1/2 Ab6:1 F6:1',
    '^Bb5,Db6,F6:2 Eb6:1 Bb5:2 Db6:1',
    '^Ab5,C6,Eb6:2 Eb6:1 ^Bb5,Db6,F6:2 Ab5:1',
    '^Gb5,Bb5,Db6:1 F6:2 Ab5:1 Eb6:1 Db6:1',
    '~Db6:6',
]

G = 'Gb3:1 Db4:1 F4:1 Bb4:1 F4:1 Db4:1'
F = 'F3:1 C4:1 Eb4:1 Ab4:1 Eb4:1 C4:1'
E = 'Eb3:1 Db4:1 Gb4:1 Ab3:1 Eb4:1 Gb4:1'
EU = 'Eb3:1 Db4:1 Gb4:1 Ab3:1 Gb4:1 Ab4:1'
ES = 'Eb3:1 Db4:1 Gb4:1 Bb4:1 Gb4:1 Db4:1'
D = 'Db3:1 C4:1 F4:1 Ab4:1 F4:1 C4:1'
GL = 'Gb2:1 Gb3:1/2 Db4:1/2 F4:1 Bb4:1 F4:1 Db4:1'
FL = 'F2:1 F3:1/2 C4:1/2 Eb4:1 Ab4:1 Eb4:1 C4:1'
EL = 'Eb3:1 Bb3:1/2 Db4:1/2 Gb4:1 Ab3:1 Eb4:1 Gb4:1'
EUL = 'Eb3:1 Bb3:1/2 Db4:1/2 Gb4:1 Ab3:1 Gb4:1 Ab4:1'
ESL = 'Eb3:1 Bb3:1/2 Db4:1/2 Gb4:1 Bb4:1 Gb4:1 Db4:1'
DL = 'Db3:1 Ab3:1/2 C4:1/2 F4:1 Ab4:1 F4:1 C4:1'
GS = 'Gb2:1 Gb3:1/2 Db4:1/2 F4:1 0:1 F4:1 Db4:1'
EC = 'Eb3:1 Bb3:1/2 Db4:1/2 Gb4:1 Ab2:1 Gb3:1 C4:1'

LEFT = [
    'Gb4,Db5:6', 'F4,C5:6', 'Eb4,Bb4:3 C4,Gb4:3', 'Db3:6', G,
    F, E, D, G, F, EU, D, G, F, ES, D, G, F, E,
    'Db3:1 C4:1 F4:1 Ab4:3', G, F, E, 'Db3:1 C4:1 F4:1 0:3',
    GL, FL, EL, DL, GL, FL, EUL, D, GL, FL, ESL, DL, GL, F, EL,
    'Db3:1 C4:1 F4:1 0:1 F4:1 C4:1',
    GS, FL, EC, DL, GS, FL, EC, D, GS, FL, EC, DL, GS,
    'F2:1 F3:1/2 Ab3:1/2 C4:1 Bb2:1 Ab3:1 0:1',
    'Eb3:1 Bb3:1/2 Db4:1/2 Gb4:1 Ab2:1 Gb3:1 Db4:1',
    'Db3:1 C4:1 F4:1 0:3',
    'Gb3:1/2 Db4:1/2 Eb4:1/2 F4:1/2 Eb4:1/2 F4:1/2 Ab4:1 F4:1 Db4:1',
    'F3:1/2 C4:1/2 Eb4:1/2 F4:1/2 Eb4:1/2 F4:1/2 Ab4:1 Eb4:1 Db4:1',
    'Eb3:1 Bb3:1/2 Db4:1/2 F4:1 Ab3:1 Gb4:1 Bb4:1',
    'Db3:1 Ab3:1/2 C4:1/2 Eb4:1/2 F4:1/2 Bb4:1 Ab4:1 F4:1',
    G, 'F3:1 C4:1 Eb4:1 Bb2:3', 'Eb3:3 Ab3:3', '~Ab3:6',
    '^Gb4,Db5,F5:6', '^F4,C5,Eb5:6',
    '^Eb4,Bb4,Db5:3 ^Ab4,Eb5:3', 'Db4:6', '^Gb4,Db5,F5:6',
    '^F4,C5,Eb5:3 Bb4:1 D5:2', '^Eb4,Bb4,Db5:3 Ab3,Gb4:3', '0:6',
]

SYSTEMS = [(1, i+1, 1+i*5, 5+i*5) for i in range(6)] + [
    (2, i+1, 31+i*5, 35+i*5) for i in range(6)] + [(3,1,61,66),(3,2,67,72)]
# Add one dotted-quarter beat at each printed fermata, preserving tied LH notes.
FERMATAS = [(Fraction(63*6), Fraction(3)), (Fraction(63*6+3), Fraction(3))]
EIGHTH_TICKS = 160  # two source 6/8 bars occupy one four-beat arranger grid bar
BPM = 52  # slower lyrical dotted-quarter tempo requested by user; not printed


def warp(units):
    return units + sum(extra for point, extra in FERMATAS if units >= point)


def hand_notes(hand):
    bars = RIGHT if hand == 'right' else LEFT if hand == 'left' else None
    if bars is None or len(bars) != 72:
        raise ValueError('Expected 72 source bars and a valid hand')
    result, active = [], {}
    for bar, notation in enumerate(bars,1):
        local = Fraction(0)
        for token in notation.split():
            symbol, length = token.split(':')
            duration = Fraction(length)
            at = (bar-1)*6+local
            tied, rolled = symbol.startswith('~'), symbol.startswith('^')
            symbol = symbol.lstrip('~^')
            if symbol != '0':
                for voice, name in enumerate(symbol.split(',')):
                    pitch = midi(name)
                    if tied:
                        previous = active.get(pitch)
                        if previous is None or previous['end'] != at:
                            raise ValueError(f'Broken tie at {hand} bar {bar}')
                        previous['end'] += duration
                        previous['source_bars'].append(bar)
                    else:
                        note={'start':at,'end':at+duration,'pitch':pitch,'name':name,
                              'source_bars':[bar],'hand':hand,'roll_offset':voice*8 if rolled else 0}
                        result.append(note);active[pitch]=note
            local += duration
        if local != 6:
            raise ValueError(f'{hand} bar {bar}: {local} eighths, expected 6')
    return result
