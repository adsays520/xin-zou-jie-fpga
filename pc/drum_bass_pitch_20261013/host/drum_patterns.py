"""Drum patterns and UART frames; 16 beats, four subdivisions per beat."""
from __future__ import annotations
from dataclasses import dataclass, field
import json
from pathlib import Path
from functools import reduce

NAMES = ("底鼓 Kick", "军鼓 Snare", "闭踩镲 CH", "开踩镲 OH", "拍手 Clap", "吊镲 Crash", "叮叮镲 Ride", "低通鼓 Low", "中通鼓 Mid", "高通鼓 High", "边击 Rim", "牛铃 Cowbell")
KITS = ("原声标准（真实采样）", "原声摇滚（真实采样）", "原声流行（真实采样）")
STEPS = 64

def frame(command: int, p0=0, p1=0, p2=0) -> bytes:
    if any(type(x) is not int or not 0 <= x <= 255 for x in (command, p0, p1, p2)):
        raise ValueError("frame values must be integer bytes")
    b = bytes((0xA5, command, p0, p1, p2))
    return b + bytes((reduce(int.__xor__, b),))

def tempo_frame(bpm: int, swing: int) -> bytes:
    if type(bpm) is not int or not 30 <= bpm <= 300 or type(swing) is not int or not 0 <= swing <= 50:
        raise ValueError("BPM 30..300, swing 0..50")
    return frame(0x51, bpm >> 8, bpm & 255, swing)

def hit_frame(voice: int, velocity: int) -> bytes:
    if type(voice) is not int or not 0 <= voice < 12 or type(velocity) is not int or not 1 <= velocity <= 127:
        raise ValueError("voice 0..11, velocity 1..127")
    return frame(0x50, voice, velocity)

