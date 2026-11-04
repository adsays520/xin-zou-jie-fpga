"""Guitar-led arrangement of the user's three-page 山海 score."""
from copy import deepcopy
from fractions import Fraction

from rock_scores import Automation, BAR, Clip, Note, PPQ, Point, Project, Track
from shanhai_score import CHORDS, melody_notes


PROFILE = {
    'id': 'g03_shanhai', 'title': '山海 · 吉他与鼓组改编',
    'genre': '用户谱改编 / 吉他主旋律 / 鼓组增强', 'key': 'E调（C指法＋4半音）',
    'bpm': 96, 'bars': 72, 'guitar_lead': True,
    'description': '依据用户提供的三页谱，吉他演奏原旋律；分解与正反扫弦、明显加强的底鼓军鼓，钢琴和小提琴轻铺背景。延音52，长音用补拨保持。',
    'original': False, 'gain_policy': 'custom-drum-forward',
    'mix_note': '已载入《山海》鼓组增强版：鼓总线64、高潮76；吉他仍负责主旋律。未自动连接或播放。',
    'attribution': '山海；词曲：草东没有派对；用户谱标注演唱：万豹，编配：无限延音。本工程根据用户上传的三页谱作器乐再编配。',
}
# Zero-based boundaries follow all 70 printed bars; two bars are added for tails.
FORM = [(0, 4, '前奏'), (4, 20, '主歌A'), (20, 29, '第一段副歌'),
        (29, 36, '推进间奏'), (36, 46, '主歌B'), (46, 51, '蓄力'),
        (51, 59, '高音副歌'), (59, 63, '长音高潮'), (63, 67, '尾段间奏'),
        (67, 70, '收束'), (70, 72, '自然尾音')]
VOICINGS = {'F': (45, 52, 57, 61), 'G': (47, 54, 59, 63),
            'Am': (49, 56, 61, 64), 'F/C': (52, 57, 61, 64)}
BASS_ROOT = {'F': 33, 'G': 35, 'Am': 37, 'F/C': 40}
PIANO = {'F': (57, 61, 64), 'G': (59, 63, 66),
         'Am': (56, 61, 64), 'F/C': (57, 61, 64)}
MIX = {
    '前奏':       (42, 20, 42, 13, 0, 35),
    '主歌A':      (46, 24, 62, 14, 0, 43),
    '第一段副歌': (48, 26, 70, 15, 8, 56),
    '推进间奏':   (47, 27, 70, 13, 0, 59),
    '主歌B':      (47, 25, 66, 17, 8, 47),
    '蓄力':       (48, 26, 72, 17, 9, 61),
    '高音副歌':   (50, 27, 76, 18, 12, 67),
    '长音高潮':   (50, 27, 76, 16, 10, 67),
    '尾段间奏':   (47, 25, 69, 17, 8, 57),
    '收束':       (45, 23, 65, 14, 6, 49),
    '自然尾音':   (44, 22, 60, 12, 5, 49),
}


def section_at(bar):
    return next(section for first, last, section in FORM if first <= bar < last)


def _put(tracks, track_index, bar, beat, duration, pitch, velocity, label=''):
    track = tracks[track_index]
    if not track.clips or track.clips[-1].start != bar * BAR:
        track.clips.append(Clip(label or section_at(bar), bar * BAR, BAR,
                                id=f'g03-track-{track_index}-bar-{bar}'))
    clip = track.clips[-1]
    start = round(beat * PPQ)
    length = max(1, min(round(duration * PPQ), BAR - start))
    clip.notes.append(Note(start, length, pitch, velocity, id=f'{clip.id}-note-{len(clip.notes)}'))


