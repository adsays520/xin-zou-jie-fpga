from pathlib import Path
import re
import sys


BASE = Path(__file__).resolve().parent.parent / 'drum_bass_pitch_20261013'
sys.path[:0] = [str(BASE / 'violin_r15'), str(BASE / 'host'), str(BASE / 'tools/python_deps')]
from arrangement_model import Automation, BAR, Clip, Note, PPQ, Point, Project, Track


FORM = [(0, 4, '前奏'), (4, 12, '主题A'), (12, 20, '主题B'),
        (20, 24, '留白'), (24, 30, '再现'), (30, 32, '尾声')]
CHORDS = {
    'Cmaj9': (36, [55, 59, 62, 64], [48, 55, 59, 62, 64]),
    'Am9': (33, [55, 59, 60, 64], [45, 52, 55, 59, 60]),
    'Dm9': (38, [57, 60, 64, 65], [50, 57, 60, 64, 65]),
    'G13': (31, [53, 57, 59, 64], [43, 50, 53, 57, 59]),
    'Fmaj7': (29, [57, 60, 64, 65], [41, 48, 57, 60, 64]),
    'Em7': (28, [55, 59, 62, 67], [40, 47, 55, 59, 62]),
    'A7': (33, [55, 61, 64, 69], [45, 52, 55, 61, 64]),
    'E7': (28, [56, 59, 62, 64], [40, 47, 56, 59, 62]),
    'Bbmaj7': (34, [57, 62, 65, 70], [46, 53, 57, 62, 65]),
    'Gm9': (31, [57, 58, 62, 65], [43, 50, 57, 58, 62]),
    'Fmaj9': (29, [57, 60, 64, 67], [45, 53, 57, 60, 67]),
    'Cadd9': (36, [55, 60, 62, 64], [48, 55, 60, 62, 64]),
}
PIANO_PROFILES = [
    {'id': 'p01_window_letter', 'title': '窗边慢信', 'genre': '钢琴独奏 / 抒情', 'key': 'C大调',
     'bpm': 88, 'bars': 32, 'piano_lead': True, 'style': 'solo', 'tonic': 'Cmaj9', 'tonic_midi': 72,
     'harmony': ['Cmaj9', 'Am9', 'Fmaj7', 'G13', 'Em7', 'Am9', 'Dm9', 'G13'],
     'bridge': ['Fmaj7', 'Em7', 'Dm9', 'G13'],
     'theme': 'E5 G5 C6 B5 G5|A5 G5 E5 C5 E5|A5 C6 A5 G5 F5|G5 A5 B5 D6 B5|G5 B5 D6 B5 G5|C6 B5 A5 E5 G5|F5 A5 C6 A5 F5|B5 A5 G5 D5 E5',
     'answer': 'G5 C6 E6 D6 C6|E6 D6 C6 A5 G5|C6 E6 F6 E6 C6|D6 C6 B5 A5 G5|B5 D6 G6 F6 D6|E6 C6 A5 G5 E5|A5 C6 F6 E6 D6|D6 B5 G5 E5 D5',
     'rhythm': [(0, .875), (1, .625), (1.75, .625), (2.5, .625), (3.25, .625)],
     'description': '真正的纯钢琴：右手主旋律、左手低音与中声部分解，带力度层次和乐句呼吸。没有小提琴，也没有鼓或吉他。'},
    {'id': 'p02_blue_platform', 'title': '蓝色站台', 'genre': '钢琴主导 / 爵士律动', 'key': 'A小调',
     'bpm': 100, 'bars': 32, 'piano_lead': True, 'style': 'jazz', 'tonic': 'Am9', 'tonic_midi': 81,
     'harmony': ['Am9', 'Dm9', 'G13', 'Cmaj9', 'Fmaj7', 'Dm9', 'E7', 'Am9'],
     'bridge': ['Fmaj7', 'Dm9', 'E7', 'Am9'],
     'theme': 'C6 E6 G5 E6 C6 A5|F5 A5 C6 E6 D6 A5|B5 D6 E6 D6 B5 G5|E6 D6 C6 G5 B5 C6|A5 C6 E6 D6 C6 A5|F5 A5 D6 C6 A5 F5|G#5 B5 D6 E6 D6 B5|C6 B5 A5 E5 G5 A5',
     'answer': 'E6 G6 E6 D6 C6 A5|A5 C6 E6 F6 E6 D6|D6 E6 G6 E6 D6 B5|G6 E6 D6 C6 B5 C6|C6 E6 A6 G6 E6 C6|A5 D6 F6 E6 D6 A5|B5 D6 E6 G#6 E6 B5|E6 C6 B5 A5 G5 A5',
     'rhythm': [(0, .3), (.6, .55), (1.5, .3), (2.1, .55), (3, .3), (3.6, .3)],
     'description': '钢琴负责完整旋律与即兴式回答，配柔和Bass、轻叮叮镲和少量干净吉他。小提琴完全不参与，避免抢主角。'},
    {'id': 'p03_after_rain', 'title': '雨后星河', 'genre': '钢琴主导 / 抒情配乐', 'key': 'D小调',
     'bpm': 80, 'bars': 32, 'piano_lead': True, 'style': 'ballad', 'tonic': 'Dm9', 'tonic_midi': 74,
     'harmony': ['Dm9', 'Bbmaj7', 'Fmaj9', 'Cadd9', 'Gm9', 'Dm9', 'Bbmaj7', 'A7'],
     'bridge': ['Gm9', 'Dm9', 'Bbmaj7', 'A7'],
     'theme': 'D5 F5 A5 G5 F5|F5 A5 D6 C6 A5|A5 C6 E6 C6 A5|G5 E5 D5 E5 G5|G5 Bb5 D6 C6 Bb5|A5 F5 E5 F5 A5|F5 D5 F5 A5 D6|E5 G5 A5 C#6 A5',
     'answer': 'A5 D6 F6 E6 D6|D6 F6 A6 F6 D6|C6 E6 G6 E6 C6|E6 D6 C6 G5 E5|Bb5 D6 G6 F6 D6|F6 E6 D6 A5 F5|D6 F6 A6 F6 D6|C#6 E6 A6 G6 E6',
     'rhythm': [(0, 1.125), (1.25, .5), (2, .5), (2.75, .5), (3.5, .375)],
     'description': '钢琴从头到尾唱旋律，后半段加入轻鼓和Bass。小提琴仅在高潮隔小节奏一个低音量长音，不重复钢琴旋律、不演奏高音独奏。'},
]