@dataclass
class Pattern:
    name: str = "自定义"
    bpm: int = 120
    swing: int = 0
    kit: int = 0
    cells: list[list[int]] = field(default_factory=lambda: [[0] * STEPS for _ in NAMES])
    levels: list[int] = field(default_factory=lambda: [100] * len(NAMES))

    def validate(self):
        tempo_frame(self.bpm, self.swing)
        if type(self.kit) is not int or not 0 <= self.kit < 3:
            raise ValueError("音色组必须为 0..2")
        if len(self.cells) != 12 or any(len(row) != STEPS for row in self.cells):
            raise ValueError("节奏必须为 12 行 × 64 个细分位置（16 拍）")
        if len(self.levels) != 12 or any(type(v) is not int or not 0 <= v <= 127 for row in self.cells for v in row) or any(type(v) is not int or not 0 <= v <= 127 for v in self.levels):
            raise ValueError("力度／音量必须是 0..127 的整数")
        if not isinstance(self.name, str) or len(self.name) > 200:
            raise ValueError("无效节奏名称")

    def upload_frames(self) -> list[bytes]:
        self.validate()
        return ([frame(0x52, 0), frame(0x53)] +
                [frame(0x54, voice, step, value) for voice, row in enumerate(self.cells) for step, value in enumerate(row)] +
                [frame(0x55), tempo_frame(self.bpm, self.swing), frame(0x56, self.kit)] +
                [frame(0x57, voice, value) for voice, value in enumerate(self.levels)])

    def save(self, path):
        self.validate()
        Path(path).write_text(json.dumps({"format": "gowin-drum-synth-v1", "meter": "4/4", "bars": 4, **self.__dict__}, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path):
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        if obj.get("format") != "gowin-drum-synth-v1" or obj.get("meter") != "4/4" or obj.get("bars") != 4:
            raise ValueError("不支持的鼓机工程格式")
        result = cls(**{k: obj[k] for k in ("name", "bpm", "swing", "kit", "cells", "levels")})
        result.validate()
        return result

    def step_seconds(self, step: int):
        return 15 / self.bpm * (1 + (self.swing / 100) * (1 if (step // 2) % 2 == 0 else -1))

# Original genre-inspired grooves, not transcriptions of songs.
BASIC_PRESETS = ("动次打次（基础8分）", "动次打次（四踩）", "动动打次（流行）", "摇滚16分", "半拍律动")
PRESETS = BASIC_PRESETS + ("经典摇滚", "布鲁斯 Shuffle", "流行 Pop", "硬摇滚", "抒情 Ballad", "Funk", "Disco / Dance", "Hip-Hop", "Bossa Nova", "爵士 Swing")

def basic_preset(name: str) -> Pattern:
    p = Pattern(name, 92 if name == "半拍律动" else 108, 0, 1)
    p.levels = [127, 112, 88, 92, 95, 100, 96, 105, 105, 105, 90, 90]
    for bar in range(4):
        b = bar * 16
        kicks = (0, 4, 8, 12) if name == "动次打次（四踩）" else (0, 2, 8, 10) if name == "动动打次（流行）" else (0, 8)
        snares = (8,) if name == "半拍律动" else (4, 12)
        for s in kicks: p.cells[0][b+s] = 118 if s % 8 == 0 else 102
        for s in snares: p.cells[1][b+s] = 112 if s == 4 else 119
        for s in range(0, 16, 1 if name == "摇滚16分" else 2):
            p.cells[2][b+s] = (78 if s % 4 == 0 else 58) if s % 2 == 0 else 42
        if name == "动动打次（流行）":
            p.cells[1][b+15] = 32  # quiet ghost note, before the next downbeat
    p.validate()
    return p

def preset(name: str) -> Pattern:
    if name not in PRESETS:
        raise ValueError("unknown preset")
    if name in BASIC_PRESETS:
        return basic_preset(name)
    bpm, swing, kit = {
        "经典摇滚": (112, 0, 1), "布鲁斯 Shuffle": (96, 33, 0), "流行 Pop": (108, 0, 2),
        "硬摇滚": (132, 0, 1), "抒情 Ballad": (72, 0, 2), "Funk": (104, 12, 1),
        "Disco / Dance": (124, 0, 2), "Hip-Hop": (88, 20, 0),
        "Bossa Nova": (126, 0, 0), "爵士 Swing": (138, 33, 0),
    }[name]
    p = Pattern(name, bpm, swing, kit)
    def put(voice, positions, velocity=100):
        for s in positions:
            p.cells[voice][s] = velocity
    for bar in range(4):
        b = bar * 16
        put(0, [b, b + 8], 115)
        put(1, [b + 4, b + 12], 108)
        put(2, [b + s for s in range(0, 16, 2)], 72)
        if name == "硬摇滚":
            put(0, [b + 6, b + 10, b + 14], 102)
            put(3, [b + 14], 88); p.cells[2][b + 14] = 0
        elif name == "布鲁斯 Shuffle":
            put(0, [b + 6], 80); put(1, [b + 10], 40)
        elif name == "流行 Pop":
            put(0, [b + 7, b + 10], 96); put(4, [b + 4, b + 12], 65)
        elif name == "抒情 Ballad":
            for s in range(b, b + 16): p.cells[2][s] = 0
            put(2, [b, b + 4, b + 8, b + 12], 55)
            put(0, [b + 10], 75)
        elif name == "Funk":
            put(0, [b + 3, b + 7, b + 10], 95)
            put(1, [b + 3, b + 9, b + 15], 38)
            put(2, [b + s for s in (1, 3, 5, 7, 9, 11, 13, 15)], 42)
        elif name == "Disco / Dance":
            put(0, [b, b + 4, b + 8, b + 12], 112)
            put(4, [b + 4, b + 12], 82)
            for s in (2, 6, 10, 14): p.cells[2][b + s] = 0
            put(3, [b + s for s in (2, 6, 10, 14)], 70)
        elif name == "Hip-Hop":
            put(0, [b + 3, b + 10], 100); put(1, [b + 15], 35)
        elif name == "Bossa Nova":
            p.cells[1][b:b + 16] = [0] * 16
            put(10, [b, b + 6, b + 12], 80); put(0, [b + 7, b + 15], 70)
        elif name == "爵士 Swing":
            p.cells[2][b:b + 16] = [0] * 16
            put(6, [b, b + 4, b + 6, b + 8, b + 12, b + 14], 85)
            put(2, [b + 4, b + 12], 45); put(1, [b + 10], 42)
    put(5, [0], 88)
    if name not in ("Bossa Nova", "爵士 Swing", "抒情 Ballad"):
        put(9, [56, 57], 90); put(8, [58, 59], 95); put(7, [60, 62], 105)
    p.validate()
    return p
