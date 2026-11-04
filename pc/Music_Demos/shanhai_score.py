"""Manual melody/chord working transcription of the three USER supplied pages.

Durations below are sixteenth-note units (16 per 4/4 bar).  h/l denote
octaves above/below 1=E4; ~ joins a same-pitch continuation.  Some beamed
syllables are rhythmically regularized for this instrumental arrangement.
This is an editable working transcription, not a certified critical edition.
"""
from fractions import Fraction


SHEET_ROWS = ((1, 1, 1, 5), (1, 2, 6, 10), (1, 3, 11, 15),
              (1, 4, 16, 20), (1, 5, 21, 24),
              (2, 1, 25, 29), (2, 2, 30, 34), (2, 3, 35, 38),
              (2, 4, 39, 42), (2, 5, 43, 46), (2, 6, 47, 51),
              (3, 1, 52, 55), (3, 2, 56, 59), (3, 3, 60, 64),
              (3, 4, 65, 69), (3, 5, 70, 70))

# Printed C-fingering chord names. Actual playback includes capo +4:
# F/C -> A/E, F -> A, G -> B, Am -> C#m.
CHORDS = (
    'F/C+G Am F/C+G Am F '
    'G Am Am F G '
    'Am Am F G Am '
    'Am F G Am Am '
    'F G Am Am '
    'F G Am Am F '
    'G Am Am F G '
    'Am Am F G '
    'Am Am F G '
    'Am Am F G '
    'Am Am F G G '
    'F G Am Am '
    'F G Am Am '
    'F G Am Am F '
    'G Am Am F G '
    'Am'
).split()

ENTRY = '0:4 0:2 l5:2 ~l5:2 3:2 ~3:2 2:2'
REFRAIN = '0:4 3:2 2:1 ~2:1 ~2:2 3:2 2:2 ~2:2'
MELODY = [
    # Page 1, printed rows 1..5, bars 1..24.
    '0:16', '0:16', '0:16', '0:16', ENTRY,
    '~2:4 0:2 l5:2 l5:2 3:1 2:1 ~2:2 l5:2',
    '3:8 0:4 0:4', '0:16', ENTRY,
    '~2:4 0:2 l5:2 l5:4 l7:2 2:2',
    '1:2 ~1:2 1:2 l6:2 ~l6:4 0:4', '0:16', ENTRY,
    '~2:4 5:4 5:2 ~5:2 5:2 3:2', '~3:4 0:12',
    '0:12 3:2 2:2', '3:4 2:4 3:2 l5:2 ~l5:4',
    '0:8 2:2 ~2:2 1:2 l7:2', 'l6:4 0:12', '0:16',
    REFRAIN, '~2:2 3:2 0:2 3:2 l6:4 l5:2 2:2',
    '3:8 0:4 2:2 3:2', 'l6:2 3:2 ~3:2 l5:2 0:2 3:2 1:2 2:2',
    # Page 2, bars 25..51.
    REFRAIN, '~2:2 3:2 0:2 3:2 l6:4 3:2 l6:2',
    '~l6:2 1:2 ~1:4 0:4 2:2 3:2',
    'l6:2 3:2 3:2 3:2 0:2 l6:2 l6:2 1:2',
    '~1:2 l6:2 0:4 0:4 0:4',
    '0:16', '0:16', '0:16', '0:16', '0:16', '0:16', '0:16', ENTRY,
    '0:2 2:2 ~2:2 1:2 2:2 3:2 3:2 ~3:2',
    '~3:4 0:4 0:4 0:3 2:1',
    '3:2 2:2 3:2 2:2 ~2:2 3:2 3:2 2:1 3:1',
    '1:4 0:2 5:2 ~5:2 3:2 ~3:2 2:2',
    '2:2 1:2 l7:4 0:4 5:2 3:2',
    '3:8 0:4 0:3 2:1', '3:2 2:2 2:2 2:2 0:4 3:2 2:2',
    '1:4 0:12', '0:16', '0:12 0:3 5:1',
    'h3:2 h2:2 h2:2 ~h2:2 h2:4 h5:2 h3:2',
    '~h3:16', 'h2:16', '0:16',
    # Page 3, bars 52..70; bare 6/7 are NOT upper-octave notes.
    '0:4 h3:2 h2:2 h2:4 h3:2 h2:2',
    '~h2:3 h3:1 ~h3:2 h3:2 6:4 h5:4',
    'h2:2 h3:2 ~h3:8 h2:2 h3:2',
    '6:2 h3:2 h3:2 h5:2 ~h5:2 h3:2 h1:2 h2:2',
    '0:4 h3:2 h2:1 ~h2:1 ~h2:2 h3:2 h2:1 ~h2:1 ~h2:2',
    '~h2:1 h3:1 0:2 h3:2 6:6 h3:1 ~h3:1 6:2',
    '~6:2 h1:2 ~h1:8 h2:2 h3:2',
    '6:2 h3:2 h3:2 ~h3:2 h3:2 5:2 4:2 h1:2',
    '7:2 6:2 ~6:8 h3:4', 'h2:12 h5:4',
    'h3:16', '~h3:16',
    '0:16', '0:16', '0:16', '0:16', '0:16',
    '0:4 0:2 h3:2 6:4 h3:3 6:1',
    '~6:2 h1:2 ~h1:4 0:4 0:4',
]


def degree_pitch(symbol):
    octave = -1 if symbol.startswith('l') else 1 if symbol.startswith('h') else 0
    degree = int(symbol[-1])
    if degree not in range(1, 8):
        raise ValueError('Invalid degree: ' + symbol)
    return 64 + (0, 2, 4, 5, 7, 9, 11)[degree - 1] + octave * 12


def source_location(bar):
    page, row, _, _ = next(item for item in SHEET_ROWS if item[2] <= bar <= item[3])
    return page, row


def melody_notes():
    """Absolute sixteenth units, with explicitly marked ties merged."""
    assert len(CHORDS) == len(MELODY) == 70
    notes = []
    for bar, notation in enumerate(MELODY, 1):
        position = 0
        for token in notation.split():
            symbol, duration_text = token.split(':')
            duration = Fraction(duration_text)
            tied = symbol.startswith('~')
            symbol = symbol.lstrip('~')
            absolute = (bar - 1) * 16 + position
            if symbol != '0':
                pitch = degree_pitch(symbol)
                if tied:
                    if not notes or notes[-1]['pitch'] != pitch or notes[-1]['end'] != absolute:
                        raise ValueError(f'Broken tie at bar {bar}: {token}')
                    notes[-1]['end'] += duration
                    notes[-1]['source_bars'].append(bar)
                else:
                    notes.append({'start': absolute, 'end': absolute + duration, 'pitch': pitch,
                                  'degree': symbol, 'source_bars': [bar]})
            position += duration
        if position != 16:
            raise ValueError(f'Bar {bar} contains {position}/16 instead of 16/16')
    return notes
