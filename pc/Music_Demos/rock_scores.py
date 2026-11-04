from pathlib import Path
import sys


BASE = Path(__file__).resolve().parent.parent / 'drum_bass_pitch_20261013'
sys.path[:0] = [str(BASE / 'violin_r15'), str(BASE / 'host'), str(BASE / 'tools/python_deps')]
from arrangement_model import Automation, BAR, Clip, Note, PPQ, Point, Project, Track


ROCK_PROFILES = [
    {'id': 'g01_iron_highway', 'title': '钢铁公路', 'genre': '失真电吉他主导 / Hard Rock',
     'key': 'E小调', 'bpm': 136, 'bars': 40, 'guitar_lead': True,
     'description': 'JCM800风格失真与箱体，全湿吉他；低弦Riff、强力和弦、主音与独奏段轮流领奏，Bass和鼓伴奏。完全没有钢琴或小提琴。'},
]
FORM = [(0, 4, '引子'), (4, 12, 'Riff主题'), (12, 20, '副歌'), (20, 24, '间奏'),
        (24, 32, '吉他独奏'), (32, 38, '副歌再现'), (38, 40, '尾声')]
ROOTS = {'E5': 40, 'C5': 48, 'G5': 43, 'D5': 50, 'A5': 45, 'B5': 47}
VERSE_CHORDS = ['E5', 'C5', 'G5', 'D5', 'E5', 'C5', 'A5', 'B5']
CHORUS_CHORDS = ['C5', 'G5', 'D5', 'E5', 'C5', 'G5', 'A5', 'B5']
BREAK_CHORDS = ['A5', 'C5', 'E5', 'B5']
HOOK = [
    [76, 79, 76, 74, 72], [74, 71, 67, 69, 71],
    [74, 78, 76, 74, 69], [76, 79, 83, 79, 76],
    [79, 76, 74, 72, 76], [79, 78, 74, 71, 67],
    [81, 79, 76, 72, 69], [75, 78, 81, 78, 71],
]
SOLO = [
    [64, 67, 69, 71, 74, 76], [76, 79, 76, 72, 67, 64],
    [67, 71, 74, 79, 78, 74], [66, 69, 74, 76, 78, 81],
    [83, 79, 76, 74, 71, 67], [72, 76, 79, 76, 74, 72],
    [69, 72, 76, 81, 79, 76], [75, 78, 81, 78, 75, 71],
]


