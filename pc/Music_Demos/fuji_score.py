"""Editable working transcription of the two-page piano PDF supplied by user.

F major (one flat), 4/4, quarter=120. Durations use sixteenth units;
~ denotes a tied continuation, 0 a rest, and comma-separated pitches a chord.
This working transcription regularizes a few ambiguous/rest-spaced figures.
"""
from fractions import Fraction
import re


SYSTEMS = ((1, 1, 1, 4), (1, 2, 5, 7), (1, 3, 8, 11),
           (1, 4, 12, 15), (1, 5, 16, 19), (1, 6, 20, 23),
           (2, 1, 24, 27), (2, 2, 28, 31), (2, 3, 32, 35),
           (2, 4, 36, 39), (2, 5, 40, 43), (2, 6, 44, 45))

RIGHT = [
    'F5:8 F6:8',
    'E6:8 A5,D6,F6:2 E6:2 D6:2 C6:2',
    'D6:2 C6:2 A5:2 G5:2 A5:2 G5:2 F5:2 E5:2',
    'F5:2 E5:2 D5:2 C5:2 D5:4 E5:2 F5:2',
    'G5:4 A5:2 D6:2 C6:8',
    'A5:2 C6:2 C5,E5,G5:2 F5:2 A6:1 F6:1 D6:1 A5:1 A6:1 F6:1 D6:1 A5:1',
    'A6:1 F6:1 D6:1 A5:1 A6:1 F6:1 D6:1 A5:1 G6:1 E6:1 C6:1 A5:1 G6:1 E6:1 C6:1 A5:1',
    'G6:1 E6:1 C6:1 A5:1 G6:1 E6:1 C6:1 A5:1 F6:1 D6:1 Bb5:1 F5:1 D6:1 Bb5:1 F5:1 D5:1',
    'C6:1 G5:1 E5:1 C5:1 G5:1 E5:1 C5:2 F5:8',
    '~F5:8 0:4 0:2 C4:2',
    'D4:2 F4:2 G4:2 F4:2 G4:2 A4:4 A4:2',
    '~A4:2 A4:2 G4:2 F4:2 G4:2 A4:4 A4:2',
    '~A4:2 A4:2 G4:2 F4:2 G4:3 F4:1 ~F4:2 D4:2',
    'F4:3 G4:1 ~G4:2 A4:2 A4:6 C4:2',
    'D4:2 F4:2 G4:2 F4:2 G4:2 F4:4 D5:2',
    '~D5:2 C5:2 A4:2 G4:2 G4:2 F4:4 A4:2',
    '~A4:2 A4:2 G4:2 F4:2 G4:3 G4:1 ~G4:2 G4:2',
    'G4:3 F4:1 ~F4:2 D4:2 G4:4 C4:4',
    'D4:2 F4:2 G4:2 F4:2 G4:2 A4:4 C5:2',
    '~C5:2 A4:2 G4:2 F4:2 G4:2 A4:4 D5:2',
    '~D5:2 A4:2 G4:2 F4:2 G4:3 F4:1 ~F4:2 D4:2',
    'F4:3 G4:1 ~G4:2 A4:2 C5:6 C4:2',
    'D4:2 F4:2 G4:2 F4:2 G4:2 F4:4 D5:2',
    '~D5:2 C5:2 A4:2 G4:2 G4:2 F4:4 A4:2',
    '~A4:2 A4:2 G4:2 F4:2 G4:3 G4:1 ~G4:2 G4:2',
    'G4:3 F4:1 ~F4:2 D4:2 F4:6 F4:2',
    'F5:2 E5:2 E5:2 D5:2 E5:2 D5:4 C5:2',
    'D5:2 C5:2 A4:2 G4:2 A4:2 C5:2 D5:2 C5:2',
    '~C5:2 C5:2 D5:2 C5:2 D5:3 D5:1 ~D5:2 D5:2',
    'D5:3 C5:1 ~C5:2 D5:2 C5:2 A4:4 A4:2',
    '~A4:2 F4:2 G4:2 A4:2 C5:2 A4:2 G4:2 F4:2',
    '~F4:2 F4:2 G4:2 A4:2 D5:2 A4:2 G4:2 F4:2',
    '~F4:2 F4:2 F4:2 F4:2 F5:3 F5:3 F5:2',
    'F5:3 D5:1 ~D5:2 F5:2 D5:6 C5:2',
    '~C5:4 F5:2 E5:2 F5:2 E5:2 D5:2 C5:2',
    'D5:2 C5:2 A4:2 G4:2 A4:2 C5:2 D5:2 C5:2',
    '~C5:2 C5:2 D5:2 C5:2 D5:3 D5:3 D5:2',
    'D5:3 C5:1 ~C5:2 D5:2 C5:2 A4:6',
    '~A4:2 F4:2 G4:2 A4:2 C5:2 A4:2 G4:2 F4:2',
    '~F4:2 F4:2 G4:2 A4:2 D5:2 A4:2 G4:2 F4:2',
    'F5:16',
    '~F5:2 F5:2 D5:2 F5:2 D5:2 C5:4 C5:2',
    'D5:2 C5:2 A4:2 G4:2 A4:2 G4:4 F4:2',
    'D4:2 ~D4:1 F4:1 ~F4:2 G4:2 F4:8',
    '~F4:8 0:8',
]

