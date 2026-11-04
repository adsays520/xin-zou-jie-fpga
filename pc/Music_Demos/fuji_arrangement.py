"""Piano-led chamber arrangement of the user's 富士山下 piano PDF."""
from copy import deepcopy

from piano_scores import Automation, BAR, Clip, Note, PPQ, Point, Project, Track
from fuji_score import hand_notes


PROFILE = {
    'id': 'p04_fuji', 'title': '富士山下 · 钢琴吉他小提琴',
    'genre': '用户钢琴谱改编 / 三乐器抒情', 'key': 'F大调', 'bpm': 120, 'bars': 47,
    'piano_lead': True, 'guitar_lead': False, 'original': False,
    'gain_policy': 'piano-led-chamber',
    'description': '钢琴保留用户两页谱的右手旋律、装饰段与左手分解，加入干净吉他和少量小提琴回答。无鼓、无独立Bass；吉他延音48。',
    'mix_note': '已载入钢琴主导版：吉他和小提琴轻伴奏；无鼓与独立Bass。未自动连接或播放。',
    'attribution': '根据用户提供的《富士山下》两页钢琴PDF作本地器乐再编配；原PDF未标注编谱者。本工程新增吉他及小提琴伴奏。',
}


def normalized_piano():
    """A physical key cannot be held separately by two UART note IDs.

    Merge simultaneous unisons; re-articulation releases the previous gate
    one tick early. This prevents a stale left-hand Off killing a new melody.
    """
    notes = []
    for hand, velocity in (('right', 90), ('left', 66)):
        for original in hand_notes(hand):
            notes.append({**original, 'start_tick': round(original['start'] * PPQ / 4),
                          'end_tick': round(original['end'] * PPQ / 4), 'velocity': velocity})
    notes.sort(key=lambda note: (note['start_tick'], note['pitch'], note['hand'] != 'right'))
    merged = []
    for note in notes:
        if merged and (note['start_tick'], note['pitch']) == (merged[-1]['start_tick'], merged[-1]['pitch']):
            merged[-1]['end_tick'] = max(merged[-1]['end_tick'], note['end_tick'])
        else:
            merged.append(note.copy())
    by_pitch = {}
    for note in merged:
        by_pitch.setdefault(note['pitch'], []).append(note)
    for group in by_pitch.values():
        for previous, following in zip(group, group[1:]):
            if previous['end_tick'] > following['start_tick']:
                previous['end_tick'] = max(previous['start_tick'] + 1, following['start_tick'] - 1)
    return merged


def _emit(tracks, index, absolute_tick, duration, pitch, velocity, label):
    track = tracks[index]
    bar = absolute_tick // BAR
    clip = next((clip for clip in track.clips if clip.start == bar * BAR), None)
    if clip is None:
        clip = Clip(label, bar * BAR, BAR, id=f'p04-{index}-bar-{bar}')
        track.clips.append(clip)
    relative = absolute_tick - clip.start
    clip.length = max(clip.length, relative + duration)
    clip.notes.append(Note(relative, duration, pitch, velocity, id=f'{clip.id}-note-{len(clip.notes)}'))


def _guitar_register(pitch):
    while pitch < 45:
        pitch += 12
    while pitch > 69:
        pitch -= 12
    return pitch


