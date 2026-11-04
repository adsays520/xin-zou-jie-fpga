import re
from dataclasses import dataclass


TICKS_PER_BEAT = 24
TICKS_PER_BAR = 96
DEGREE_SEMITONES = (0, 2, 4, 5, 7, 9, 11)


@dataclass(frozen=True)
class ScoreNote:
    token: str
    ticks: int

    @property
    def pitch(self):
        if self.token == '0':
            return None
        match = re.fullmatch(r"([#b]?)([1-7])('*)", self.token)
        if not match:
            raise ValueError(f'无效简谱音符：{self.token}')
        accidental = {'': 0, '#': 1, 'b': -1}[match[1]]
        return 60 + DEGREE_SEMITONES[int(match[2]) - 1] + 12 * len(match[3]) + accidental


def beat(tokens, *durations):
    notes = tokens.split()
    if len(notes) != len(durations) or sum(durations) != TICKS_PER_BEAT:
        raise ValueError('每组必须正好一拍，音符与时值一一对应')
    if any(type(duration) is not int or duration <= 0 for duration in durations):
        raise ValueError('时值必须为正整数')
    result = tuple(ScoreNote(token, duration) for token, duration in zip(notes, durations))
    for note in result:
        note.pitch
    return result


def measure(*beats):
    if len(beats) != 4:
        raise ValueError('每小节必须四拍')
    return tuple(note for group in beats for note in group)


INTRO = measure(beat("3' 3' 3'", 6, 12, 6), beat("0 1' 3'", 6, 6, 12),
                beat("5' 0", 12, 12), beat('5 0', 12, 12))
VERSE = measure(beat("1' 0 5", 12, 6, 6), beat('0 3', 12, 12),
                beat('0 6 7', 6, 12, 6), beat('0 b7 6', 6, 6, 12))
VERSE_SHORT_END = measure(beat("1' 0 5", 12, 6, 6), beat('0 3', 12, 12),
                          beat('0 6 7', 6, 12, 6), beat('0 b7 6 0', 6, 6, 6, 6))
ANSWER = measure(beat("5 3' 5'", 8, 8, 8), beat("6' 4' 5'", 12, 6, 6),
                 beat("0 3' 1'", 6, 12, 6), beat("2' 7 0", 6, 12, 6))
CHROMATIC = measure(beat("0 5' #4'", 12, 6, 6), beat("4' b3' 3'", 6, 12, 6),
                    beat("0 #5 6 1'", 6, 6, 6, 6), beat("0 6 1' 2'", 6, 6, 6, 6))
CHROMATIC_END = measure(beat("0 5' #4'", 12, 6, 6), beat("4' b3' 3'", 6, 12, 6),
                        beat("0 1' 1'", 6, 12, 6), beat("1' 0", 12, 12))
BREAK = measure(beat("0 5'", 12, 12), beat("0 4' 0", 6, 12, 6),
                beat("3' 0", 12, 12), beat('0', 24))
BRIDGE = measure(beat("1' 1' 1'", 6, 12, 6), beat("0 1' 2'", 6, 6, 12),
                 beat("3' 1' 6", 6, 12, 6), beat('5 0', 12, 12))
BRIDGE_END = measure(beat("1' 1' 1'", 6, 12, 6), beat("0 1' 2' 3'", 6, 6, 6, 6),
                     beat('0', 24), beat('0', 24))
REFRAIN = measure(beat("3' 1' 5", 6, 12, 6), beat('0 #5', 12, 12),
                  beat("6 4' 4'", 6, 12, 6), beat('6 0', 12, 12))
TRIPLETS = measure(beat("7 6' 6'", 8, 8, 8), beat("6' 5' 4'", 8, 8, 8),
                   beat("3' 1' 6", 6, 12, 6), beat('5 0', 12, 12))
CADENCE = measure(beat("7 4' 4'", 6, 12, 6), beat("4' 3' 2'", 8, 8, 8),
                  beat("1' 0", 12, 12), beat('0', 24))

MEASURES = (
    INTRO, VERSE, ANSWER, VERSE, ANSWER,
    CHROMATIC, CHROMATIC, CHROMATIC_END, CHROMATIC,
    BREAK, BRIDGE, BRIDGE_END, BRIDGE, INTRO, VERSE_SHORT_END,
    ANSWER, VERSE, ANSWER, REFRAIN, TRIPLETS, REFRAIN, CADENCE,
    REFRAIN, TRIPLETS, REFRAIN, CADENCE, BRIDGE, BRIDGE_END,
    BRIDGE, INTRO, REFRAIN, TRIPLETS, REFRAIN, CADENCE,
)


def bar_order(start_bar=1, score_repeat=True):
    if type(start_bar) is not int or not 1 <= start_bar <= len(MEASURES):
        raise ValueError('起始小节必须为1～34')
    return tuple(range(start_bar, 35)) + (tuple(range(23, 35)) if score_repeat else ())


def numbered_measure(notes):
    groups = []
    current = []
    position = 0
    for note in notes:
        current.append(note.token.replace("'", '̇'))
        position += note.ticks
        if position % TICKS_PER_BEAT == 0:
            groups.append(' '.join(current))
            current = []
    return '  /  '.join(groups)
