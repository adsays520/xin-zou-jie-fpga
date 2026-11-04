"""Deterministic circle/slider charts and clock-independent rhythm judgement."""
from bisect import bisect_left, bisect_right
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import math

from arrangement_model import BAR, PPQ, Clip, Note, Project, Track, Automation, Point, pitch_name
from arrangement_playback import score_notes
from melody_player import note_frame


DIFFICULTIES = {'入门': (.48, 1.65, .055), '标准': (.28, 1.35, .046), '挑战': (.16, 1.05, .039)}
WINDOWS = ((.045, 300, 'PERFECT'), (.100, 100, 'GOOD'), (.160, 50, 'OK'))
MISS_WINDOW = .160


@dataclass(frozen=True)
class Target:
    id: int
    at: float
    x: float
    y: float
    duration: float = 0
    control: tuple = ()
    tail: tuple = ()
    notes: tuple = ()
    string: int = 0
    label: str = ''

    @property
    def slider(self):
        return self.duration > 0

    def position(self, progress):
        if not self.slider:
            return self.x, self.y
        t = max(0., min(1., progress))
        a, b = self.control
        c, d = self.tail
        return ((1-t)**2*self.x + 2*(1-t)*t*a + t*t*c,
                (1-t)**2*self.y + 2*(1-t)*t*b + t*t*d)


@dataclass(frozen=True)
class Chart:
    name: str
    instrument: str
    targets: tuple
    duration: float
    bpm: int
    difficulty: str
    approach: float
    radius: float
    fingerprint: str
    source_count: int = 0


def make_chart(project, track_id, difficulty='标准', sliders=True):
    project.validate()
    if difficulty not in DIFFICULTIES:
        raise ValueError('未知难度')
    track = next((track for track in project.active_tracks() if track.id == track_id), None)
    if track is None:
        raise ValueError('请选择一条未静音且有音符的目标轨道')
    selected = deepcopy(project)
    selected.tracks = [deepcopy(track)]
    notes = score_notes(selected)
    if not notes:
        raise ValueError('目标轨道没有音符')
    spacing, approach, radius = DIFFICULTIES[difficulty]
    seconds = 60 / project.bpm / PPQ
    groups = {}
    for note in notes:
        groups.setdefault(note.start, []).append(note)
    groups = sorted(groups.items())
    chosen = []
    for tick, group in groups:
        if not chosen or (tick-chosen[-1][0])*seconds >= spacing - 1e-9:
            chosen.append((tick, tuple(group)))
    if len(chosen) > 5000:
        raise ValueError('谱面超过5000个目标，请降低难度或缩短工程')
    targets = []
    for index, (tick, group) in enumerate(chosen):
        # Pitch contour and alternating arcs keep the generated map reproducible.
        pitch = max(note.pitch for note in group)
        x = .19 + .62 * (.5 + .5 * math.sin(index * 1.21))
        y = .13 + .38 * (.5 + .5 * math.sin(index * .83 + pitch * .13))
        at = tick * seconds
        next_at = chosen[index+1][0]*seconds if index+1 < len(chosen) else project.length*seconds
        length = min(min(note.end for note in group)*seconds-at, next_at-at-.20, 1.30)
        duration = length if sliders and index % 3 == 1 and length >= .55 else 0
        tail = (max(.13, min(.87, x + (.18 if index % 2 else -.18))),
                max(.10, min(.55, y + (.09 if index % 3 else -.09))))
        control = ((x+tail[0])/2, max(.08, min(.57, y-.10)))
        string = 0
        if track.instrument in ('guitar', 'bass'):
            string = note_frame(2 if track.instrument == 'bass' else 0, group[0].pitch, 80, True)[2]
        label = f'{string}弦 · {pitch_name(group[0].pitch)}' if string else (
            f'鼓 {group[0].pitch + 1}' if track.instrument == 'drums' else pitch_name(group[0].pitch))
        targets.append(Target(index, at, x, y, duration, control, tail, group, string, label))
    signature = repr((project.bpm, track.instrument, difficulty, sliders,
        [(t.at, t.duration, t.x, t.y, [(n.pitch, n.velocity) for n in t.notes]) for t in targets]))
    return Chart(project.name, track.instrument, tuple(targets), project.length*seconds,
                 project.bpm, difficulty, approach, radius, hashlib.sha256(signature.encode()).hexdigest(), len(groups))


