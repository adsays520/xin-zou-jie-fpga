from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
BASE = WORKSPACE / 'drum_bass_pitch_20261013'
APP = BASE / 'violin_r15'
sys.path[:0] = [str(APP), str(BASE / 'host'), str(BASE / 'tools/python_deps')]
from arrangement_model import Automation, BAR, Clip, Note, PPQ, Point, Project, Track
from demo_headroom import with_headroom


NEON_PATH = APP / 'demos/neon_runway_20261024/build_demo.py'
specification = importlib.util.spec_from_file_location('original_neon_demo', NEON_PATH)
neon = importlib.util.module_from_spec(specification)
specification.loader.exec_module(neon)
CHORDS = {**neon.CHORDS,
    'Cmaj9': (36, [55, 59, 62, 64], [48, 55, 59, 62, 64]),
    'Cmaj7': (36, [55, 59, 64, 67], [48, 55, 59, 64, 67]),
    'Am9': (33, [55, 59, 60, 64], [45, 52, 55, 59, 60]),
    'Am7': (33, [55, 60, 64, 69], [45, 52, 55, 60, 64]),
    'G13': (31, [53, 57, 59, 64], [43, 50, 53, 57, 59]),
    'Em7': (28, [55, 59, 62, 67], [40, 47, 55, 59, 62]),
    'Em9': (28, [55, 59, 64, 66], [40, 47, 54, 55, 59]),
    'Fmaj7': (29, [57, 60, 64, 65], [41, 48, 57, 60, 64]),
    'Bm7b5': (35, [57, 62, 65, 69], [47, 53, 57, 62, 65]),
    'E7': (28, [56, 59, 62, 64], [40, 47, 56, 59, 62]),
    'Gadd9': (31, [55, 59, 62, 69], [43, 50, 55, 59, 69]),
    'D/F#': (30, [57, 62, 66, 69], [42, 50, 57, 62, 66]),
    'D7': (38, [54, 60, 62, 69], [50, 54, 60, 62, 69]),
    'Dadd9': (38, [57, 62, 64, 66], [50, 57, 62, 64, 66]),
    'B7': (35, [57, 63, 66, 71], [47, 54, 57, 63, 66]),
}
STANDARD_FORM = [(0, 4, 'intro'), (4, 12, 'verse'), (12, 20, 'chorus'),
                 (20, 24, 'break'), (24, 30, 'return'), (30, 32, 'coda')]
SHORT_FORM = [(0, 4, 'intro'), (4, 12, 'verse'), (12, 20, 'chorus'),
              (20, 22, 'return'), (22, 24, 'coda')]
LONG_FORM = [(0, 8, 'intro'), (8, 16, 'verse'), (16, 24, 'chorus'),
             (24, 28, 'break'), (28, 38, 'return'), (38, 40, 'coda')]
FORM_NAMES = {'intro': '前奏', 'verse': '主题A', 'chorus': '主题B', 'break': '留白',
              'return': '回归', 'coda': '收束'}