def compose_fuji():
    roles = [('piano', '01 钢琴右手·主旋律与装饰', 100),
             ('piano', '02 钢琴左手·按谱分解', 84),
             ('guitar', '03 干净吉他·轻分解与扫弦', 73),
             ('violin', '04 小提琴·句间回答', 66)]
    tracks = [Track(instrument, title, level, id=f'p04-track-{index}')
              for index, (instrument, title, level) in enumerate(roles)]
    for note in normalized_piano():
        bar = note['start_tick'] // BAR
        if note['hand'] == 'right':
            velocity = 83 if bar < 9 else 92 if 26 <= bar < 41 else 88
            # The fast high-register introduction should sparkle, not dominate.
            if note['pitch'] >= 86:
                velocity -= 7
        else:
            velocity = 66 if bar < 9 else 63
        _emit(tracks, 0 if note['hand'] == 'right' else 1,
              note['start_tick'], note['end_tick'] - note['start_tick'],
              note['pitch'], velocity, f'谱第{bar + 1}小节 · 钢琴{note["hand"]}')

    left = hand_notes('left')
    for bar in range(9, 44):
        source = [note for note in left if note['start'] < (bar + 1) * 16 and note['end'] > bar * 16]
        if not source:
            continue
        # Use actual left-hand chord tones instead of guessing new harmonies.
        for pulse, beat in enumerate((.25, 2.25)):
            instant = bar * 16 + beat * 4
            candidates = [note for note in source if note['start'] <= instant]
            chosen = max(candidates, key=lambda note: note['start']) if candidates else source[0]
            _emit(tracks, 2, bar * BAR + round(beat * PPQ), round(.58 * PPQ),
                  _guitar_register(chosen['pitch']), 65 - pulse * 4, '吉他·按钢琴和声轻分解')
        if bar in (14, 18, 22, 26, 30, 34, 38, 42):
            late = [note for note in source if note['start'] >= bar * 16 + 8] or source
            tones = sorted({_guitar_register(note['pitch']) for note in late})[:3]
            for voice, pitch in enumerate(tones):
                _emit(tracks, 2, bar * BAR + round((3 + voice * .04) * PPQ), round(.52 * PPQ),
                      pitch, 59 - voice * 3, '吉他·低音量和弦扫弦')

        if bar in (13, 17, 21, 25, 29, 33, 37, 41, 43):
            # A single answering bow. No independent violin lead line is added.
            anchor = source[-1]['pitch']
            while anchor < 65:
                anchor += 12
            while anchor > 79:
                anchor -= 12
            _emit(tracks, 3, bar * BAR + round(1.75 * PPQ), round(1.65 * PPQ),
                  anchor, 47 if bar < 26 else 52, '小提琴·轻声回答')

    project = Project(PROFILE['title'], bpm=120, bars=47, tracks=tracks, loop_end=47 * BAR, guitar_sustain=48)
    project.parameters.update({'bus.piano': 52, 'bus.guitar': 18, 'bus.violin': 0,
        'bus.bass': 0, 'bus.drums': 0, 'guitar.amp': 0, 'guitar.drive': 0,
        'guitar.tone': 56, 'guitar.level': 64, 'guitar.mix': 127,
        'guitar.cabinet': 0, 'guitar.gate': 0, 'guitar.compressor': 0, 'guitar.modulation': 0,
        'space.chorus_mix': 0, 'space.delay_mix': 0, 'space.delay_time': 40, 'space.delay_feedback': 0})
    settings = {'bus.piano': [(0, 50), (9, 52), (26, 54), (41, 51), (44, 48)],
                'bus.guitar': [(0, 0), (9, 18), (26, 23), (41, 18), (44, 0)],
                'bus.violin': [(0, 0), (13, 11), (26, 15), (41, 12), (44, 0)],
                'bus.bass': [(0, 0)], 'bus.drums': [(0, 0)]}
    for target, values in settings.items():
        points = []
        previous = None
        for bar, value in values:
            tick = bar * BAR
            if previous is not None and tick:
                points.append(Point(tick - PPQ // 8, previous))
            points.append(Point(tick, value))
            previous = value
        points.extend((Point(46 * BAR, previous), Point(47 * BAR - PPQ // 2, 0)))
        project.automation.append(Automation(target, 'linear', points))
    return project.validate()


def fuji_short(project):
    """Printed bars 28..33 plus a two-bar arranged F-major resolution."""
    result = deepcopy(project)
    result.name = '富士山下 · 钢琴三重奏16秒试听'
    result.bars, result.loop_start, result.loop_end = 8, 0, 8 * BAR
    start, end = 27 * BAR, 33 * BAR
    for track in result.tracks:
        adjusted = []
        for clip in track.clips:
            selected = []
            for note in clip.notes:
                first, last = clip.start + note.start, clip.start + note.start + note.duration
                if start <= first < end:
                    selected.append(Note(first - start, min(last, end) - first,
                                         note.pitch, note.velocity, note.id))
            if selected:
                adjusted.extend(selected)
        track.clips = [Clip('短版·谱第28–33小节', 0, 6 * BAR, adjusted, id=f'{track.id}-excerpt')] if adjusted else []
    for lane in result.automation:
        amount = lane.value_at(start, result.parameters[lane.target])
        result.parameters[lane.target] = amount
        lane.points = [Point(0, amount), Point(7 * BAR, amount), Point(8 * BAR - PPQ // 2, 0)]
    for pitch in (65, 69, 72):
        _emit(result.tracks, 0, 6 * BAR, round(2.5 * PPQ), pitch, 77, '短版·F大调收束')
    for pitch in (41, 53):
        _emit(result.tracks, 1, 6 * BAR, round(2.5 * PPQ), pitch, 58, '短版·左手根音')
    for index, pitch in enumerate((53, 57, 60)):
        _emit(result.tracks, 2, 6 * BAR + round(index * .04 * PPQ), round(.55 * PPQ),
              pitch, 53 - index * 3, '短版·吉他落地')
    _emit(result.tracks, 3, 6 * BAR, round(1.8 * PPQ), 69, 40, '短版·小提琴轻收束')
    return result.validate()