@dataclass(frozen=True)
class Judgement:
    target: Target
    score: int
    text: str
    error_ms: float
    at: float


class Session:
    def __init__(self, chart, offset_ms=0, assist=False, autoplay=False):
        if not -250 <= offset_ms <= 250:
            raise ValueError('输入校准范围为-250..250ms')
        self.chart, self.offset, self.assist, self.autoplay = chart, offset_ms/1000, assist, autoplay
        self.done, self.holding = {}, {}
        self.score = self.combo = self.max_combo = 0
        self.hp = 100.
        self.counts = Counter()
        self.recent = []
        self.last_time = -math.inf
        self._miss_index = 0
        self._times = tuple(target.at for target in chart.targets)

    @property
    def accuracy(self):
        return 100. * sum(j.score for j in self.done.values()) / (300*len(self.done)) if self.done else 100.

    @property
    def finished(self):
        return len(self.done) == len(self.chart.targets)

    def _judge(self, target, points, error, now):
        if target.id in self.done:
            return None
        text = {300: 'PERFECT', 100: 'GOOD', 50: 'OK', 0: 'MISS'}[points]
        result = Judgement(target, points, text, error, now)
        self.done[target.id] = result
        self.holding.pop(target.id, None)
        self.counts[text] += 1
        self.combo = self.combo+1 if points else 0
        self.max_combo = max(self.combo, self.max_combo)
        self.score += points * (1+min(self.combo, 100)//10)
        self.hp = max(0., min(100., self.hp + (2 if points else -8)))
        self.recent.append(result)
        self.recent = self.recent[-40:]
        return result

    def tap(self, now, position=None, string=0):
        """One input consumes at most one target; no credit for early spam."""
        if self.autoplay:
            return None
        adjusted = now-self.offset
        candidates = []
        for target in self.visible(adjusted):
            if target.id in self.done or target.id in self.holding:
                continue
            error = adjusted-target.at
            if abs(error) > MISS_WINDOW + 1e-9:
                continue
            if string and target.string and string != target.string:
                continue
            if not self.assist and (position is None or math.dist(position, (target.x, target.y)) > self.chart.radius):
                continue
            candidates.append((abs(error), target.at, target))
        if not candidates:
            return None
        target = min(candidates, key=lambda item: item[:2])[2]
        error = adjusted-target.at
        points = next(points for limit, points, _ in WINDOWS if abs(error) <= limit+1e-9)
        if target.slider and not self.assist:
            self.holding[target.id] = [target, points, error*1000, 0., max(target.at, adjusted)]
            return Judgement(target, points, 'HOLD', error*1000, adjusted)
        return self._judge(target, points, error*1000, adjusted)

    def advance(self, now, position=None, pressed=False):
        """Rendering may skip frames; judgements use absolute song time."""
        if now < self.last_time:
            return []
        self.last_time = now
        emitted = []
        if self.autoplay:
            for target in self.visible(now):
                if target.at <= now and target.id not in self.done and target.id not in self.holding:
                    if target.slider:
                        self.holding[target.id] = [target, 300, 0., 0., target.at]
                    else:
                        emitted.append(self._judge(target, 300, 0., target.at))
        for key, holding in tuple(self.holding.items()):
            target, points, error, good, previous = holding
            end = target.at+target.duration
            instant = min(now, end)
            dt = max(0., instant-previous)
            wanted = target.position((instant-target.at)/target.duration)
            follows = self.autoplay or (pressed and position is not None and math.dist(position, wanted) <= self.chart.radius*1.8)
            if follows:
                good += dt if self.autoplay else min(dt, .080)  # a stalled UI cannot award unobserved tracking
            holding[3], holding[4] = good, max(previous, instant)
            if now >= end:
                coverage = good/target.duration
                value = points if coverage >= .8 else min(points, 100) if coverage >= .5 else 0
                emitted.append(self._judge(target, value, error, now))
        while self._miss_index < len(self.chart.targets):
            target = self.chart.targets[self._miss_index]
            if target.at+MISS_WINDOW >= now-self.offset:
                break
            self._miss_index += 1
            if target.id not in self.done and target.id not in self.holding:
                emitted.append(self._judge(target, 0, MISS_WINDOW*1000, now))
        return [item for item in emitted if item is not None]

    def visible(self, now):
        a = bisect_left(self._times, now-1.65)
        b = bisect_right(self._times, now+self.chart.approach)
        return self.chart.targets[a:b]

    def summary(self):
        return {'score': self.score, 'accuracy': round(self.accuracy, 3), 'max_combo': self.max_combo,
                'counts': dict(self.counts), 'objects': len(self.chart.targets), 'judged': len(self.done),
                'chart_sha256': self.chart.fingerprint, 'autoplay': self.autoplay}


def training_project():
    """An original 8-bar phrase: clear beats, sustained notes and quiet ensemble."""
    melody = [Track('guitar', '01 星轨练习·吉他主旋律', 90, id='rhythm-guitar'),
              Track('piano', '02 钢琴和弦', 65, id='rhythm-piano'),
              Track('bass', '03 Bass', 70, id='rhythm-bass'),
              Track('drums', '04 鼓组', 90, id='rhythm-drums')]
    chords = [(50, 57, 65), (46, 53, 62), (53, 60, 65), (48, 55, 64)]
    tunes = [(62, 65, 67, 69), (70, 69, 67, 65), (69, 72, 74, 72), (67, 65, 64, 62)]
    for bar in range(7):
        clips = [Clip(f'第{bar+1}小节', bar*BAR, BAR, id=f'rhythm-{i}-{bar}') for i in range(4)]
        melody[0].clips.append(clips[0])
        if bar in (1, 3, 5):
            attacks = [(0, tunes[bar%4][0], PPQ*3//2), (2*PPQ, tunes[bar%4][2], PPQ*3//2)]
        else:
            attacks = [(beat*PPQ, pitch, PPQ*3//4) for beat, pitch in enumerate(tunes[bar%4])]
        for index, (start, pitch, duration) in enumerate(attacks):
            clips[0].notes.append(Note(start, duration, pitch, 95, id=f'rhythm-lead-{bar}-{index}'))
        for i in range(1, 4):
            melody[i].clips.append(clips[i])
        for index, pitch in enumerate(chords[bar%4]):
            clips[1].notes.append(Note(0, 3*PPQ, pitch, 66, id=f'rhythm-chord-{bar}-{index}'))
        for beat in (0, 2):
            clips[2].notes.append(Note(beat*PPQ, PPQ, chords[bar%4][0]-12, 74, id=f'rhythm-bass-{bar}-{beat}'))
        for beat in range(4):
            clips[3].notes.append(Note(beat*PPQ, PPQ//4, 0 if beat%2==0 else 1, 90, id=f'rhythm-drum-{bar}-{beat}'))
    project = Project('星轨练习 · 原创音游入门', bpm=108, bars=8, tracks=melody, loop_end=8*BAR, guitar_sustain=48)
    project.parameters.update({'bus.guitar': 44, 'bus.piano': 24, 'bus.bass': 27, 'bus.drums': 40,
                               'bus.violin': 0, 'guitar.amp': 0, 'guitar.level': 64,
                               'space.delay_mix': 0, 'space.delay_feedback': 0})
    for target in ('bus.guitar', 'bus.piano', 'bus.bass', 'bus.drums'):
        amount = project.parameters[target]
        project.automation.append(Automation(target, 'linear', [Point(0, amount), Point(7*BAR, amount), Point(8*BAR-PPQ//2, 0)]))
    return project.validate()
