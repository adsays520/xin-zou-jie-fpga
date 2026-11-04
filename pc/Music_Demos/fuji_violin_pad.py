"""Piano-led 富士山下 with a soft, melodic, connected violin background."""
from copy import deepcopy

from fuji_arrangement import PROFILE as BASE_PROFILE, compose_fuji, fuji_short, _emit
from fuji_score import hand_notes, midi
from fuji_violin_score import phrase_notes
from piano_scores import Automation, BAR, PPQ, Point

PROFILE = {**BASE_PROFILE,
    'id': 'p06_fuji_pad', 'title': '富士山下 · 钢琴主奏与提琴旋律衬底',
    'genre': '钢琴抒情 / 轻提琴连弓伴行',
    'gain_policy': 'piano-led-continuous-bow',
    'description': '钢琴双手主奏；提琴第二小节轻入，有旋律起伏与收句，用连弓保持连续。主段采用用户提琴谱中与钢琴对齐的乐句，其余按钢琴旋律衬托。',
    'mix_note': '已载入提琴旋律衬底版：钢琴主奏，提琴低音量连弓伴行，有曲调且不反复起停。未自动连接或播放。',
    'attribution': '根据用户钢琴PDF及提琴PNG选段工作转谱再编配；前奏为钢琴动机下移，提琴辅助线按乐句对齐，不是原唱弦乐分轨复刻。',
}

# Intro: lower the recognizable piano motif; simplify only the fast arpeggios.
INTRO = {
    2: 'E5:8 F5:2 E5:2 D5:2 C5:2',
    3: 'D5:2 C5:2 A4:2 G4:2 A4:2 G4:2 F4:2 E4:2',
    4: 'F4:2 E4:2 D4:2 C4:2 D4:4 E4:2 F4:2',
    5: 'G4:4 A4:2 D5:2 C5:8',
    6: 'A4:2 C5:2 G4:2 F4:2 D5:4 A4:4',
    7: 'F5:4 D5:4 C5:4 A4:4',
    8: 'E5:4 C5:4 Bb4:4 F4:4',
    9: 'G4:4 E4:4 F4:8',
}
# first/last violin printed bars, excerpt sixteenth window, target piano bar/beat.
# Pitch stays in unison with the matching piano phrase: this is a soft melodic
# doubling, not a separately invented contrapuntal harmony that could clash.
SCORE_WINDOWS = [
    (9, 13, 6, 80, 10, 3.5),
    (16, 16, 0, 16, 17, 2),
    (20, 20, 0, 8, 21, 2),
    (24, 24, 0, 16, 25, 2),
    (30, 30, 0, 16, 31, 2),
    (31, 31, 0, 8, 32, 2),
    (34, 34, 0, 16, 35, 2),
    (35, 35, 10, 16, 37, .5),
    (57, 57, 0, 8, 38, 2),
    (38, 38, 0, 8, 39, 2),
    (41, 41, 8, 16, 43, 0),
    (62, 63, 0, 32, 43, 2),
]
PAD_END = 45 * BAR + 3 * PPQ


def pad_notes():
    """Continuous, merge-repeated-note line; preserve melodic motion and cadence."""
    events = []
    for bar, notation in INTRO.items():
        position = 0
        for token in notation.split():
            name, units = token.split(':')
            events.append(((bar - 1) * BAR + position * PPQ // 4, midi(name)))
            position += int(units)
        assert position == 16
    # Supplement the two independent score layouts with the existing piano line.
    # Hold through its short written breaths; the first actual pickup starts C4.
    for note in hand_notes('right'):
        tick = round(note['start'] * PPQ / 4)
        if tick >= 9 * BAR:
            events.append((tick, note['pitch'] - (12 if tick < 9 * BAR + 2 * PPQ else 0)))
    for first, last, begin, end, bar, beat in SCORE_WINDOWS:
        onset = (bar - 1) * BAR + round(beat * PPQ)
        stop = onset + round((end - begin) * PPQ / 4)
        events = [(tick, pitch) for tick, pitch in events if not onset <= tick < stop]
        for note in phrase_notes(first, last):
            a, b = max(begin, note['start']), min(end, note['end'])
            if a < b:
                events.append((onset + round((a - begin) * PPQ / 4), note['pitch']))
    events.sort()
    anchors = []
    for tick, pitch in events:
        if anchors and anchors[-1][1] == pitch:
            continue
        anchors.append((tick, pitch))
    return [(start, anchors[index + 1][0] if index + 1 < len(anchors) else PAD_END, pitch)
            for index, (start, pitch) in enumerate(anchors)]


def compose_fuji_pad():
    project = deepcopy(compose_fuji())
    project.name, project.violin_legato = PROFILE['title'], True
    project.tracks[1].name, project.tracks[1].level = '02 钢琴左手·保留原谱分解', 84
    project.tracks[2].name, project.tracks[2].clips = '03 吉他·空轨可选', []
    violin = project.tracks[3]
    violin.name, violin.level, violin.clips = '04 提琴·轻声旋律伴行（连弓）', 60, []
    for start, end, pitch in pad_notes():
        _emit(project.tracks, 3, start, end - start, pitch, 42, '提琴·弱奏连弓旋律衬底')
    project.parameters.update({'bus.piano': 50, 'bus.violin': 0, 'bus.guitar': 0,
                               'bus.bass': 0, 'bus.drums': 0})
    # Smooth entrance, restrained chorus lift and one long final fade. No pumping
    # automation or short phrase gates. Values are controls, not measured dB.
    project.automation = [
        lane for lane in project.automation if lane.target == 'bus.piano']
    project.automation.append(Automation('bus.violin', 'linear', [
        Point(0, 0), Point(BAR, 0), Point(BAR + 2 * PPQ, 9),
        Point(9 * BAR, 10), Point(25 * BAR, 10), Point(27 * BAR, 14),
        Point(39 * BAR, 14), Point(41 * BAR, 11), Point(44 * BAR, 9),
        Point(PAD_END, 0), Point(project.length, 0)]))
    for target in ('bus.guitar', 'bus.bass', 'bus.drums'):
        project.automation.append(Automation(target, 'step', [Point(0, 0)]))
    return project.validate()


def fuji_pad_short(project):
    result = fuji_short(project)
    result.name = '富士山下 · 提琴旋律衬底16秒试听'
    # The generic excerpt selects only new attacks; here we chase the ongoing pad
    # at the excerpt boundary so it cannot start with an unintended silence.
    start, end = 27 * BAR, 33 * BAR
    result.tracks[2].clips = []
    result.tracks[3].clips = []
    for first, last, pitch in pad_notes():
        a, b = max(first, start), min(last, end)
        if a < b:
            _emit(result.tracks, 3, a - start, b - a, pitch, 42, '短版·连续提琴（追赶段首长音）')
    _emit(result.tracks, 3, 6 * BAR, 3 * PPQ, 65, 42, '短版·提琴F音连弓收束')
    lane = next(lane for lane in result.automation if lane.target == 'bus.violin')
    lane.points = [Point(0, 0), Point(PPQ, 14), Point(6 * BAR, 14),
                   Point(6 * BAR + 3 * PPQ, 0), Point(result.length, 0)]
    result.parameters['bus.violin'] = 0
    return result.validate()
