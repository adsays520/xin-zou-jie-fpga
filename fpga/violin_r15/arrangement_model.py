"""Editable musical events, independent of Tk, serial ports and audio synthesis."""
from copy import deepcopy
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import uuid


PPQ = 480
BAR = 4 * PPQ
FORMAT = 'tang-arrangement-v1'
INSTRUMENTS = {'guitar': '木吉他', 'piano': '钢琴', 'bass': 'Bass',
               'violin': '独奏小提琴', 'drums': '鼓组'}
COLORS = {'guitar': '#D38948', 'piano': '#368BD5', 'bass': '#168C85',
          'violin': '#8266BB', 'drums': '#CB6079'}
DRUM_NAMES = ('底鼓', '军鼓', '闭镲', '开镲', '拍手', '吊镲', '叮叮镲',
              '低通鼓', '中通鼓', '高通鼓', '边击', '牛铃')
PARAMETERS = {
    'bus.guitar': ('吉他/Bass 总线音量', 0, 127, 100),
    'bus.piano': ('钢琴总线音量', 0, 127, 100),
    'bus.drums': ('鼓总线音量', 0, 127, 100),
    'bus.violin': ('小提琴总线音量', 0, 127, 100),
    'bus.bass': ('v8 Bass独立总线音量', 0, 127, 100),
    'space.chorus_mix': ('总线合唱混合', 0, 127, 0),
    'space.chorus_rate': ('总线合唱速度', 0, 127, 40),
    'space.chorus_depth': ('总线合唱深度', 0, 127, 40),
    'space.delay_mix': ('总线延迟混合', 0, 127, 0),
    'space.delay_time': ('总线延迟时间', 0, 127, 42),
    'space.delay_feedback': ('总线延迟反馈', 0, 96, 35),
    'guitar.amp': ('吉他/Bass 箱头类型', 0, 10, 0),
    'guitar.drive': ('吉他/Bass 增益', 0, 127, 64),
    'guitar.tone': ('吉他/Bass 音色', 0, 127, 64),
    'guitar.level': ('吉他/Bass 效果音量', 0, 127, 80),
    'guitar.mix': ('吉他/Bass 干湿比', 0, 127, 127),
    'guitar.modulation': ('吉他/Bass 调制类型', 0, 5, 0),
    'guitar.rate': ('吉他/Bass 调制速度', 0, 127, 40),
    'guitar.depth': ('吉他/Bass 调制深度', 0, 127, 64),
    'guitar.threshold': ('吉他/Bass 噪声门阈值', 0, 127, 32),
    'guitar.cabinet': ('吉他/Bass 箱体开关', 0, 1, 0),
    'guitar.gate': ('吉他/Bass 噪声门开关', 0, 1, 0),
    'guitar.compressor': ('吉他/Bass 压缩开关', 0, 1, 0),
}
DISCRETE = {'guitar.amp', 'guitar.modulation', 'guitar.cabinet',
            'guitar.gate', 'guitar.compressor'}


def identity():
    return uuid.uuid4().hex


def integer(value, minimum, maximum, label):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{label}必须是 {minimum}..{maximum} 的整数')