def compose_rock(profile):
    definitions = [('guitar', '电吉他·低弦Riff', 95), ('guitar', '电吉他·强力和弦', 88),
                   ('guitar', '电吉他·主音与独奏', 100), ('bass', 'Bass·跟随根音', 87),
                   ('drums', '鼓·底鼓军鼓', 100), ('drums', '鼓·镲片', 80), ('drums', '鼓·过门', 90)]
    tracks = [Track(instrument, f'{index + 1:02d} {name}', level,
                    id=f'{profile["id"]}-track-{index}')
              for index, (instrument, name, level) in enumerate(definitions)]

    def chord_at(bar):
        first, last, section = next(item for item in FORM if item[0] <= bar < item[1])
        progression = BREAK_CHORDS if section == '间奏' else CHORUS_CHORDS if section in ('副歌', '副歌再现') else VERSE_CHORDS
        return 'E5' if section == '尾声' else progression[(bar - first) % len(progression)]

    def emit(track_index, bar, beat, duration, pitch, velocity, offset=0):
        track = tracks[track_index]
        if not track.clips or track.clips[-1].start != bar * BAR:
            first, last, section = next(item for item in FORM if item[0] <= bar < item[1])
            track.clips.append(Clip(f'{section} · {chord_at(bar)}', bar * BAR, BAR,
                                    id=f'{profile["id"]}-clip-{track_index}-{bar}'))
        clip = track.clips[-1]
        start = round(beat * PPQ) + offset
        clip.notes.append(Note(start, min(round(duration * PPQ), BAR - start), pitch, velocity,
                               id=f'{clip.id}-note-{len(clip.notes)}'))

    def power_chord(bar, beat, root, velocity, duration=.45):
        for voice, interval in enumerate((0, 7, 12)):
            emit(1, bar, beat, duration, root + interval, velocity - voice * 4, voice * 8)

    for bar in range(profile['bars'] - 1):
        first, last, section = next(item for item in FORM if item[0] <= bar < item[1])
        position = bar - first
        root = ROOTS[chord_at(bar)]
        strong = section in ('副歌', '副歌再现')
        solo = section == '吉他独奏'
        if section == '尾声':
            power_chord(bar, .25, 40, 104, 2.75)
            emit(2, bar, .5, 2.5, 76, 100)
            emit(3, bar, 0, 2.75, 28, 91)
            emit(4, bar, 0, .15, 0, 109)
            emit(6, bar, 0, .15, 5, 76)
            continue
        if section == '间奏':
            riff = [(.25, root), (1.75, root + 7), (2.75, root)]
            hits = (3.5,)
        elif strong:
            riff = [(.75, root), (1.25, root + 7), (2.25, root), (2.75, root + 12)]
            hits = (.25, 1.75, 3.25)
        else:
            riff = [(.25, root), (.75, root), (1.5, root + 7),
                    (2.25, root), (2.75, root + 12), (3.5, root + 7)]
            hits = (1.75, 3.75) if section != '引子' or position >= 2 else ()
        for pulse, (beat, pitch) in enumerate(riff):
            emit(0, bar, beat, .23 if pulse % 2 else .34, pitch,
                 (101 if strong else 94 if solo else 97) - pulse % 3 * 7)
        for beat in hits:
            power_chord(bar, beat, root, 105 if strong else 86 if solo else 94, .45 if beat < 3.5 else .2)

        if strong:
            rhythm = [(.5, .625), (1.25, .5), (2, .5), (2.75, .5), (3.5, .375)]
            for pulse, (pitch, (beat, duration)) in enumerate(zip(HOOK[position % 8], rhythm)):
                emit(2, bar, beat, duration, pitch, 108 - pulse % 3 * 4)
        elif solo:
            rhythm = [(.25, .375), (.75, .5), (1.5, .5), (2.25, .375), (2.75, .5), (3.5, .375)]
            for pulse, (pitch, (beat, duration)) in enumerate(zip(SOLO[position % 8], rhythm)):
                emit(2, bar, beat, duration, pitch, 110 - pulse % 3 * 5)
        elif section == 'Riff主题' and position % 2:
            for pulse, interval in enumerate((19, 22, 19)):
                emit(2, bar, 2.5 + pulse * .5, .32, min(83, root + interval), 93 - pulse * 3)

        if section == '引子' and position < 2:
            continue
        bass_root = root - 12
        bass_line = [(0, bass_root), (1.5, bass_root), (2.5, bass_root + 7), (3.5, bass_root)]
        if section == '间奏':
            bass_line = [(0, bass_root), (2.5, bass_root + 7)]
        for beat, pitch in bass_line:
            emit(3, bar, beat, .6, pitch, 96 if beat == 0 else 84)
        kicks = (0, .75, 1.5, 2, 2.75) if strong else (0, 1.5, 2.75) if solo else (0, .75, 2, 2.75)
        if section == '间奏':
            kicks = (0, 2.5)
        for beat in kicks:
            emit(4, bar, beat, .12, 0, 110 if strong else 101)
        for beat in (1, 3):
            emit(4, bar, beat, .12, 1, 111 if strong else 103, 6)
        if section != '间奏':
            emit(4, bar, 2.75, .1, 1, 37, 12)
        for pulse in range(4 if section == '间奏' else 8):
            beat = pulse * (1 if section == '间奏' else .5)
            voice = 6 if solo else 3 if strong and pulse == 7 else 2
            emit(5, bar, beat, .1, voice, 59 if pulse % 2 == 0 else 38, 5 if pulse % 2 else 0)
        if position % 4 == 0 and section != '间奏':
            emit(6, bar, 0, .15, 5, 83 if strong else 68)
        if position % 4 == 3:
            for pulse, voice in enumerate((9, 8, 8, 7)):
                emit(6, bar, 3 + pulse * .25, .12, voice, 72 + pulse * 7)

    project = Project(profile['title'] + ' · 失真电吉他主导', bpm=profile['bpm'], bars=profile['bars'],
                      tracks=tracks, loop_start=0, loop_end=profile['bars'] * BAR)
    project.parameters.update({'bus.guitar': 96, 'bus.bass': 62, 'bus.drums': 61,
        'bus.piano': 0, 'bus.violin': 0, 'guitar.amp': 3, 'guitar.drive': 72,
        'guitar.tone': 48, 'guitar.level': 64, 'guitar.mix': 127, 'guitar.cabinet': 1,
        'guitar.gate': 1, 'guitar.threshold': 18, 'guitar.compressor': 0,
        'guitar.modulation': 0, 'space.chorus_mix': 0,
        'space.delay_mix': 5, 'space.delay_time': 48, 'space.delay_feedback': 16})
    for target in ('bus.guitar', 'bus.bass', 'bus.drums', 'bus.piano', 'bus.violin'):
        points = []
        for first, last, section in FORM:
            amount = {'引子': .88, 'Riff主题': .96, '副歌': 1.05, '间奏': .84,
                      '吉他独奏': 1.03 if target == 'bus.guitar' else .90, '副歌再现': 1.05, '尾声': .94}[section]
            points.append(Point(first * BAR, round(project.parameters[target] * amount)))
        points += [Point((profile['bars'] - 1) * BAR, points[-1].value),
                   Point(profile['bars'] * BAR - PPQ // 2, 0)]
        project.automation.append(Automation(target, 'linear', points))
    project.automation.append(Automation('space.delay_mix', 'step',
        [Point(first * BAR, 8 if section == '吉他独奏' else 5 if section in ('副歌', '副歌再现') else 3)
         for first, last, section in FORM] + [Point((profile['bars'] - 1) * BAR, 0)]))
    return project.validate()