def parse_theme(text):
    result = []
    for phrase in text.split('|'):
        notes = []
        for token in phrase.split():
            match = re.fullmatch(r'([A-G])([#b]?)(\d)', token)
            if not match:
                raise ValueError('Invalid piano note: ' + token)
            letter, accidental, octave = match.groups()
            notes.append((int(octave) + 1) * 12
                         + {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[letter]
                         + {'': 0, '#': 1, 'b': -1}[accidental])
        result.append(notes)
    return result


def compose_piano(profile):
    style = profile['style']
    definitions = [('piano', '钢琴·右手主旋律', 100), ('piano', '钢琴·中声部与和声', 80),
                   ('piano', '钢琴·左手低音', 87)]
    if style != 'solo':
        definitions += [('bass', 'Bass·轻伴奏', 76), ('drums', '鼓·轻节奏', 72),
                        ('guitar', '吉他·少量背景分解', 57)]
    if style == 'ballad':
        definitions += [('violin', '小提琴·低音量背景长音', 48)]
    tracks = [Track(instrument, f'{index + 1:02d} {name}', level,
                    id=f'{profile["id"]}-track-{index}')
              for index, (instrument, name, level) in enumerate(definitions)]
    themes, answers = parse_theme(profile['theme']), parse_theme(profile['answer'])

    def emit(track_index, bar, beat, duration, pitch, velocity, offset=0):
        track = tracks[track_index]
        if not track.clips or track.clips[-1].start != bar * BAR:
            first, last, section = next(item for item in FORM if item[0] <= bar < item[1])
            progression = profile['bridge'] if section == '留白' else profile['harmony']
            chord = profile['tonic'] if section == '尾声' else progression[(bar - first) % len(progression)]
            track.clips.append(Clip(f'{section} · {chord}', bar * BAR, BAR,
                                    id=f'{profile["id"]}-clip-{track_index}-{bar}'))
        clip = track.clips[-1]
        start = round(beat * PPQ) + offset
        length = min(round(duration * PPQ), BAR - start)
        clip.notes.append(Note(start, max(1, length), pitch, velocity,
                               id=f'{clip.id}-note-{len(clip.notes)}'))

    for bar in range(profile['bars'] - 1):
        first, last, section = next(item for item in FORM if item[0] <= bar < item[1])
        position = bar - first
        strong = section in ('主题B', '再现')
        sparse = section in ('前奏', '留白')
        progression = profile['bridge'] if section == '留白' else profile['harmony']
        chord = profile['tonic'] if section == '尾声' else progression[position % len(progression)]
        root, harmony, guitar = CHORDS[chord]
        if section == '尾声':
            emit(0, bar, 0, 2.75, profile['tonic_midi'], 91)
            for voice, pitch in enumerate(harmony):
                emit(1, bar, 0, 2.5, pitch, 65 - voice * 2, voice * 5)
            emit(2, bar, 0, 2.75, root, 74)
            if style != 'solo':
                emit(3, bar, 0, 2, root, 62)
            continue

        if section == '前奏':
            melody = themes[position % 8]
            rhythm = profile['rhythm']
            pairs = list(zip(melody, rhythm))[:3] if position < 2 else list(zip(melody, rhythm))
        elif section == '留白':
            melody = themes[(position + 4) % 8]
            pairs = [(melody[0], (0, 1.5)), (melody[2], (2, 1.5))]
        else:
            melody = (answers if strong else themes)[position % 8]
            pairs = list(zip(melody, profile['rhythm']))
        for voice, (pitch, (beat, duration)) in enumerate(pairs):
            velocity = (103 if strong else 91 if not sparse else 83) + (4 if voice == 0 else -(voice % 3) * 3)
            emit(0, bar, beat, duration, pitch, velocity)

        if style == 'jazz' and not sparse:
            for beat in (.3, 2.1):
                for voice, pitch in enumerate(harmony):
                    emit(1, bar, beat, .7, pitch, 67 - voice * 3, voice * 4)
        else:
            count = 4 if sparse else 8
            order = (0, 2, 1, 3, 0, 2, 3, 1)
            for pulse in range(count):
                beat = pulse * 4 / count
                emit(1, bar, beat, .7 if sparse else .62, harmony[order[pulse]],
                     (66 if strong else 59) + (5 if pulse % 4 == 0 else -pulse % 3), 7 if pulse % 2 else 0)
        for beat, pitch in ((0, root), (2, root + 12)):
            emit(2, bar, beat, 1.65 if style != 'jazz' else 1.25, pitch, 76 if strong else 66)

        if style == 'solo' or (section == '前奏' and position < 2) or section == '留白':
            continue
        bass_line = ((0, root), (1, root + 7), (2, root + 12), (3, root + 7)) if style == 'jazz' else ((0, root), (2, root + 7))
        for beat, pitch in bass_line:
            emit(3, bar, beat, .72, pitch, 74 if strong else 63)
        for beat in (0, 2):
            emit(4, bar, beat, .12, 0, 67 if strong else 56)
        for beat in (1, 3):
            emit(4, bar, beat, .1, 10 if style == 'jazz' else 1, 46 if strong else 35, 5)
        for pulse in range(8 if strong else 4):
            emit(4, bar, pulse * (.5 if strong else 1), .1, 6 if style == 'jazz' else 2,
                 37 if pulse % 2 == 0 else 25, 42 if style == 'jazz' and pulse % 2 else 0)
        for pulse, tone in enumerate((0, 2, 4, 2) if strong else (0, 3)):
            emit(5, bar, pulse * (1 if strong else 2), .3, guitar[tone], 48)
        if style == 'ballad' and strong and position % 2 == 0:
            emit(6, bar, .25, 2.75, harmony[2], 46)

    project = Project(profile['title'] + ' · ' + profile['genre'], bpm=profile['bpm'], bars=profile['bars'],
                      tracks=tracks, loop_start=0, loop_end=profile['bars'] * BAR)
    project.parameters.update({'bus.piano': 98, 'bus.guitar': 0 if style == 'solo' else 30,
        'bus.bass': 0 if style == 'solo' else 51, 'bus.drums': 0 if style == 'solo' else 35,
        'bus.violin': 14 if style == 'ballad' else 0, 'space.chorus_mix': 0,
        'space.delay_mix': 6 if style != 'jazz' else 3, 'space.delay_time': 68 if style == 'solo' else 79,
        'space.delay_feedback': 14, 'guitar.amp': 0, 'guitar.modulation': 0,
        'guitar.gate': 0, 'guitar.compressor': 0, 'guitar.cabinet': 0})
    for target in ('bus.piano', 'bus.guitar', 'bus.bass', 'bus.drums', 'bus.violin', 'space.delay_mix'):
        points = []
        for first, last, section in FORM:
            base = project.parameters[target]
            amount = {'前奏': .86, '主题A': .95, '主题B': 1.04, '留白': .80, '再现': 1.03, '尾声': .90}[section]
            points.append(Point(first * BAR, round(base * amount)))
        points += [Point((profile['bars'] - 1) * BAR, points[-1].value),
                   Point(profile['bars'] * BAR - PPQ // 2, 0)]
        project.automation.append(Automation(target, 'linear', points))
    return project.validate()