LEFT = [
    '0:16',
    '0:8 D3:2 A3:2 D4:2 F4:2',
    'A4:2 F4:2 D4:2 A3:2 A2:2 E3:2 A3:2 C4:2',
    'E4:2 C4:2 A3:2 E3:2 Bb2:2 F3:2 D4:4',
    'C3:2 G3:2 E4:4 F3:2 C4:2 F4:2 G4:2',
    'A4:4 E4:4 D3:2 A3:2 D4:2 E4:2',
    'F4:2 E4:2 D4:2 A3:2 A2:2 E3:2 A3:2 C4:2',
    'E4:2 C4:2 A3:2 E3:2 Bb2:2 F3:2 D4:2 F4:2',
    'C3:2 G3:2 E4:4 F3:2 C4:2 F4:2 G4:2',
    'A4:8 F2:2 C3:2 F3:2 G3:2',
    'A3:8 F2:2 C3:2 F3:2 G3:2',
    'A3:8 E2:2 C3:2 E3:2 G3:2',
    'C4:8 D2:2 A2:2 D3:2 E3:2',
    'F3:8 C2:2 A2:2 C3:2 E3:2',
    'A3:8 Bb2:2 F3:2 Bb3:2 C4:2',
    'D4:8 A2:2 F3:2 A3:2 C4:2',
    'F4:8 G2:3 D3:3 G3:2',
    'D3:3 Bb3:1 ~Bb3:2 0:2 C3:2 G3:2 Bb3:2 Bb3:2',
    '~Bb3:6 D3:2 F2:2 C3:2 F3:2 G3:2',
    'A3:8 E2:2 C3:2 E3:2 G3:2',
    '0:4 C4:4 D2:2 0:2 0:4',
    '0:8 C2:2 A2:2 C3:2 E3:2',
    'A3:2 ~A3:6 Bb2:2 F3:2 Bb3:2 C4:2',
    'D4:8 A2:2 F3:2 A3:2 C4:2',
    'F4:8 G2:2 D3:2 B3:4',
    'C3:2 G3:2 Bb3:4 F2:2 C3:2 F3:2 G3:2',
    'A3:8 D2:2 A2:2 D3:2 F3:2',
    'A3:8 A2:2 E3:2 G3:2 C4:2',
    'E4:8 Bb2:2 F3:2 D4:4',
    'C3:2 G3:2 E4:4 F2:2 C3:2 F3:2 G3:2',
    'A3:2 A3:6 D2:2 A2:2 D3:2 E3:2',
    'F3:2 ~F3:6 G2:2 D3:2 G3:2 A3:2',
    'Bb3:4 ~Bb3:4 B2:2 G3:2 B3:2 D4:2',
    'F4:8 C3:2 G3:2 C4:2 D4:2',
    'E4:2 F4:6 D2:2 A2:2 D3:2 F3:2',
    'A3:4 ~A3:4 A2:2 E3:2 G3:2 C4:2',
    'E4:8 Bb2:2 F3:2 D4:4',
    'C3:2 G3:2 E4:4 F2:2 C3:2 G3:2 A3:2',
    'C4:4 E3:4 D2:2 A2:2 D3:2 E3:2',
    'F3:4 A3:4 G2:2 D3:2 A3:2 Bb3:2',
    'B2:16',
    '~B2:8 Bb2:2 F3:2 C4:2 D4:2',
    '~D4:8 C3:2 G3:2 Bb3:4',
    '~Bb3:8 F2:2 C3:2 F3:2 Bb3:2',
    'C4:4 G3:4 F3,A3:8',
]


def midi(name):
    match = re.fullmatch(r'([A-G])([b#]?)(-?\d+)', name)
    if not match:
        raise ValueError('Invalid pitch: ' + name)
    letter, accidental, octave = match.groups()
    return (int(octave) + 1) * 12 + {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[letter] + {'': 0, 'b': -1, '#': 1}[accidental]


def hand_notes(hand):
    bars = RIGHT if hand == 'right' else LEFT if hand == 'left' else None
    if bars is None:
        raise ValueError('Hand must be right or left')
    assert len(bars) == 45
    notes = []
    active_ties = {}
    for bar, notation in enumerate(bars, 1):
        position = Fraction(0)
        for token in notation.split():
            symbol, length = token.split(':')
            duration = Fraction(length)
            start = (bar - 1) * 16 + position
            continuation = symbol.startswith('~')
            symbol = symbol.lstrip('~')
            if symbol != '0':
                for name in symbol.split(','):
                    pitch = midi(name)
                    previous = active_ties.get(pitch)
                    if continuation:
                        if previous is None or previous['end'] != start:
                            raise ValueError(f'Broken {hand} tie at bar {bar}: {token}')
                        previous['end'] += duration
                        previous['source_bars'].append(bar)
                    else:
                        note = {'start': start, 'end': start + duration, 'pitch': pitch,
                                'name': name, 'source_bars': [bar], 'hand': hand}
                        notes.append(note)
                        active_ties[pitch] = note
            position += duration
        if position != 16:
            raise ValueError(f'{hand} bar {bar}: {position}/16 instead of 16/16')
    return notes