def _lead(tracks):
    for source in melody_notes():
        start, end = source['start'] / 4, source['end'] / 4
        # Each RAM envelope lasts ~710ms at sustain=52. Re-pick long sung
        # notes every .875 beats instead of letting the melody disappear.
        attack = start
        repeat = 0
        while attack < end:
            bar = int(attack // 4)
            next_attack = min(end, attack + Fraction(7, 8))
            duration = min(next_attack - attack, Fraction(13, 16))
            if repeat == 0:
                velocity = 108 if bar >= 51 else 103
            else:
                velocity = (94 if bar >= 51 else 91) - min(3, repeat)
            _put(tracks, 0, bar, attack % 4, duration, source['pitch'], velocity,
                 f'谱第{source["source_bars"][0]}小节 · 吉他主旋律')
            attack = next_attack
            repeat += 1


def compose_shanhai():
    roles = [('guitar', '01 主旋律·吉他（按用户谱）', 100),
             ('guitar', '02 吉他·分解与正反扫弦', 74),
             ('guitar', '03 吉他·间奏回答', 76),
             ('bass', '04 Bass·和声根音', 90),
             ('piano', '05 钢琴·轻和声与句间填充', 72),
             ('violin', '06 小提琴·低音量背景长音', 68),
             ('drums', '07 鼓·底鼓军鼓（加强）', 100),
             ('drums', '08 鼓·镲片律动', 92),
             ('drums', '09 鼓·通鼓过门', 96)]
    tracks = [Track(instrument, name, level, id=f'g03-track-{index}')
              for index, (instrument, name, level) in enumerate(roles)]
    _lead(tracks)
    for bar in range(70):
        section = section_at(bar)
        chord_parts = CHORDS[bar].split('+')
        chord = chord_parts[0]
        full = section in ('第一段副歌', '推进间奏', '高音副歌', '长音高潮', '尾段间奏')
        build = section == '蓄力'
        last = bar == 69
        voicing = VOICINGS[chord]

        def put(index, beat, duration, pitch, velocity, label=''):
            _put(tracks, index, bar, beat, duration, pitch, velocity, label)

        def strum(beat, up=False, strength=75, which=chord):
            pitches = tuple(reversed(VOICINGS[which])) if up else VOICINGS[which]
            for voice, pitch in enumerate(pitches):
                put(1, beat + voice * Fraction(3, 80), .48, pitch, strength - voice * 3,
                    section + (' · 上扫' if up else ' · 下扫'))

        if last or bar in (51, 52, 67, 68):
            # Printed break-down strokes: leave air for the high melody.
            strum(0, strength=79 if last else 70)
        elif full or build:
            strum(.125, strength=79 if full else 72)
            strum(2.5, up=True, strength=70 if full else 65)
            if bar % 4 == 3 and section != '长音高潮':
                # A light upstroke pickup, kept below the melody.
                for voice, pitch in enumerate(reversed(voicing[-2:])):
                    put(1, 3.5 + voice * Fraction(3, 80), .28, pitch, 55 - voice * 3)
        else:
            # Finger-picked backing follows the printed chord, below the lead.
            for pulse, beat in enumerate((0, 1, 2, 3)):
                active_chord = chord_parts[1] if len(chord_parts) == 2 and beat >= 2 else chord
                pitches = VOICINGS[active_chord]
                put(1, beat, .52, pitches[(0, 2, 1, 3)[pulse]], 62 + (pulse % 2) * 3)

        if section in ('前奏', '推进间奏', '尾段间奏') and bar % 2 == 1:
            # Added replies only where the printed melody is resting.
            for beat, pitch in ((.75, voicing[2] + 12), (1.5, voicing[-1] + 12), (3.25, voicing[2] + 12)):
                put(2, beat, .40, pitch, 73 if full else 66, '吉他·原创句间回答')

        bass_beats = (0,) if last else (0, 1.5, 2.5, 3.5) if full else (0, 2)
        for pulse, beat in enumerate(bass_beats):
            active_chord = chord_parts[1] if len(chord_parts) == 2 and beat >= 2 else chord
            root = BASS_ROOT[active_chord]
            put(3, beat, .58, root + (7 if pulse == 3 and not last else 0), 86 if pulse == 0 else 75)

        if bar % 2 == 0 or section == '自然尾音':
            for voice, pitch in enumerate(PIANO[chord]):
                put(4, .5 + voice * .25, 1.35, pitch, 58 - voice * 4, '钢琴·轻背景')
        if section in ('推进间奏', '尾段间奏') and bar % 4 == 2:
            for pulse, pitch in enumerate(reversed(PIANO[chord])):
                put(4, 2.5 + pulse * .375, .35, pitch + 12, 49 - pulse * 3, '钢琴·句间回答')

        if section in ('第一段副歌', '主歌B', '蓄力', '高音副歌', '长音高潮', '尾段间奏') and bar % 4 == 0:
            # One monophonic low-register bow, never doubling the melody line.
            put(5, .25, 3.25, PIANO[chord][1] + 7, 48, '小提琴·低声铺底')

        if last:
            put(6, 0, .1, 0, 113)
            put(8, 0, .1, 5, 78)
            continue
        if section == '前奏' and bar < 2:
            kicks, snares, hats = (0,), (3,), (0, 1, 2, 3)
        elif full:
            kicks, snares, hats = (0, .75, 1.5, 2, 2.75), (1, 3), tuple(pulse * .5 for pulse in range(8))
        elif build:
            kicks, snares, hats = (0, 1.5, 2.75), (1, 3), tuple(pulse * .5 for pulse in range(8))
        else:
            kicks, snares, hats = (0, 1.5, 2.5), (1, 3), tuple(pulse * .5 for pulse in range(8))
        for beat in kicks:
            put(6, beat, .1, 0, 116 if full else 109 if bar >= 4 else 96)
        for beat in snares:
            put(6, beat + Fraction(1, 80), .1, 1 if bar >= 2 else 10, 118 if full else 111 if bar >= 4 else 87)
        if full:
            put(6, 2.75 + Fraction(1, 40), .1, 1, 45)
        for pulse, beat in enumerate(hats):
            voice = 6 if section == '长音高潮' else 3 if full and pulse == 7 else 2
            put(7, beat, .1, voice, (73 if full else 63) - pulse % 2 * 12)
        if full and (bar % 4 == 0 or bar in (51, 59, 63)):
            put(8, 0, .1, 5, 83)
        if bar in (3, 19, 28, 35, 45, 50, 58, 62, 66):
            for pulse, voice in enumerate((9, 8, 8, 7)):
                put(8, 3 + pulse * .25, .1, voice, 76 + pulse * 5, '鼓·段落过门')

    project = Project(PROFILE['title'], bpm=96, bars=72, tracks=tracks, loop_end=72 * BAR, guitar_sustain=52)
    project.parameters.update({'bus.guitar': 46, 'bus.bass': 24, 'bus.drums': 64,
        'bus.piano': 14, 'bus.violin': 0, 'guitar.amp': 3, 'guitar.drive': 43,
        'guitar.tone': 50, 'guitar.level': 54, 'guitar.mix': 127,
        'guitar.cabinet': 1, 'guitar.gate': 1, 'guitar.threshold': 14,
        'guitar.compressor': 0, 'guitar.modulation': 0,
        'space.chorus_mix': 0, 'space.delay_mix': 0, 'space.delay_time': 32, 'space.delay_feedback': 0})
    for index, target in enumerate(('bus.guitar', 'bus.bass', 'bus.drums', 'bus.piano', 'bus.violin', 'guitar.drive')):
        points = [Point(first * BAR, MIX[section][index]) for first, last, section in FORM]
        if target.startswith('bus.'):
            points.extend((Point(71 * BAR, points[-1].value), Point(72 * BAR - PPQ // 2, 0)))
            # Linear transitions are confined to short explicit ramps; avoid
            # ramping the whole verse accidentally toward a later climax.
            expanded = []
            for point in points:
                if expanded and point.tick > expanded[-1].tick + PPQ // 8:
                    expanded.append(Point(point.tick - PPQ // 8, expanded[-1].value))
                expanded.append(point)
            points = expanded
        project.automation.append(Automation(target, 'linear' if target.startswith('bus.') else 'step', points))
    return project.validate()


def shanhai_short(project):
    """Six bars of page-3 chorus followed by a two-bar arranged resolution."""
    result = deepcopy(project)
    first, last = 51 * BAR, 57 * BAR
    result.name = '山海 · 高音副歌与收束20秒试听'
    result.bars, result.loop_start, result.loop_end = 8, 0, 8 * BAR
    for track in result.tracks:
        track.clips = [clip for clip in track.clips if first <= clip.start < last]
        for clip in track.clips:
            clip.start -= first
    for lane in result.automation:
        value = lane.value_at(first, result.parameters[lane.target])
        result.parameters[lane.target] = value
        lane.points = [Point(0, value)]
        if lane.target.startswith('bus.'):
            lane.points.extend((Point(7 * BAR, value), Point(8 * BAR - PPQ // 2, 0)))
    tracks = result.tracks
    for pulse in range(3):
        _put(tracks, 0, 6, pulse * .875, .7, 73, 101 - pulse * 7, '短版·C#m收束')
    for voice, pitch in enumerate(VOICINGS['Am']):
        _put(tracks, 1, 6, voice * Fraction(3, 80), .55, pitch, 74 - voice * 3, '短版·结束扫弦')
    _put(tracks, 3, 6, 0, 1, 37, 83, '短版·根音收束')
    for pitch in PIANO['Am']:
        _put(tracks, 4, 6, 0, 1.5, pitch, 46, '短版·轻和声')
    _put(tracks, 6, 6, 0, .1, 0, 114, '短版·结束底鼓')
    _put(tracks, 8, 6, 0, .1, 5, 78, '短版·结束镲')
    return result.validate()
