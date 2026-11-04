from collections import Counter, deque
from copy import deepcopy
import csv
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
BASE = APP.parent
sys.path[:0] = [str(APP), str(BASE / 'host'), str(BASE / 'tools/python_deps')]

from arrangement_model import Automation, BAR, Clip, Note, PPQ, Point, Project, Track
from arrangement_playback import compile_plan, score_notes


CHORDS = {
    'Dm9': (38, [57, 60, 64, 65], [50, 57, 60, 64, 65]),
    'Bbmaj7': (34, [57, 62, 65, 70], [46, 53, 57, 62, 65]),
    'Fmaj9': (29, [57, 60, 64, 67], [45, 53, 57, 60, 67]),
    'Cadd9': (36, [55, 60, 62, 64], [48, 55, 60, 62, 64]),
    'Gm9': (31, [57, 58, 62, 65], [43, 50, 57, 58, 62]),
    'A7': (33, [55, 61, 64, 69], [45, 52, 55, 61, 64]),
}
HARMONY = (
    ['Dm9', 'Bbmaj7', 'Fmaj9', 'A7']
    + ['Dm9', 'Bbmaj7', 'Fmaj9', 'Cadd9', 'Dm9', 'Gm9', 'Bbmaj7', 'A7'] * 2
    + ['Gm9', 'Dm9', 'Bbmaj7', 'A7']
    + ['Dm9', 'Bbmaj7', 'Fmaj9', 'Cadd9', 'Gm9', 'A7', 'Dm9', 'Dm9']
)
SECTIONS = [(0, 4, 'Intro / 夜色'), (4, 12, 'A / 行进'), (12, 20, 'B / 展开'),
            (20, 24, 'Break / 留白'), (24, 30, 'B2 / 回归'), (30, 32, 'Coda / 落地')]
VERSE = [
    [(0, 74, 1), (1.25, 77, .5), (2, 76, .5), (2.75, 74, .625), (3.5, 69, .375)],
    [(0, 70, .625), (.75, 74, .75), (1.75, 77, 1.25), (3.25, 76, .5)],
    [(0, 77, 1.25), (1.5, 76, .5), (2.25, 72, .75), (3.25, 69, .5)],
    [(0, 72, 1.5), (1.75, 74, .5), (2.5, 76, .5), (3.5, 72, .375)],
    [(0, 69, .5), (.75, 74, 1), (2, 77, .5), (2.75, 81, 1)],
    [(0, 79, 1.5), (1.75, 77, .5), (2.5, 74, 1)],
    [(.25, 77, .75), (1.25, 74, .5), (2, 70, .75), (3.25, 69, .5)],
    [(0, 73, .5), (.75, 76, .5), (1.5, 79, .5), (2.25, 81, .75), (3.25, 73, .375)],
]
CHORUS = [
    [(0, 81, 1.375), (1.5, 77, .375), (2, 76, .5), (2.75, 77, .375), (3.5, 74, .375)],
    [(0, 82, .625), (.75, 81, .75), (1.75, 77, 1.75)],
    [(0, 81, .75), (1, 84, .75), (2, 81, .5), (2.75, 77, 1)],
    [(0, 79, 1.5), (1.75, 76, .5), (2.5, 74, .5), (3.25, 72, .5)],
    [(0, 77, .75), (1, 81, .75), (2, 86, 1.5)],
    [(0, 82, 1), (1.25, 81, .5), (2, 79, .5), (2.75, 77, .75)],
    [(0, 81, .75), (1, 77, .75), (2, 74, 1), (3.25, 77, .5)],
    [(0, 76, .5), (.75, 73, .5), (1.5, 76, .5), (2.25, 79, .75), (3.25, 81, .5)],
]


def section_at(bar):
    return next(label for first, last, label in SECTIONS if first <= bar < last)


