"""Bounded SMF 0/1 reader and guitar light mapping; no audio or serial side effects."""
from bisect import bisect_right
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
import struct


@dataclass(frozen=True)
class MidiNote:
    start: float
    end: float
    pitch: int
    velocity: int
    track: int
    channel: int


@dataclass(frozen=True)
class MidiScore:
    notes: tuple
    names: tuple
    duration: float


def read_midi(path):
    data = Path(path).read_bytes()
    if len(data) > 16 * 1024 * 1024:
        raise ValueError('MIDI文件超过16MB')
    def chunk(pos, tag):
        if data[pos:pos+4] != tag or pos+8 > len(data):
            raise ValueError('无效或截断的MIDI块')
        n = int.from_bytes(data[pos+4:pos+8], 'big')
        end = pos+8+n
        if end > len(data):
            raise ValueError('MIDI块长度超过文件')
        return data[pos+8:end], end
    header, pos = chunk(0, b'MThd')
    if len(header) != 6:
        raise ValueError('MIDI头长度无效')
    fmt, tracks, division = struct.unpack('>HHH', header)
    if fmt not in (0, 1) or not 1 <= tracks <= 256 or not division or division & 0x8000 or (fmt == 0 and tracks != 1):
        raise ValueError('支持PPQ时间制的标准MIDI 0/1；不支持SMPTE或格式2')
    events, tempos, names = [], [(0, -1, 500000)], []
    order = 0
    def vlq(buf, i):
        value = 0
        for _ in range(4):
            if i >= len(buf):
                raise ValueError('MIDI可变长度数被截断')
            b = buf[i]; i += 1
            value = (value << 7) | (b & 127)
            if b < 128:
                return value, i
        raise ValueError('MIDI可变长度数超过4字节')
    final_tick = 0
    for track in range(tracks):
        buf, pos = chunk(pos, b'MTrk')
        i = tick = running = 0
        name = f'轨道 {track+1}'
        ended = False
        while i < len(buf):
            dt, i = vlq(buf, i); tick += dt
            if i >= len(buf):
                raise ValueError('MIDI事件缺少状态字节')
            status = buf[i]
            if status & 128:
                i += 1
                running = status if status < 0xF0 else 0
            else:
                status = running
                if not status:
                    raise ValueError('MIDI running status缺少前导状态')
            order += 1
            if order > 1000000:
                raise ValueError('MIDI事件过多')
            if status in (0xFF, 0xF0, 0xF7):
                kind = buf[i] if status == 0xFF and i < len(buf) else None
                if status == 0xFF:
                    if kind is None: raise ValueError('Meta事件截断')
                    i += 1
                n, i = vlq(buf, i)
                payload = buf[i:i+n]; i += n
                if len(payload) != n: raise ValueError('MIDI事件内容截断')
                if kind == 3: name = payload.decode('utf-8', errors='replace')[:100]
                if kind == 0x51:
                    if n != 3 or not int.from_bytes(payload, 'big'): raise ValueError('MIDI速度事件无效')
                    tempos.append((tick, order, int.from_bytes(payload, 'big')))
                if kind == 0x2F:
                    if n: raise ValueError('MIDI结束事件无效')
                    ended = True; break
                continue
            if not 0x80 <= status < 0xF0: raise ValueError('不支持的MIDI状态')
            n = 1 if status >> 4 in (12, 13) else 2
            payload = buf[i:i+n]; i += n
            if len(payload) != n or any(b > 127 for b in payload): raise ValueError('MIDI通道数据无效')
            events.append((tick, order, track, status & 15, status >> 4, payload))
        if not ended: raise ValueError('MIDI轨道缺少结束标记')
        final_tick = max(final_tick, tick)
        names.append(name)
    tempos.sort()
    ticks, seconds, values = [], [], []
    previous = elapsed = 0; tempo = 500000
    for tick, _, new in tempos:
        elapsed += (tick-previous)*tempo/division/1000000
        ticks.append(tick); seconds.append(elapsed); values.append(new)
        previous, tempo = tick, new
    def sec(tick):
        j = bisect_right(ticks, tick)-1
        return seconds[j] + (tick-ticks[j])*values[j]/division/1000000
    held, released, pedals, notes = defaultdict(deque), defaultdict(list), defaultdict(bool), []
    def finish(item, end):
        start, pitch, velocity, track, channel = item
        if end > start: notes.append(MidiNote(sec(start), sec(end), pitch, velocity, track, channel))
    for tick, _, track, channel, kind, payload in sorted(events):
        key = (track, channel, payload[0]); group = (track, channel)
        if kind == 9 and payload[1]:
            held[key].append((tick, payload[0], payload[1], track, channel))
        elif kind == 8 or (kind == 9 and not payload[1]):
            if held[key]:
                item = held[key].popleft()
                if pedals[group]: released[group].append(item)
                else: finish(item, tick)
        elif kind == 11 and payload[0] in (64, 120, 121, 123):
            if payload[0] == 64:
                pedals[group] = payload[1] >= 64
            else:
                pedals[group] = False
                if payload[0] in (120, 123):
                    for k in list(held):
                        if k[:2] == group:
                            while held[k]: finish(held[k].popleft(), tick)
            if not pedals[group]:
                for item in released.pop(group, []): finish(item, tick)
    for items in list(held.values()) + list(released.values()):
        for item in items: finish(item, final_tick)
    if not notes: raise ValueError('MIDI没有可用的音符')
    return MidiScore(tuple(sorted(notes, key=lambda n: (n.start, n.track, n.pitch))), tuple(names), sec(final_tick))


OPEN_PITCHES = (64, 59, 55, 50, 45, 40)


def fingering(pitch):
    choices = [(pitch-base, string) for string, base in enumerate(OPEN_PITCHES, 1) if 0 <= pitch-base <= 20]
    return min(choices) if choices else None


def guide_masks(notes, position, transpose=0):
    """Position 1 is open fret; positions 2..21 are frets 1..20."""
    frets = strings = 0
    active = []
    for note in notes:
        if note.start <= position < note.end:
            choice = fingering(note.pitch + transpose)
            if choice:
                fret, string = choice
                frets |= 1 << fret
                strings |= 1 << (string-1)
                active.append((note.pitch+transpose, fret, string))
    return frets, strings, active


def mask_command(frets, strings):
    if not 0 <= frets < 1 << 21 or not 0 <= strings < 1 << 6:
        raise ValueError('灯位掩码越界')
    return f'LED,GUIDE,{frets:X},{strings:X}\n'.encode('ascii')