def text_value(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 120:
        raise ValueError(f'{label}不能为空或超过120字')


def snap(tick, grid):
    return max(0, int(tick / grid + 0.5) * grid)


def pitch_name(pitch):
    return ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')[pitch % 12] + str(pitch // 12 - 1)


@dataclass
class Note:
    start: int = 0
    duration: int = PPQ
    pitch: int = 60
    velocity: int = 100
    id: str = field(default_factory=identity)


@dataclass
class Clip:
    name: str = '新片段'
    start: int = 0
    length: int = BAR
    notes: list = field(default_factory=list)
    id: str = field(default_factory=identity)


@dataclass
class Track:
    instrument: str = 'piano'
    name: str = '钢琴'
    level: int = 100
    muted: bool = False
    solo: bool = False
    clips: list = field(default_factory=list)
    id: str = field(default_factory=identity)


@dataclass
class Point:
    tick: int = 0
    value: int = 0


@dataclass
class Automation:
    target: str = 'space.delay_mix'
    interpolation: str = 'step'
    points: list = field(default_factory=list)

    def value_at(self, tick, fallback):
        previous = None
        for point in sorted(self.points, key=lambda item: item.tick):
            if point.tick > tick:
                if previous is None or self.interpolation == 'step' or self.target in DISCRETE:
                    return fallback if previous is None else previous.value
                ratio = (tick - previous.tick) / (point.tick - previous.tick)
                return round(previous.value + ratio * (point.value - previous.value))
            previous = point
        return fallback if previous is None else previous.value


@dataclass
class Project:
    name: str = '未命名编曲'
    bpm: int = 110
    bars: int = 8
    tracks: list = field(default_factory=list)
    automation: list = field(default_factory=list)
    parameters: dict = field(default_factory=lambda: {key: spec[3] for key, spec in PARAMETERS.items()})
    loop_start: int = 0
    loop_end: int = 4 * BAR
    format: str = FORMAT

    @property
    def length(self):
        return self.bars * BAR

    def active_tracks(self):
        solo = any(track.solo and not track.muted for track in self.tracks)
        return [track for track in self.tracks if not track.muted and track.level > 0 and (not solo or track.solo)]

    def validate(self):
        if self.format != FORMAT:
            raise ValueError('不支持的编曲格式')
        text_value(self.name, '工程名')
        integer(self.bpm, 30, 300, 'BPM')
        integer(self.bars, 1, 256, '小节数')
        integer(self.loop_start, 0, self.length - 1, '循环起点')
        integer(self.loop_end, self.loop_start + 1, self.length, '循环终点')
        if type(self.tracks) is not list or len(self.tracks) > 64:
            raise ValueError('轨道最多64条')
        identifiers = set()

        def unique(value):
            text_value(value, '事件ID')
            if value in identifiers:
                raise ValueError('事件ID重复')
            identifiers.add(value)

        note_count = 0
        for track in self.tracks:
            unique(track.id)
            text_value(track.name, '轨道名')
            if track.instrument not in INSTRUMENTS:
                raise ValueError('不支持的乐器')
            integer(track.level, 0, 127, '轨道力度比例')
            if type(track.muted) is not bool or type(track.solo) is not bool:
                raise ValueError('Mute/Solo必须为布尔值')
            if type(track.clips) is not list or len(track.clips) > 1024:
                raise ValueError('每轨片段最多1024个')
            for clip in track.clips:
                unique(clip.id)
                text_value(clip.name, '片段名')
                integer(clip.start, 0, self.length - 1, '片段起点')
                integer(clip.length, 1, self.length - clip.start, '片段长度')
                if type(clip.notes) is not list:
                    raise ValueError('音符必须为列表')
                note_count += len(clip.notes)
                if note_count > 20000:
                    raise ValueError('工程最多20000个音符')
                for note in clip.notes:
                    unique(note.id)
                    integer(note.start, 0, clip.length - 1, '音符起点')
                    integer(note.duration, 1, clip.length - note.start, '音符时值')
                    integer(note.pitch, 0, 11 if track.instrument == 'drums' else 127, '音高/鼓编号')
                    integer(note.velocity, 1, 127, '力度')
        if type(self.parameters) is not dict or set(self.parameters) != set(PARAMETERS):
            raise ValueError('效果器基础参数缺失或包含未知参数')
        for target, value in self.parameters.items():
            integer(value, PARAMETERS[target][1], PARAMETERS[target][2], target)
        if type(self.automation) is not list or len(self.automation) > len(PARAMETERS):
            raise ValueError('自动化轨道过多')
        targets = set()
        for lane in self.automation:
            if lane.target not in PARAMETERS or lane.target in targets:
                raise ValueError('自动化目标未知或重复')
            targets.add(lane.target)
            if lane.interpolation not in ('step', 'linear'):
                raise ValueError('插值必须为step或linear')
            if lane.target in DISCRETE and lane.interpolation != 'step':
                raise ValueError('开关与类型参数仅支持阶梯自动化')
            if type(lane.points) is not list or len(lane.points) > 4096:
                raise ValueError('自动化点过多')
            ticks = set()
            for point in lane.points:
                integer(point.tick, 0, self.length, '自动化时间')
                integer(point.value, PARAMETERS[lane.target][1], PARAMETERS[lane.target][2], '自动化值')
                if point.tick in ticks:
                    raise ValueError('同一参数同一时刻只能有一个自动化点')
                ticks.add(point.tick)
        return self

    def to_dict(self):
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        try:
            if not isinstance(data, dict):
                raise ValueError('工程顶层必须为对象')
            if data.get('format') != FORMAT:
                raise ValueError('不支持的编曲格式')
            values = dict(data)
            if isinstance(values.get('parameters'), dict) and set(values['parameters']) == set(PARAMETERS) - {'bus.bass'}:
                values['parameters'] = {**values['parameters'], 'bus.bass': PARAMETERS['bus.bass'][3]}
            values['tracks'] = [Track(**{**track, 'clips': [
                Clip(**{**clip, 'notes': [Note(**note) for note in clip['notes']]})
                for clip in track['clips']]}) for track in values['tracks']]
            values['automation'] = [Automation(**{**lane, 'points': [Point(**point) for point in lane['points']]})
                                    for lane in values['automation']]
            return cls(**values).validate()
        except (TypeError, KeyError, AttributeError) as error:
            raise ValueError(f'工程结构错误：{error}') from error

    def save(self, path):
        payload = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        destination = Path(path)
        temporary = destination.with_name(destination.name + '.' + identity() + '.tmp')
        try:
            temporary.write_text(payload, encoding='utf-8')
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    @classmethod
    def load(cls, path):
        if Path(path).stat().st_size > 8 * 1024 * 1024:
            raise ValueError('工程文件超过8MiB')
        try:
            return cls.from_dict(json.loads(Path(path).read_text(encoding='utf-8-sig')))
        except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
            raise ValueError('不是有效的编曲JSON文件') from error


class History:
    def __init__(self, project):
        self.project = project
        self.undo_stack = []
        self.redo_stack = []

    def edit(self, operation):
        before = deepcopy(self.project)
        try:
            operation(self.project)
            self.project.validate()
        except Exception:
            self.project = before
            raise
        if before != self.project:
            self.undo_stack.append(before)
            self.undo_stack = self.undo_stack[-80:]
            self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.project)
            self.project = self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.project)
            self.project = self.redo_stack.pop()