PROFILES = [
    {'id': '01_city_lights', 'title': '晨光车站', 'genre': 'City Pop / 都市律动', 'key': 'C大调',
     'bpm': 108, 'bars': 32, 'form': STANDARD_FORM, 'tonic': 'Cmaj9', 'tonic_midi': 72,
     'harmony': ['Cmaj9', 'Am9', 'Dm9', 'G13', 'Em7', 'A7', 'Dm9', 'G13'],
     'bridge': ['Fmaj7', 'Em7', 'Dm9', 'G13'], 'style': 'city', 'lift': 0,
     'theme': 'E5 G5 A5 G5 E5|C5 E5 G5 A5 E5|F5 A5 C6 A5 F5|B4 D5 E5 G5 D5|G5 B5 A5 G5 E5|C#5 E5 G5 A5 E5|F5 E5 D5 F5 A5|B4 D5 E5 D5 B4',
     'rhythm': [(.25, .375), (.75, .75), (1.75, .5), (2.5, .5), (3.25, .625)],
     'delay': 79, 'chorus': 13, 'description': '切分Bass、后拍扫弦、九和弦钢琴与明亮小提琴，偏轻快的城市夜行。'},
    {'id': '02_rain_cafe', 'title': '雨夜咖啡', 'genre': 'Jazz / 慢拍摇摆', 'key': 'A小调',
     'bpm': 78, 'bars': 24, 'form': SHORT_FORM, 'tonic': 'Am9', 'tonic_midi': 69,
     'harmony': ['Am9', 'Dm9', 'G13', 'Cmaj9', 'Fmaj7', 'Bm7b5', 'E7', 'Am9'],
     'bridge': ['Fmaj7', 'Bm7b5', 'E7', 'Am9'], 'style': 'jazz', 'lift': 0,
     'theme': 'C5 E5 B4 A4|F5 E5 D5 A4|B4 D5 E5 F5|E5 D5 B4 G4|A4 C5 E5 A4|D5 F5 A4 B4|G#4 B4 D5 E5|C5 B4 A4 E5',
     'rhythm': [(.5, .75), (1.5, .5), (2.25, .625), (3.25, .5)],
     'delay': 72, 'chorus': 6, 'description': '轻摇摆叮叮镲、步行低音、稀疏钢琴和声；不是通过降低采样率模拟Lo-fi。'},
    {'id': '03_northern_letter', 'title': '北风来信', 'genre': 'Folk / 原声抒情', 'key': 'G大调',
     'bpm': 72, 'bars': 24, 'form': SHORT_FORM, 'tonic': 'Gadd9', 'tonic_midi': 67,
     'harmony': ['Gadd9', 'D/F#', 'Em7', 'Cmaj7', 'Am7', 'D7', 'Gadd9', 'D7'],
     'bridge': ['Cmaj7', 'Am7', 'D7', 'Gadd9'], 'style': 'folk', 'lift': 12,
     'theme': 'G4 B4 D5 B4|A4 F#4 A4 D5|G4 B4 E5 D5|E5 D5 B4 G4|A4 C5 E5 C5|F#4 A4 C5 A4|B4 D5 G5 D5|A4 F#4 E4 D4',
     'rhythm': [(0, .875), (1, 1.25), (2.5, .5), (3.25, .5)],
     'delay': 79, 'chorus': 4, 'description': '指弹是主角，小提琴像人声一样分句回答；先稀疏、后加入完整节奏组。'},
    {'id': '04_red_engine', 'title': '赤色引擎', 'genre': 'Rock / 切分轻摇滚', 'key': 'E小调',
     'bpm': 124, 'bars': 32, 'form': STANDARD_FORM, 'tonic': 'Em9', 'tonic_midi': 76,
     'harmony': ['Em9', 'Cmaj7', 'Gadd9', 'Dadd9', 'Em7', 'Am7', 'Cmaj7', 'B7'],
     'bridge': ['Am7', 'Cmaj7', 'Dadd9', 'B7'], 'style': 'rock', 'lift': 0,
     'theme': 'E5 G5 A5 B5 G5 E5|G5 E5 D5 E5 G5 E5|B4 D5 G5 A5 B5 G5|F#5 E5 D5 A4 D5 F#5|E5 G5 B5 D6 B5 G5|A5 G5 E5 C5 E5 G5|E5 G5 C6 B5 G5 E5|D#5 F#5 A5 B5 F#5 D#5',
     'rhythm': [(0, .375), (.5, .625), (1.25, .5), (2, .5), (2.75, .5), (3.5, .375)],
     'delay': 93, 'chorus': 8, 'description': '低音弦Riff、力度分层和强后拍；吉他轻度Crunch，不是高增益金属音墙。'},
    {'id': '05_stellar_voyage', 'title': '星海远航', 'genre': 'Cinematic / 渐进配乐', 'key': 'D小调',
     'bpm': 92, 'bars': 40, 'form': LONG_FORM, 'tonic': 'Dm9', 'tonic_midi': 74,
     'harmony': ['Dm9', 'Bbmaj7', 'Fmaj9', 'Cadd9', 'Gm9', 'Dm9', 'Bbmaj7', 'A7'],
     'bridge': ['Gm9', 'Dm9', 'Bbmaj7', 'A7'], 'style': 'cinema', 'lift': 12,
     'theme': 'D5 F5 A5|F5 A5 D5|A4 C5 E5|G4 C5 E5|G4 Bb4 D5|F5 E5 D5|D5 F5 A5|C#5 E5 A5',
     'rhythm': [(0, 1.375), (1.5, .875), (2.5, 1.25)],
     'delay': 94, 'chorus': 12, 'description': '高音钢琴固定音型、长线旋律、通鼓铺陈和逐段渐强；小提琴仍是单声部独奏。'},
]