def create_project():
    definitions = [
        ('piano', '01 Piano / 和声铺底', 93),
        ('piano', '02 Piano / 高音回答', 82),
        ('guitar', '03 Guitar / 指弹流动', 87),
        ('guitar', '04 Guitar / 扫弦切分', 82),
        ('bass', '05 Bass / 根音与经过音', 100),
        ('violin', '06 Violin / 主旋律', 96),
        ('drums', '07 Drums / 底鼓军鼓', 100),
        ('drums', '08 Drums / 镲片律动', 94),
        ('drums', '09 Drums / 加花与转场', 95),
    ]
    tracks = [Track(instrument, name, level, id=f'track-{index:02d}')
              for index, (instrument, name, level) in enumerate(definitions)]

    def clip_for(track_index, bar):
        track = tracks[track_index]
        if not track.clips or track.clips[-1].start != bar * BAR:
            track.clips.append(Clip(f'{section_at(bar).split(" / ")[0]} · {HARMONY[bar]}',
                                    bar * BAR, BAR, id=f'clip-{track_index:02d}-{bar:02d}'))
        return track.clips[-1]

    def add(track_index, bar, beat, duration, pitch, velocity, offset=0):
        clip = clip_for(track_index, bar)
        start = max(0, min(BAR - 1, round(beat * PPQ) + offset))
        ticks = max(1, min(round(duration * PPQ), BAR - start))
        clip.notes.append(Note(start, ticks, pitch, max(1, min(127, velocity)),
                               id=f'note-{track_index:02d}-{bar:02d}-{len(clip.notes):03d}'))

    def piano_chord(bar, beat, duration, pitches, strength):
        for index, pitch in enumerate(pitches):
            add(0, bar, beat, duration, pitch, strength + index * 2, index * 4)

    for bar, chord in enumerate(HARMONY):
        root, piano, guitar = CHORDS[chord]
        loud = 12 <= bar < 20 or 24 <= bar < 30
        quiet = bar < 4 or 20 <= bar < 24
        if bar == 31:
            continue
        if bar == 30:
            piano_chord(bar, 0, 2.5, [50, 57, 60, 64, 65, 74], 78)
            for index, pitch in enumerate(guitar):
                add(3, bar, 0, 2.25, pitch, 85 - index * 3, index * 10)
            add(4, bar, 0, 2, 38, 89)
            add(5, bar, 0, 2.75, 74, 90)
            add(6, bar, 0, .125, 0, 96)
            add(8, bar, 0, .25, 5, 68)
            continue

        if quiet:
            piano_chord(bar, 0, 2.75, piano, 60 if bar < 4 else 68)
        else:
            voicing = list(piano)
            if bar % 2:
                voicing = voicing[1:] + [voicing[0] + 12]
            piano_chord(bar, 0, 1.25, voicing, 74 if loud else 65)
            piano_chord(bar, 2.5, .9, voicing[1:], 68 if loud else 59)
        if bar % 4 == 3 or 20 <= bar < 24:
            answer = [piano[-1] + 12, piano[-2] + 12, piano[1] + 24]
            for index, pitch in enumerate(answer):
                add(1, bar, 2.5 + index * .5, .375, pitch, 72 + index * 3)

        arp_beats = (0, 1, 2, 3) if loud else tuple(index * .5 for index in range(8))
        if quiet and bar >= 20:
            arp_beats = (0, 1.5, 2.5)
        order = (0, 2, 3, 4, 2, 1, 3, 2)
        for index, beat in enumerate(arp_beats):
            pitch = guitar[order[(index + (bar % 2) * 2) % len(order)]]
            add(2, bar, beat, .375, pitch, (61 if quiet else 72) + (6 if index % 4 == 0 else 0),
                8 if index % 2 else 0)
        if loud or (bar >= 4 and not quiet):
            for beat, selection, strength in ((0, guitar, 84), (1.5, guitar[2:], 67),
                                               (2.75, guitar[1:], 75), (3.5, guitar[2:], 62)):
                if not loud and beat not in (0, 2.75):
                    continue
                pitches = selection if beat != 3.5 else list(reversed(selection))
                for index, pitch in enumerate(pitches):
                    add(3, bar, beat, .375, pitch, strength - index * 3, index * 9)

        if bar >= 2:
            bass_pattern = [(0, root, .875, 97)]
            if not quiet:
                bass_pattern += [(1.5, root + 7, .375, 76), (2.25, root + 12, .625, 86),
                                 (3.5, root, .375, 82)]
                if bar % 4 == 3:
                    following = CHORDS[HARMONY[bar + 1]][0]
                    approach = following - 1 if following > root else following + 1
                    bass_pattern.append((3.875, max(28, approach), .1, 67))
            elif bar >= 20:
                bass_pattern.append((2.5, root + 7, .75, 71))
            for beat, pitch, duration, strength in bass_pattern:
                add(4, bar, beat, duration, pitch, strength)

        if 4 <= bar < 12:
            melody = VERSE[bar - 4]
        elif 12 <= bar < 20:
            melody = CHORUS[bar - 12]
        elif 24 <= bar < 28:
            melody = CHORUS[bar - 24]
        elif bar == 28:
            melody = [(0, 79, .75), (1, 82, .75), (2, 81, .5), (2.75, 77, .875)]
        elif bar == 29:
            melody = [(0, 76, .5), (.75, 73, .5), (1.5, 76, .5), (2.25, 81, 1.25)]
        elif bar in (2, 3, 20, 22):
            melody = {2: [(2, 77, 1.5)], 3: [(1, 76, 1), (2.5, 73, 1)],
                      20: [(0, 79, 2.5)], 22: [(1, 77, 2.5)]}[bar]
        else:
            melody = []
        for index, (beat, pitch, duration) in enumerate(melody):
            strength = (96 if loud else 80) + (5 if index == 0 else -(index % 5))
            add(5, bar, beat, duration, pitch, strength)

        if bar < 2:
            kicks, snares = ((0,), ())
        elif quiet:
            kicks, snares = ((0, 2.5), (1, 3))
        elif loud:
            kicks, snares = ((0, .75, 1.5, 2, 2.75, 3.5), (1, 3))
        else:
            kicks, snares = ((0, 1.75, 2.5, 3.5) if bar % 2 else (0, 1.75, 2.5), (1, 3))
        for beat in kicks:
            add(6, bar, beat, .125, 0, 108 if loud and beat in (0, 2) else 94)
        for beat in snares:
            add(6, bar, beat, .125, 10 if quiet else 1, 62 if quiet else 106 if loud else 94, 6)
        if not quiet:
            add(6, bar, 2.75, .125, 1, 36 + bar % 7, 10)
        subdivisions = 16 if loud else 4 if 20 <= bar < 24 else 8
        for index in range(subdivisions):
            beat = index * 4 / subdivisions
            if (loud and index == 14) or (not quiet and subdivisions == 8 and index == 7):
                voice = 3
            else:
                voice = 6 if loud and bar % 4 == 2 and index % 4 == 0 else 2
            strength = (63 if index % (subdivisions // 4) == 0 else 39) + (8 if loud else 0)
            add(7, bar, beat, .1, voice, strength + (bar + index) % 7,
                12 if index % 2 else 0)
        if bar in (4, 12, 16, 24, 28):
            add(8, bar, 0, .25, 5, 82 if loud else 65)
        if loud:
            add(8, bar, 3, .125, 4, 61, 12)
        if bar in (3, 7, 11, 15, 19, 23, 27, 29):
            for index, voice in enumerate((9, 9, 8, 7)):
                add(8, bar, 3 + index * .25, .125, voice, 58 + index * 9 + (8 if loud else 0))

    project = Project('霓虹航线 Neon Runway · 五乐器合奏', bpm=96, bars=32,
                      tracks=tracks, loop_start=0, loop_end=32 * BAR)
    project.parameters.update({
        'bus.guitar': 72, 'bus.piano': 64, 'bus.drums': 60, 'bus.violin': 0, 'bus.bass': 0,
        'space.chorus_mix': 8, 'space.chorus_rate': 26, 'space.chorus_depth': 27,
        'space.delay_mix': 10, 'space.delay_time': 90, 'space.delay_feedback': 24,
        'guitar.amp': 0, 'guitar.drive': 25, 'guitar.tone': 58, 'guitar.level': 82,
        'guitar.mix': 127, 'guitar.cabinet': 0, 'guitar.gate': 0, 'guitar.compressor': 0,
        'guitar.modulation': 0,
    })
    specifications = {
        'bus.guitar': [(0, 72), (4, 81), (12, 88), (20, 67), (24, 87), (30, 80)],
        'bus.piano': [(0, 64), (4, 72), (12, 79), (20, 73), (24, 80), (30, 75)],
        'bus.bass': [(0, 0), (1.75, 0), (2, 77), (4, 84), (12, 89), (20, 72), (24, 88), (30, 81)],
        'bus.violin': [(0, 0), (1.75, 0), (2, 74), (4, 89), (12, 98), (20, 76), (24, 98), (30, 88)],
        'bus.drums': [(0, 54), (2, 65), (4, 78), (12, 87), (20, 58), (24, 86), (30, 72)],
        'space.delay_mix': [(0, 10), (4, 13), (12, 18), (20, 22), (24, 16), (30, 21)],
    }
    for target, values in specifications.items():
        points = [Point(round(bar * BAR), value) for bar, value in values]
        points += [Point(31 * BAR, points[-1].value), Point(32 * BAR - PPQ // 2, 0)]
        project.automation.append(Automation(target, 'linear', points))
    project.automation.append(Automation('space.chorus_mix', 'step',
        [Point(0, 8), Point(12 * BAR, 13), Point(20 * BAR, 7), Point(24 * BAR, 12), Point(31 * BAR, 6)]))
    return project.validate()


def excerpt(project, first_bar=24, bars=8):
    result = deepcopy(project)
    first, end = first_bar * BAR, (first_bar + bars) * BAR
    result.name = '霓虹航线 · 20秒高潮与收束试听'
    result.bars, result.loop_start, result.loop_end = bars, 0, bars * BAR
    for track in result.tracks:
        track.clips = [clip for clip in track.clips if first <= clip.start < end]
        for clip in track.clips:
            clip.start -= first
    for lane in result.automation:
        baseline = lane.value_at(first, result.parameters[lane.target])
        result.parameters[lane.target] = baseline
        lane.points = [Point(point.tick - first, point.value) for point in lane.points if first <= point.tick <= end]
        if not lane.points or lane.points[0].tick != 0:
            lane.points.insert(0, Point(0, baseline))
    return result.validate()


def analyze(project):
    plan = compile_plan(project, hardware=True, ensemble=True)
    notes = score_notes(project)
    active = Counter()
    peak = Counter()
    simultaneous_engines = 0
    for tick, on, identifier, note in sorted(
            [(note.start, 1, note.id, note) for note in notes]
            + [(note.end, 0, note.id, note) for note in notes]):
        active[note.instrument] += 1 if on else -1
        peak[note.instrument] = max(peak[note.instrument], active[note.instrument])
        simultaneous_engines = max(simultaneous_engines, sum(value > 0 for value in active.values()))
    window = deque()
    pending = maximum = 0
    for event in plan.events:
        while window and window[0][0] <= event.at - .1:
            pending -= window.popleft()[1]
        window.append((event.at, len(event.data)))
        pending += len(event.data)
        maximum = max(maximum, pending)
        for offset in range(0, len(event.data), 6):
            frame = event.data[offset:offset + 6]
            assert len(frame) == 6 and frame[0] == 0xa5
            checksum = 0
            for value in frame:
                checksum ^= value
            assert checksum == 0
    tails = {}
    for instrument, seconds in (('guitar', 1.4), ('bass', 3.0)):
        attacks = [note.start * 60 / (project.bpm * PPQ) for note in notes if note.instrument == instrument]
        recent = deque()
        highest = 0
        for attack in attacks:
            while recent and recent[0] <= attack - seconds:
                recent.popleft()
            recent.append(attack)
            highest = max(highest, len(recent))
        tails[instrument] = {'assumed_seconds': seconds, 'peak_attacks_in_window': highest}
    return {
        'hardware_compilation_passed': True, 'duration_seconds': plan.duration,
        'tracks': len(project.tracks), 'notes': len(notes), 'scheduled_events': len(plan.events),
        'automation_lanes': len(project.automation), 'simultaneous_instrument_types': simultaneous_engines,
        'gated_peak_voices': dict(peak), 'maximum_bytes_per_100ms': maximum,
        'UART_budget_bytes_per_100ms': 864, 'tail_load_estimate_not_measured': tails,
        'notes_per_instrument': dict(Counter(note.instrument for note in notes)),
        'real_serial_connected': False, 'board_listening_validated': False,
    }


def main():
    project = create_project()
    short = excerpt(project)
    proof = {'generated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
             'passed': True, 'files': {}, 'sources': {}}
    for name, score in (('Neon_Runway_32bars.tang.json', project), ('Neon_Runway_8bars.tang.json', short)):
        destination = HERE / name
        score.save(destination)
        assert Project.load(destination) == score
        proof['files'][name] = {**analyze(score), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
    with (HERE / 'Neon_Runway_events.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream)
        writer.writerow(('bar_1based', 'beat_1based', 'instrument', 'pitch_or_drum_id', 'velocity', 'duration_beats'))
        for note in score_notes(project):
            writer.writerow((note.start // BAR + 1, round((note.start % BAR) / PPQ + 1, 4),
                             note.instrument, note.pitch, note.velocity, round((note.end - note.start) / PPQ, 4)))
    for path in (Path(__file__), APP / 'arrangement_model.py', APP / 'arrangement_playback.py',
                 APP / 'ensemble_protocol.py', APP / 'melody_player.py',
                 BASE / 'host/drum_patterns.py', BASE / 'host/guitar_effects.py', BASE / 'host/master_space_effects.py'):
        proof['sources'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    (HERE / 'validation.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(proof['files'], ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