def duplicate_clip(clip, start):
    result = deepcopy(clip)
    result.id, result.start = identity(), start
    for note in result.notes:
        note.id = identity()
    return result


def demo_project():
    piano = Track('piano', '01 钢琴 · 和弦')
    guitar = Track('guitar', '02 吉他 · 分解')
    bass = Track('bass', '03 Bass · 低音')
    violin = Track('violin', '04 小提琴 · 旋律')
    drums = Track('drums', '05 鼓组 · 全段')
    for track, start, pitches in ((piano, 0, (60, 64, 67, 72)),
                                  (guitar, 2 * BAR, (40, 47, 52, 55, 59, 64)),
                                  (bass, 4 * BAR, (28, 35, 40, 43)),
                                  (violin, 6 * BAR, (67, 69, 71, 74))):
        clip = Clip(track.name.split('·')[-1].strip(), start, 2 * BAR)
        if track.instrument == 'piano':
            clip.notes = [Note(beat * PPQ, PPQ * 2, pitch, 84) for beat in (0, 4) for pitch in pitches]
        else:
            clip.notes = [Note(index * PPQ, int(PPQ * 0.8), pitches[index % len(pitches)], 95)
                          for index in range(8)]
        track.clips.append(clip)
    for bar in range(8):
        clip = Clip('基础律动', bar * BAR, BAR)
        clip.notes = ([Note(beat * PPQ, PPQ // 4, 0, 110) for beat in (0, 2)] +
                      [Note(beat * PPQ, PPQ // 4, 1, 100) for beat in (1, 3)] +
                      [Note(step * PPQ // 2, PPQ // 4, 2, 60 + (step % 2) * 10) for step in range(8)])
        drums.clips.append(clip)
    return Project('四乐器分段 + 鼓组演示', tracks=[piano, guitar, bass, violin, drums],
                   automation=[Automation('space.delay_mix', 'linear',
                                          [Point(0, 0), Point(6 * BAR, 0), Point(7 * BAR, 28), Point(8 * BAR, 0)])]).validate()


def ensemble_demo_project():
    project = demo_project()
    project.name = 'v8 五路合奏示例'
    project.bars = 4
    for track in project.tracks:
        if track.instrument == 'drums':
            track.clips = track.clips[:4]
        else:
            original = track.clips[0]
            original.start = 0
            track.clips.append(duplicate_clip(original, 2 * BAR))
    project.automation = [Automation('space.delay_mix', 'linear',
                                      [Point(0, 0), Point(2 * BAR, 0), Point(3 * BAR, 20), Point(4 * BAR, 0)])]
    return project.validate()