def midi(token):
    match = re.fullmatch(r'([A-G])([#b]?)(-?\d+)', token)
    if not match:
        raise ValueError('Invalid note name: ' + token)
    letter, accidental, octave = match.groups()
    return (int(octave) + 1) * 12 + {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[letter] + {'': 0, '#': 1, 'b': -1}[accidental]


def compose(profile):
    style, bars = profile['style'], profile['bars']
    roles = [('piano', '钢琴·和声', 90), ('piano', '钢琴·回答/固定音型', 77),
             ('guitar', '吉他·分解/Riff', 89), ('guitar', '吉他·切分和弦', 80),
             ('bass', 'Bass·节奏低音', 100), ('violin', '小提琴·主旋律', 94),
             ('drums', '鼓·底鼓军鼓', 100), ('drums', '鼓·镲片', 91), ('drums', '鼓·过门', 94)]
    tracks = [Track(instrument, f'{index + 1:02d} {role}', level, id=f'{profile["id"]}-track-{index}')
              for index, (instrument, role, level) in enumerate(roles)]
    themes = [[midi(token) for token in phrase.split()] for phrase in profile['theme'].split('|')]
    swing = 48 if style == 'jazz' else 10

    def emit(track_index, bar, beat, length, pitch, velocity, offset=0):
        track = tracks[track_index]
        if not track.clips or track.clips[-1].start != bar * BAR:
            first, last, section = next(item for item in profile['form'] if item[0] <= bar < item[1])
            chord = profile['tonic'] if section == 'coda' else (
                profile['bridge'] if section == 'break' else profile['harmony'])[(bar - first) % (4 if section == 'break' else 8)]
            track.clips.append(Clip(f'{FORM_NAMES[section]} · {chord}', bar * BAR, BAR,
                                    id=f'{profile["id"]}-clip-{track_index}-{bar}'))
        clip = track.clips[-1]
        start = max(0, min(BAR - 1, round(beat * PPQ) + offset))
        duration = max(1, min(round(length * PPQ), BAR - start))
        clip.notes.append(Note(start, duration, int(pitch), max(1, min(127, int(velocity))),
                               id=f'{clip.id}-note-{len(clip.notes)}'))

    def chord_hit(bar, beat, duration, pitches, velocity, guitar=False):
        for voice, pitch in enumerate(pitches):
            emit(3 if guitar else 0, bar, beat, duration, pitch, velocity - voice * 2, voice * (9 if guitar else 4))

    for bar in range(bars - 1):
        first, last, section = next(item for item in profile['form'] if item[0] <= bar < item[1])
        position = bar - first
        strong = section in ('chorus', 'return')
        sparse = section in ('intro', 'break')
        chord = profile['tonic'] if section == 'coda' else (
            profile['bridge'] if section == 'break' else profile['harmony'])[position % (4 if section == 'break' else 8)]
        bass_root, piano, guitar = CHORDS[chord]
        if section == 'coda':
            chord_hit(bar, 0, 2.5, sorted(set([bass_root + 12, *piano, profile['tonic_midi']])), 80)
            chord_hit(bar, 0, 2.25, guitar, 78, guitar=True)
            emit(4, bar, 0, 2.25, bass_root, 88)
            emit(5, bar, 0, 2.5, profile['tonic_midi'], 89)
            emit(6, bar, 0, .125, 0, 90)
            emit(8, bar, 0, .125, 5, 63)
            continue

        if style in ('folk', 'cinema') or sparse:
            chord_hit(bar, 0, 2.75 if style != 'cinema' else 3.25, piano, 62 if sparse else 72)
        else:
            voicing = piano if position % 2 == 0 else list(dict.fromkeys([*piano[1:], piano[0] + 12]))
            chord_hit(bar, .25 if style == 'city' else 0, 1.1, voicing, 72 if strong else 64)
            chord_hit(bar, 2.5 if style != 'jazz' else 2.6, .85, voicing[1:], 66 if strong else 57)
        if style == 'cinema':
            for pulse in range(8 if not sparse else 4):
                pitch = piano[(pulse * 3 + position) % len(piano)]
                while pitch < 76:
                    pitch += 12
                emit(1, bar, pulse * (0.5 if not sparse else 1), .34, pitch, 59 + (pulse % 2) * 6)
        elif position % 4 == 3 or section == 'break':
            for voice, tone in enumerate(reversed(piano[1:])):
                pitch = tone
                while pitch < 76:
                    pitch += 12
                emit(1, bar, 2.5 + voice * .5, .35, pitch, 64 + voice * 4)

        if style == 'rock':
            riff = [(0, bass_root + 12), (.75, bass_root + 19), (2, bass_root + 12), (2.75, bass_root + 22)]
            for beat, pitch in riff:
                emit(2, bar, beat, .38, pitch, 91 if beat in (0, 2) else 77)
            if not sparse:
                for beat in (1.5, 3.5):
                    chord_hit(bar, beat, .35, guitar[:3], 83 if strong else 74, guitar=True)
        else:
            count = 8 if style == 'folk' or (style == 'city' and not strong) else 4
            if section == 'break':
                count = 3
            order = (0, 2, 4, 3, 1, 2, 4, 2)
            for pulse in range(count):
                beat = pulse * 4 / count
                emit(2, bar, beat, .38, guitar[order[(pulse + position % 2) % len(order)]],
                     61 if sparse else 72 + (pulse % 4 == 0) * 6, swing if pulse % 2 else 0)
            if not sparse and style in ('city', 'folk'):
                hits = (1.5, 3.5) if style == 'city' else (0, 2.75) if strong else (0,)
                for beat in hits:
                    chord_hit(bar, beat, .35, guitar[1:4] if style == 'city' else guitar,
                              76 if strong else 65, guitar=True)

        if section != 'intro' or position >= (last - first) // 2:
            if style == 'jazz' and not sparse:
                bass_line = [(0, bass_root), (1, bass_root + 7), (2, bass_root + 12), (3, bass_root + 9)]
            elif style == 'folk':
                bass_line = [(0, bass_root), (2.5, bass_root + 7)]
            elif style == 'cinema':
                bass_line = [(0, bass_root), (2, bass_root + 12)]
            elif sparse:
                bass_line = [(0, bass_root), (2.5, bass_root + 7)]
            else:
                bass_line = [(0, bass_root), (1.5, bass_root + 7), (2.75, bass_root + 12), (3.5, bass_root)]
            for beat, pitch in bass_line:
                emit(4, bar, beat, .65 if style == 'jazz' else .8, pitch,
                     (94 if strong else 82) - (0 if beat == 0 else 10))

        melody = themes[position % 8]
        rhythm = profile['rhythm']
        if section == 'break':
            melody, rhythm = [piano[-1] + 12], [(.5, 2.75)]
        elif section == 'intro':
            melody, rhythm = ([melody[-1]], [(2, 1.5)]) if position >= last - first - 2 else ([], [])
        elif strong:
            melody = [pitch + profile['lift'] for pitch in melody]
        for voice, (pitch, (beat, duration)) in enumerate(zip(melody, rhythm)):
            emit(5, bar, beat, duration, pitch, (94 if strong else 78) + (4 if voice == 0 else -(voice % 5)))

        if style == 'jazz':
            kicks, snares = ((0, 2.5), (1, 3))
        elif style == 'folk':
            kicks, snares = ((0, 2), (1, 3)) if not sparse else ((0,), (3,))
        elif style == 'cinema':
            kicks, snares = ((0, 1.5, 2.5), (3,)) if strong else ((0, 2), ())
        elif style == 'rock':
            kicks, snares = ((0, .75, 1.5, 2, 2.75), (1, 3))
        else:
            kicks, snares = ((0, .75, 2, 2.75), (1, 3))
        for beat in kicks:
            emit(6, bar, beat, .125, 0, 101 if strong else 78 if sparse else 91)
        for beat in snares:
            emit(6, bar, beat, .125, 10 if style == 'jazz' or sparse else 1,
                 57 if sparse or style == 'jazz' else 110 if style == 'rock' else 95, 6)
        if not sparse and style in ('jazz', 'city'):
            emit(6, bar, 2.75, .1, 1, 34, 7)
        hats = 4 if sparse else 16 if style == 'city' and strong else 8
        for pulse in range(hats):
            beat = pulse * 4 / hats
            voice = 6 if style == 'jazz' else 3 if strong and pulse == hats - 1 else 2
            emit(7, bar, beat, .1, voice, (58 if strong else 45) - (pulse % 2) * 16 + position % 6,
                 swing if pulse % 2 else 0)
        if strong and position % 4 == 0:
            emit(8, bar, 0, .125, 5, 73)
        if style == 'cinema':
            for beat, voice in ((0, 7), (1.5, 8), (2.5, 7)):
                emit(8, bar, beat, .125, voice, 82 if strong else 48)
        if position % 4 == 3 and section != 'intro':
            for pulse, voice in enumerate((9, 8, 8, 7)):
                emit(8, bar, 3 + pulse * .25, .125, voice, (48 if style in ('jazz', 'folk') else 65) + pulse * 6)
        if style == 'city' and strong:
            emit(8, bar, 3, .1, 4, 57, 12)

    project = Project(profile['title'] + ' · 五乐器合奏', bpm=profile['bpm'], bars=bars,
                      tracks=tracks, loop_start=0, loop_end=bars * BAR)
    project.parameters.update({'bus.guitar': 72, 'bus.piano': 67, 'bus.drums': 65, 'bus.bass': 78,
        'bus.violin': 84, 'space.chorus_mix': profile['chorus'], 'space.chorus_rate': 24,
        'space.chorus_depth': 24, 'space.delay_mix': 12, 'space.delay_time': profile['delay'],
        'space.delay_feedback': 23, 'guitar.amp': 2 if style == 'rock' else 0,
        'guitar.drive': 28, 'guitar.tone': 53, 'guitar.level': 77,
        'guitar.mix': 43 if style == 'rock' else 127, 'guitar.cabinet': int(style == 'rock'),
        'guitar.gate': 0, 'guitar.compressor': 0, 'guitar.modulation': 0})
    for target in ('bus.guitar', 'bus.piano', 'bus.drums', 'bus.bass', 'bus.violin', 'space.delay_mix'):
        points = []
        for first, last, section in profile['form']:
            amount = {'intro': .76, 'verse': .92, 'chorus': 1.08, 'break': .72, 'return': 1.08, 'coda': .92}[section]
            base = project.parameters[target]
            if target == 'space.delay_mix':
                value = 20 if section == 'break' else 14 if section in ('chorus', 'return') else 10
            else:
                value = min(104, round(base * amount))
            points.append(Point(first * BAR, value))
        points += [Point((bars - 1) * BAR, points[-1].value), Point(bars * BAR - PPQ // 2, 0)]
        project.automation.append(Automation(target, 'linear', points))
    project.automation.append(Automation('space.chorus_mix', 'step',
        [Point(first * BAR, profile['chorus'] + (3 if section in ('chorus', 'return') else 0))
         for first, last, section in profile['form']]))
    return project.validate()


def short_version(project, title):
    result = deepcopy(project)
    start = (project.bars - 8) * BAR
    result.name = title + ' · 精华8小节'
    result.bars, result.loop_start, result.loop_end = 8, 0, 8 * BAR
    for track in result.tracks:
        track.clips = [clip for clip in track.clips if clip.start >= start]
        for clip in track.clips:
            clip.start -= start
    for lane in result.automation:
        baseline = lane.value_at(start, result.parameters[lane.target])
        result.parameters[lane.target] = baseline
        lane.points = [Point(point.tick - start, point.value) for point in lane.points if point.tick >= start]
        if lane.points[0].tick != 0:
            lane.points.insert(0, Point(0, baseline))
    return result.validate()


def generate():
    from piano_scores import PIANO_PROFILES, compose_piano
    from rock_scores import ROCK_PROFILES, compose_rock
    from rock_short_tail import PROFILE as SHORT_ROCK, compose_short_rock
    from build_shanhai import save_projects as save_shanhai_projects
    from build_fuji import save_projects as save_fuji_projects
    from build_fuji_violin import save_projects as save_fuji_violin_projects
    from build_fuji_pad import save_projects as save_fuji_pad_projects
    from build_time_machine import save_projects as save_time_machine_projects

    directory = ROOT / 'projects'
    directory.mkdir(exist_ok=True)
    catalog = {'format': 'tang-demo-library-v1', 'songs': [], 'demo_bus_gain': 0.5}
    proof = {'generated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(), 'projects': {},
             'real_serial_connected': False, 'board_listening_validated': False}
    for profile in [*PIANO_PROFILES, SHORT_ROCK, *ROCK_PROFILES, *PROFILES]:
        factory = compose_short_rock if profile is SHORT_ROCK else compose_piano if profile.get('piano_lead') else compose_rock if profile.get('guitar_lead') else compose
        project = factory(profile)
        short = short_version(project, profile['title'])
        paths = {}
        for variant, score in (('full', project), ('short', short)):
            score = with_headroom(score)
            path = directory / f'{profile["id"]}_{variant}.tang.json'
            analysis = neon.analyze(score)
            score.save(path)
            assert Project.load(path) == score
            proof['projects'][path.name] = {**analysis, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            paths[variant] = path.relative_to(ROOT).as_posix()
        catalog['songs'].append({key: profile[key] for key in ('id', 'title', 'genre', 'key', 'bpm', 'bars', 'description')}
                               | paths | {'piano_lead': bool(profile.get('piano_lead')),
                                          'guitar_lead': bool(profile.get('guitar_lead')),
                                          'duration_seconds': project.bars * 240 / project.bpm,
                                          'short_seconds': 8 * 240 / project.bpm})
    original = APP / 'demos/neon_runway_20261024'
    paths = {}
    for variant, name in (('full', 'Neon_Runway_32bars.tang.json'), ('short', 'Neon_Runway_8bars.tang.json')):
        path = directory / f'06_neon_runway_{variant}.tang.json'
        score = with_headroom(Project.load(original / name))
        score.save(path)
        proof['projects'][path.name] = {**neon.analyze(score), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        paths[variant] = path.relative_to(ROOT).as_posix()
    catalog['songs'].append({'id': '06_neon_runway', 'title': '霓虹航线', 'genre': 'Fusion / 五路合奏',
        'key': 'D小调', 'bpm': 96, 'bars': 32, 'duration_seconds': 80, 'short_seconds': 20,
        'description': '保留原创曲谱并降低总线音量：切分低音、钢琴回答、分解与扫弦、主旋律和多段落过门。', **paths})
    shanhai_entry, shanhai_reports = save_shanhai_projects()
    catalog['songs'].insert(3, shanhai_entry)
    proof['projects'].update(shanhai_reports)
    fuji_entry, fuji_reports = save_fuji_projects()
    catalog['songs'].insert(3, fuji_entry)
    proof['projects'].update(fuji_reports)
    fuji_violin_entry, fuji_violin_reports = save_fuji_violin_projects()
    catalog['songs'].insert(3, fuji_violin_entry)
    proof['projects'].update(fuji_violin_reports)
    fuji_pad_entry, fuji_pad_reports = save_fuji_pad_projects()
    catalog['songs'].insert(3, fuji_pad_entry)
    proof['projects'].update(fuji_pad_reports)
    time_machine_entry, time_machine_reports = save_time_machine_projects()
    catalog['songs'].insert(3, time_machine_entry)
    proof['projects'].update(time_machine_reports)
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'validation.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    return catalog, proof


if __name__ == '__main__':
    library, evidence = generate()
    for song in library['songs']:
        report = evidence['projects'][Path(song['full']).name]
        print(f'{song["title"]}: {song["bpm"]} BPM, {song["duration_seconds"]:.1f}s, '
              f'{report["notes"]} notes, {report["maximum_bytes_per_100ms"]} bytes/100ms, '
              f'{report["simultaneous_instrument_types"]} engines')
