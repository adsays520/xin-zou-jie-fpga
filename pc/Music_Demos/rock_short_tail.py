"""Original guitar-led rock, with real per-voice envelope RAM shortening."""
from rock_scores import Automation, BAR, Clip, Note, PPQ, Point, Project, Track


PROFILE = {'id': 'g02_spark_switch', 'title': '断电火花', 'genre': '短延音失真 / 和弦扫弦摇滚',
           'key': 'E小调', 'bpm': 128, 'bars': 32, 'guitar_lead': True,
           'description': '电吉他主旋律＋正反向和弦扫弦，Bass和鼓伴奏；延音36，逐声部短包络约561ms归零。带停顿、独奏与齐奏收尾；无钢琴、小提琴。'}
FORM = [(0, 4, '引子'), (4, 12, '主歌'), (12, 20, '副歌'), (20, 24, '停顿间奏'),
        (24, 28, '独奏'), (28, 30, '副歌再现'), (30, 32, '尾声')]
VOICINGS = {'Em': [40, 47, 55, 64], 'C': [48, 55, 60, 64], 'G': [43, 50, 59, 67],
            'D': [50, 57, 62, 66], 'Am': [45, 52, 60, 64], 'B': [47, 54, 63, 66]}
VERSE = ['Em', 'Em', 'C', 'D', 'Em', 'G', 'Am', 'B']
CHORUS = ['C', 'D', 'Em', 'G', 'C', 'D', 'Am', 'B']
HOOK = [[76, 79, 78, 74], [78, 81, 78, 74], [79, 76, 83, 79], [79, 83, 81, 79],
        [76, 79, 72, 76], [78, 81, 74, 78], [81, 79, 76, 72], [75, 78, 81, 71]]
SOLO = [[76, 79, 81, 79, 76, 74, 71, 74], [72, 76, 79, 76, 74, 72, 67, 72],
        [74, 78, 81, 78, 76, 74, 69, 74], [75, 78, 81, 83, 81, 78, 75, 71]]


