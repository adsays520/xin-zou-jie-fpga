"""Keep the piano melody, give the main accompaniment to one violin voice."""
from copy import deepcopy

from fuji_arrangement import PROFILE as BASE_PROFILE, compose_fuji, fuji_short, _emit
from fuji_score import hand_notes
from piano_scores import Automation, BAR, PPQ, Point


PROFILE = {**BASE_PROFILE,
    'id': 'p05_fuji_violin', 'title': '富士山下 · 钢琴主旋律与小提琴和声',
    'genre': '用户钢琴谱改编 / 小提琴和声版',
    'description': '钢琴保留原右手旋律与前奏；主段左手缩为轻低音，由单声部小提琴长音承接和声，吉他仅少量点缀。无鼓、无独立Bass。',
    'mix_note': '已载入小提琴和声版：钢琴仍唱主旋律，小提琴承担主要伴奏；吉他退到轻点缀。未自动连接或播放。',
}


def _violin_register(pitch, previous):
    candidates = [value for value in range(60, 75) if value % 12 == pitch % 12]
    return min(candidates, key=lambda value: (abs(value - previous), value))


def compose_fuji_violin():
    project = deepcopy(compose_fuji())
    project.name = PROFILE['title']
    right, left_track, guitar, violin = project.tracks
    left_track.name = '02 钢琴·前奏原左手／主段轻低音'
    # Retain the original two-handed intro, then make room for the bow line.
    left_track.clips = [clip for clip in left_track.clips if clip.start < 9 * BAR]
    left_track.level = 76
    guitar.name, guitar.level = '03 干净吉他·偶尔点缀', 66
    guitar.clips = [clip for clip in guitar.clips if (clip.start // BAR - 9) % 2 == 0]
    for clip in guitar.clips:
        clip.notes = clip.notes[:1]
    violin.name, violin.level = '04 小提琴·主要和声线（单声部）', 84
    violin.clips = []
    source = hand_notes('left')
    bows = []
    previous_pitch = 69
    for bar in range(9, 45):
        notes = [note for note in source if note['start'] < (bar + 1) * 16 and note['end'] > bar * 16]
        root = min(note['pitch'] for note in notes)
        while root > 48:
            root -= 12
        while root < 36:
            root += 12
        _emit(project.tracks, 1, bar * BAR, round(1.25 * PPQ), root, 55,
              '钢琴·轻根音（和声交给小提琴）')
        first_half = [note for note in notes if note['start'] < bar * 16 + 8]
        first = max(first_half or notes, key=lambda note: (note['end'] - note['start'], note['pitch']))
        second_half = [note for note in notes if bar * 16 + 8 <= note['start'] < (bar + 1) * 16]
        second = second_half[min(2, len(second_half) - 1)] if second_half else notes[-1]
        for beat, note in ((0, first), (2, second)):
            pitch = _violin_register(note['pitch'], previous_pitch)
            start, end = bar * BAR + beat * PPQ, bar * BAR + (beat + 2) * PPQ
            if bows and bows[-1]['pitch'] == pitch and bows[-1]['end'] == start:
                bows[-1]['end'] = end
            else:
                bows.append({'start': start, 'end': end, 'pitch': pitch,
                             'velocity': 58 if bar >= 26 else 54})
            previous_pitch = pitch
    for bow in bows:
        _emit(project.tracks, 3, bow['start'], bow['end'] - bow['start'], bow['pitch'], bow['velocity'],
              '小提琴·顺接和声长音')

    # The violin is now an audible accompanist, below the piano melody.
    project.parameters.update({'bus.guitar': 0, 'bus.violin': 0})
    changes = {'bus.piano': [(0, 50), (9, 52), (26, 54), (41, 51), (44, 48)],
               'bus.guitar': [(0, 0), (9, 10), (26, 12), (41, 10), (44, 0)],
               'bus.violin': [(0, 0), (9, 22), (26, 28), (41, 24), (44, 22)],
               'bus.bass': [(0, 0)], 'bus.drums': [(0, 0)]}
    project.automation = []
    for target, values in changes.items():
        points = []
        previous = None
        for bar, value in values:
            if previous is not None:
                points.append(Point(bar * BAR - PPQ // 8, previous))
            points.append(Point(bar * BAR, value))
            previous = value
        points.extend((Point(46 * BAR, previous), Point(47 * BAR - PPQ // 2, 0)))
        project.automation.append(Automation(target, 'linear', points))
    return project.validate()


def fuji_violin_short(project):
    result = fuji_short(project)
    result.name = '富士山下 · 小提琴和声16秒试听'
    # Keep one quiet bass tone and let the violin resolve the final harmony.
    ending = next(clip for clip in result.tracks[1].clips if clip.start == 6 * BAR)
    ending.notes = [min(ending.notes, key=lambda note: note.pitch)]
    result.tracks[3].clips[-1].notes[-1].velocity = 52
    return result.validate()