def compose_short_rock(profile=PROFILE):
    roles = [('guitar', '电吉他·主旋律与独奏', 100), ('guitar', '电吉他·正反向和弦扫弦', 88),
             ('guitar', '电吉他·低弦短Riff', 82), ('bass', 'Bass·根音推进', 87),
             ('drums', '鼓·底鼓军鼓', 100), ('drums', '鼓·镲片与过门', 78)]
    tracks = [Track(instrument, name, level, id=f'{profile["id"]}-track-{index}')
              for index, (instrument, name, level) in enumerate(roles)]

    def emit(track_index, bar, beat, duration, pitch, velocity, offset=0, label=''):
        track = tracks[track_index]
        if not track.clips or track.clips[-1].start != bar * BAR:
            section = next(section for first, last, section in FORM if first <= bar < last)
            track.clips.append(Clip(section + (' · ' + label if label else ''), bar * BAR, BAR,
                                    id=f'{profile["id"]}-clip-{track_index}-{bar}'))
        clip = track.clips[-1]
        start = round(beat * PPQ) + offset
        clip.notes.append(Note(start, min(round(duration * PPQ), BAR - start), pitch, velocity,
                               id=f'{clip.id}-note-{len(clip.notes)}'))

    def strum(bar, beat, chord, up=False, velocity=85):
        pitches = list(reversed(VOICINGS[chord])) if up else VOICINGS[chord]
        for index, pitch in enumerate(pitches):
            emit(1, bar, beat, .55, pitch, velocity - index * 3, index * 18,
                 f'{chord} ' + ('上扫' if up else '下扫'))

    for bar in range(31):
        first, last, section = next(item for item in FORM if item[0] <= bar < item[1])
        position = bar - first
        strong = section in ('副歌', '副歌再现')
        chord = 'Em' if section == '尾声' else (CHORUS if strong else VERSE)[position % 8]
        root = VOICINGS[chord][0]
        if section == '尾声':
            strum(bar, .25, 'Em', velocity=87)
            emit(0, bar, .75, .6, 76, 96)
            emit(3, bar, .25, .5, 28, 81)
            emit(4, bar, .25, .1, 0, 94)
            emit(5, bar, .25, .1, 5, 58)
            continue
        strum(bar, .25, chord, velocity=88 if strong else 76)
        if section != '停顿间奏' and (section != '引子' or position >= 2):
            strum(bar, 2.25 if strong else 2.75, chord, up=True, velocity=79 if strong else 70)
        if section != '停顿间奏':
            for beat in (1.5, 3.5):
                emit(2, bar, beat, .22, root, 82 if beat == 1.5 else 72)

        if section == '独奏':
            for pulse, pitch in enumerate(SOLO[position % 4]):
                emit(0, bar, .125 + pulse * .5, .34, pitch, 98 - pulse % 3 * 4)
        elif strong:
            for pulse, pitch in enumerate(HOOK[position % 8]):
                emit(0, bar, (.5, 1.5, 2.5, 3.25)[pulse], (.48, .45, .45, .55)[pulse], pitch, 100 - pulse % 2 * 5)
        elif section == '停顿间奏':
            for beat, pitch in ((.5, root + 24), (1.25, root + 19)):
                emit(0, bar, beat, .35, min(83, pitch), 96)
        elif section == '主歌':
            phrase = HOOK[position % 8]
            for pulse, beat in enumerate((.5, 1.25, 2.0, 3.25)):
                emit(0, bar, beat, .42, phrase[(pulse + 2) % 4] - (12 if position < 4 else 0), 95 - pulse % 2 * 5)

        if section == '引子' and position < 2:
            continue
        bass_root = root - 12
        bass_beats = (.25, 1.5, 2.25, 3.5) if section != '停顿间奏' else (.25, 1.25)
        for pulse, beat in enumerate(bass_beats):
            emit(3, bar, beat, .45, bass_root + (7 if pulse == 3 else 0), 84 - pulse % 2 * 8)
        kicks = (.25, 1.75, 2.25, 2.75) if strong else (.25, 2.25, 2.75)
        snares = (1, 3)
        hats = tuple(pulse * .5 for pulse in range(8))
        if section == '停顿间奏':
            kicks, snares, hats = (.25,), (1,), (0, .5, 1, 1.5)
        for beat in kicks:
            emit(4, bar, beat, .1, 0, 99 if strong else 91)
        for beat in snares:
            emit(4, bar, beat, .1, 1, 103 if strong else 93, 6)
        for pulse, beat in enumerate(hats):
            emit(5, bar, beat, .1, 3 if strong and pulse == 7 else 2, 48 if pulse % 2 == 0 else 32)
        if position % 4 == 0 and section != '停顿间奏':
            emit(5, bar, 0, .1, 5, 57)
        if position % 4 == 3 and section != '停顿间奏':
            for pulse, voice in enumerate((9, 8, 7)):
                emit(5, bar, 3.25 + pulse * .25, .1, voice, 58 + pulse * 7)

    project = Project(profile['title'] + ' · 短延音失真与和弦扫弦', bpm=128, bars=32,
                      tracks=tracks, loop_end=32 * BAR, guitar_sustain=36)
    project.parameters.update({'bus.guitar': 94, 'bus.bass': 54, 'bus.drums': 58,
        'bus.piano': 0, 'bus.violin': 0, 'guitar.amp': 3, 'guitar.drive': 64,
        'guitar.tone': 49, 'guitar.level': 56, 'guitar.mix': 127, 'guitar.cabinet': 1,
        'guitar.gate': 1, 'guitar.threshold': 18, 'guitar.compressor': 0,
        'guitar.modulation': 0, 'space.chorus_mix': 0, 'space.delay_mix': 0,
        'space.delay_time': 30, 'space.delay_feedback': 0})
    for target in ('bus.guitar', 'bus.bass', 'bus.drums', 'bus.piano', 'bus.violin'):
        points = [Point(first * BAR, round(project.parameters[target] *
                  (.88 if section == '引子' else 1.04 if section in ('副歌', '副歌再现') else .94)))
                  for first, last, section in FORM]
        points.extend((Point(31 * BAR, points[-1].value), Point(32 * BAR - PPQ // 2, 0)))
        project.automation.append(Automation(target, 'linear', points))
    return project.validate()
