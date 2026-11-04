#!/usr/bin/env python3
"""Graphical low-speed UART trigger for the Tang Mega guitar project."""

from __future__ import annotations

import math
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from ui_notices import messagebox
from ui_pages import EmbeddedPage
from drawn_synth import CMD_DRAW_SELECT, control_frame, make_upload_frames
from drawn_synth_editor import DrawnSynthPanel
from guitar_effects import GuitarEffects
from master_space_effects import MasterSpaceEffects
from drum_editor import DrumEditor
from performance_mixer import PerformanceMixer, DUET_LEVELS, level_frame
from serial_transport import SerializedPort

# Prefer the installed package; the portable release also includes pyserial.
try:
    import serial
    from serial.tools import list_ports
except ImportError:  # Keep protocol tests/imports usable before installation.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/python_deps'))
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        serial = None
        list_ports = None


SOF_COMMAND = 0xA5
CMD_PLUCK = 0x02
CMD_MODE = 0x03
CMD_TIMBRE = 0x04
CMD_PIANO_KEY = 0x05
CMD_PIANO_PEDAL = 0x06
CMD_ENV_BEGIN = 0x10
CMD_ENV_DATA = 0x11
CMD_ENV_COMMIT = 0x12
CMD_ENV_SELECT = 0x13
MODE_MONO = 0
MODE_POLY4 = 1
TIMBRE_GUITAR = 0
TIMBRE_PIANO = 1
TIMBRE_BASS = 2
ENVELOPE_POINTS = 4096
ENVELOPE_BLOCK_WORDS = 16
BASE_FREQUENCIES = (329.63, 246.94, 196.00, 146.83, 110.00, 82.41)
BASE_MIDI = (64, 59, 55, 50, 45, 40)
OPEN_NAMES = ("E4", "B3", "G3", "D3", "A2", "E2")
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Original four-bar hard-rock riff, quantized to a sixteenth-note grid.  The
# short E5 attacks act as palm-muted chugs; the three-note voicings are the
# accented power-chord punches.  It deliberately uses the normal pluck
# protocol, so every existing guitar effect remains live while it plays.
RIFF_BPM = 132
RIFF_STEPS = 64
RIFF_VOICINGS = {
    "E5": ((6, 0), (5, 2), (4, 2)),
    "E5·": ((6, 0), (5, 2)),
    "G5": ((6, 3), (5, 5), (4, 5)),
    "A5": ((6, 5), (5, 7), (4, 7)),
    "B♭5": ((6, 6), (5, 8), (4, 8)),
    "B5": ((5, 2), (4, 4), (3, 4)),
    "C5": ((5, 3), (4, 5), (3, 5)),
    "D5": ((5, 5), (4, 7), (3, 7)),
}
RIFF_EVENTS = (
    # Deliberately sparse revision: every attack has room to speak, while the
    # two-note E5 chugs remain quieter than the accented three-note punches.
    (0, "E5", 12), (3, "E5·", -18), (6, "E5·", -14),
    (8, "G5", 8), (12, "A5", 12), (14, "G5", 2),
    (16, "E5", 12), (19, "E5·", -18), (22, "E5·", -14),
    (24, "D5", 10), (28, "C5", 4), (30, "D5", 8),
    (32, "E5", 12), (35, "E5·", -18), (38, "E5·", -14),
    (40, "G5", 8), (44, "A5", 10), (46, "B♭5", 12),
    (48, "E5", 12), (52, "D5", 8), (56, "C5", 4),
    (60, "B5", 10), (62, "D5", 6),
)

# A slower, deliberately simple 4/4 progression: broad chords and generous
# rests, with a classic blues-rock attitude but no quotation of an existing
# song melody.  Each grid step is an eighth note.
RIFF2_BPM = 82
RIFF2_STEPS = 64
RIFF2_EVENTS = (
    (0, "E5", 8), (4, "G5", 2), (6, "A5", 6),
    (8, "E5", 8), (12, "D5", 4), (14, "C5", 0),
    (16, "E5", 8), (20, "G5", 2), (22, "A5", 6),
    (24, "C5", 4), (28, "D5", 6), (30, "E5", 10),
    (32, "E5", 8), (36, "D5", 4), (38, "C5", 0),
    (40, "G5", 4), (44, "A5", 6), (46, "C5", 8),
    (48, "B5", 4), (52, "C5", 2), (54, "D5", 6),
    (56, "E5", 12), (60, "E5·", -8), (62, "E5", 8),
)

# Original hard-rock hook: low-E pedal, a short sixteenth-note pickup,
# open power-chord punches and a C-D-B-E turnaround. Muted dyads use a
# shorter gate than the full chords, rather than letting every hit ring.
RIFF3_BPM = 128
RIFF3_STEPS = 64
RIFF3_EVENTS = (
    (0, "E5", 12), (2, "E5·", -18), (4, "E5·", -14),
    (6, "E5·", -18), (7, "E5·", -12), (8, "G5", 8),
    (10, "E5·", -14), (12, "A5", 12), (14, "E5·", -12),
    (16, "E5", 12), (18, "E5·", -18), (20, "E5·", -14),
    (22, "E5·", -18), (23, "E5·", -12), (24, "D5", 10),
    (26, "E5·", -14), (28, "A5", 12), (30, "G5", 8),
    (32, "E5", 12), (34, "E5·", -18), (36, "E5·", -14),
    (38, "E5·", -18), (39, "E5·", -12), (40, "G5", 8),
    (42, "E5·", -14), (44, "A5", 10), (46, "D5", 12),
    (48, "C5", 8), (50, "E5·", -18), (52, "D5", 10),
    (54, "E5·", -14), (56, "B5", 12), (60, "E5", 16),
    (62, "E5·", -14), (63, "E5·", -18),
)

RIFF_PROFILES = {
    1: {
        "title": "Riff 1",
        "description": "原创 E 小调 · 132 BPM · 4 小节",
        "bpm": RIFF_BPM,
        "subdivision": 4,
        "steps": RIFF_STEPS,
        "events": RIFF_EVENTS,
        "tail_min_ms": 190,
    },
    2: {
        "title": "Riff 2",
        "description": "慢速 4/4 蓝调硬摇滚 · 82 BPM · 8 小节",
        "bpm": RIFF2_BPM,
        "subdivision": 2,
        "steps": RIFF2_STEPS,
        "events": RIFF2_EVENTS,
        "tail_min_ms": 290,
    },
    3: {
        "title": "Riff 3 · 铁轨",
        "description": "原创硬摇滚 · E 小调 · 128 BPM · 4/4 × 4小节",
        "bpm": RIFF3_BPM,
        "subdivision": 4,
        "steps": RIFF3_STEPS,
        "events": RIFF3_EVENTS,
        "tail_min_ms": 225,
        "tail_by_voicing": {"E5·": 70},
    },
}
RIFF_IDLE_TEXT = "Riff 1：132 BPM · Riff 2：82 BPM · Riff 3 铁轨：128 BPM / 4/4"
RIFF_SUSTAIN_MAX = 127
RIFF_NATURAL_TAIL_MS = 1400


def xor_checksum(values: bytes | bytearray | list[int]) -> int:
    result = 0
    for value in values:
        result ^= int(value)
    return result


def make_command(command: int, string_number: int, fret: int, velocity: int) -> bytes:
    if command != CMD_PLUCK:
        raise ValueError("unsupported command")
    if not 1 <= string_number <= 6:
        raise ValueError("string must be 1..6")
    if not 0 <= fret <= 20:
        raise ValueError("fret must be 0..20")
    if not 1 <= velocity <= 127:
        raise ValueError("velocity must be 1..127")
    frame = bytearray((SOF_COMMAND, command, string_number, fret, velocity))
    frame.append(xor_checksum(frame))
    return bytes(frame)


def make_mode_command(mode: int) -> bytes:
    if mode not in (MODE_MONO, MODE_POLY4):
        raise ValueError("mode must be MODE_MONO or MODE_POLY4")
    frame = bytearray((SOF_COMMAND, CMD_MODE, mode, 0, 0))
    frame.append(xor_checksum(frame))
    return bytes(frame)


def make_timbre_command(timbre: int) -> bytes:
    if timbre not in (TIMBRE_GUITAR, TIMBRE_PIANO, TIMBRE_BASS):
        raise ValueError("timbre must be guitar, piano or bass")
    frame = bytearray((SOF_COMMAND, CMD_TIMBRE, timbre, 0, 0))
    frame.append(xor_checksum(frame))
    return bytes(frame)


def make_piano_key_command(key: int, velocity: int, note_on: bool) -> bytes:
    if not 21 <= key <= 108:
        raise ValueError("piano key must be MIDI 21..108 (A0..C8)")
    if not 1 <= velocity <= 127:
        raise ValueError("velocity must be 1..127")
    frame = bytearray((SOF_COMMAND, CMD_PIANO_KEY, key, velocity, int(note_on)))
    frame.append(xor_checksum(frame))
    return bytes(frame)


def make_piano_pedal_command(level: int) -> bytes:
    if not 0 <= level <= 4:
        raise ValueError("piano pedal level must be 0..4")
    frame = bytearray((SOF_COMMAND, CMD_PIANO_PEDAL, level, 0, 0))
    frame.append(xor_checksum(frame))
    return bytes(frame)


def crc16_ccitt(values: bytes | bytearray, initial: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE used by fixed sixteen-word envelope packets."""
    crc = initial
    for value in values:
        crc ^= int(value) << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def make_envelope_control(command: int, value: int = 0) -> bytes:
    if command not in (CMD_ENV_BEGIN, CMD_ENV_COMMIT, CMD_ENV_SELECT):
        raise ValueError("unsupported envelope control command")
    if command == CMD_ENV_SELECT and value not in (0, 1):
        raise ValueError("envelope mode must be 0 or 1")
    if command != CMD_ENV_SELECT and value != 0:
        raise ValueError("BEGIN/COMMIT payload must be zero")
    frame = bytearray((SOF_COMMAND, command, value, 0, 0))
    frame.append(xor_checksum(frame))
    return bytes(frame)


def make_envelope_data(address: int, words: list[int] | tuple[int, ...]) -> bytes:
    if not 0 <= address <= ENVELOPE_POINTS - ENVELOPE_BLOCK_WORDS:
        raise ValueError("envelope address out of range")
    if address % ENVELOPE_BLOCK_WORDS:
        raise ValueError("envelope address must be sixteen-word aligned")
    if len(words) != ENVELOPE_BLOCK_WORDS:
        raise ValueError("envelope packet must contain sixteen words")
    frame = bytearray((SOF_COMMAND, CMD_ENV_DATA, (address >> 8) & 0x0F, address & 0xFF))
    for word in words:
        if not 0 <= int(word) <= 0xFFFF:
            raise ValueError("envelope word out of range")
        frame.extend(((int(word) >> 8) & 0xFF, int(word) & 0xFF))
    crc = crc16_ccitt(frame)
    frame.extend((crc >> 8, crc & 0xFF))
    return bytes(frame)


def make_envelope_upload(words: list[int] | tuple[int, ...]) -> bytes:
    if len(words) != ENVELOPE_POINTS:
        raise ValueError(f"envelope must contain {ENVELOPE_POINTS} points")
    frames = [make_envelope_control(CMD_ENV_BEGIN)]
    for address in range(0, ENVELOPE_POINTS, ENVELOPE_BLOCK_WORDS):
        frames.append(make_envelope_data(address, words[address:address + ENVELOPE_BLOCK_WORDS]))
    frames.append(make_envelope_control(CMD_ENV_COMMIT))
    frames.append(make_envelope_control(CMD_ENV_SELECT, 1))
    return b"".join(frames)


def note_name(string_number: int, fret: int) -> str:
    midi = BASE_MIDI[string_number - 1] + fret
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def midi_note_name(midi: int) -> str:
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def note_frequency(string_number: int, fret: int) -> float:
    return BASE_FREQUENCIES[string_number - 1] * 2.0 ** (fret / 12.0)


def bass_note_name(string_number: int, fret: int) -> str:
    if not 3 <= string_number <= 6 or not 0 <= fret <= 20:
        raise ValueError("Bass uses guitar strings 3..6, frets 0..20")
    return midi_note_name(BASE_MIDI[string_number - 1] + fret - 12)


def bass_note_frequency(string_number: int, fret: int) -> float:
    bass_note_name(string_number, fret)  # Same range validation as the FPGA.
    return note_frequency(string_number, fret) / 2


def make_riff_event_frames(voicing: str, velocity: int) -> bytes:
    """Build one atomic UART burst for a named power-chord voicing."""
    if voicing not in RIFF_VOICINGS:
        raise ValueError("unknown riff voicing")
    velocity = max(1, min(127, int(velocity)))
    return b"".join(
        make_command(CMD_PLUCK, string_number, fret, velocity)
        for string_number, fret in RIFF_VOICINGS[voicing]
    )


def riff_tail_ms(riff_number: int, sustain: int, voicing: str | None = None) -> int | None:
    """Map 0 to today's short tail and 127 to the previous natural tail."""
    if riff_number not in RIFF_PROFILES:
        raise ValueError("unknown riff number")
    if not 0 <= sustain <= RIFF_SUSTAIN_MAX:
        raise ValueError("riff sustain must be 0..127")
    if sustain == RIFF_SUSTAIN_MAX:
        return None
    profile = RIFF_PROFILES[riff_number]
    minimum = int(profile.get("tail_by_voicing", {}).get(voicing, profile["tail_min_ms"]))
    return round(minimum + (RIFF_NATURAL_TAIL_MS - minimum) * sustain / 126)


def make_riff_attack_frames(
    riff_number: int, voicing: str, velocity: int, sustain: int = 0
) -> bytes:
    """Build a tight attack, optionally clearing the previous ringing voices."""
    riff_tail_ms(riff_number, sustain, voicing)  # Validate profile and slider range.
    frames = make_riff_event_frames(voicing, velocity)
    if sustain < RIFF_SUSTAIN_MAX:
        frames = make_mode_command(MODE_POLY4) + frames
    return frames


class PianoKeyboard(EmbeddedPage):
    """Independent, scrollable A0-C8 keyboard using the existing UART port."""

    WHITE_WIDTH = 28
    BLACK_WIDTH = 18
    WHITE_HEIGHT = 190
    BLACK_HEIGHT = 112
    BLACK_NOTES = frozenset((1, 3, 6, 8, 10))

    def __init__(self, controller: "GuitarController") -> None:
        super().__init__(controller)
        self.controller = controller
        self.held_key: int | None = None

        from ui_theme import scroll_body, window
        window(self, '88 键钢琴', '钢琴演奏 · 手绘波形 · 手绘包络', 1200, 790)
        body = scroll_body(self, padding=(12, 0, 12, 12))
        toolbar = ttk.Frame(body, padding=10)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="钢琴力度").pack(side="left")
        ttk.Scale(toolbar, from_=1, to=127, variable=controller.piano_velocity,
                  orient="horizontal", length=180).pack(side="left", padx=6)
        ttk.Label(toolbar, textvariable=controller.piano_velocity, width=4).pack(side="left")
        ttk.Label(toolbar, text="踏板").pack(side="left", padx=(22, 4))
        pedal = ttk.Combobox(toolbar, state="readonly", width=4,
                             textvariable=controller.piano_pedal, values=(0, 1, 2, 3, 4))
        pedal.pack(side="left")
        pedal.bind("<<ComboboxSelected>>", self._pedal_changed)
        ttk.Label(toolbar, text="0=抬起  4=全踏").pack(side="left", padx=6)
        ttk.Button(toolbar, text="抬起踏板", command=self.pedal_up).pack(side="left", padx=8)
        ttk.Label(toolbar, text="跳到").pack(side="left", padx=(20, 4))
        self.octave = ttk.Combobox(toolbar, state="readonly", width=5,
                                   values=("A0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"))
        self.octave.pack(side="left")
        self.octave.set("C4")
        self.octave.bind("<<ComboboxSelected>>", self._jump_to_octave)

        self.drawn_panel = DrawnSynthPanel(body, controller)
        self.drawn_panel.pack(fill="x", padx=10, pady=(0, 6))

        self.canvas = tk.Canvas(body, height=self.WHITE_HEIGHT + 20,
                                background="#E8F2FC", highlightthickness=0)
        self.canvas.pack(fill="x", padx=10, pady=(2, 0))
        scrollbar = ttk.Scrollbar(body, orient="horizontal", command=self.canvas.xview)
        scrollbar.pack(fill="x", padx=10, pady=(0, 4))
        self.canvas.configure(xscrollcommand=scrollbar.set)
        self._draw_keys()
        # Mouse-up anywhere in the main window releases the held piano note.
        self._release_binding = controller.bind("<ButtonRelease-1>", self._release_key, add="+")

        self.status = tk.StringVar(value="按住琴键发声，松开即制音；横向滚动覆盖全部 88 键。")
        ttk.Label(body, textvariable=self.status, padding=(10, 0, 10, 8)).pack(fill="x")
        from ui_theme import compact_keyboard
        compact_keyboard(self)
        self.after_idle(lambda: self._show_key(60))

    def _draw_keys(self) -> None:
        white_index: dict[int, int] = {}
        count = 0
        for key in range(21, 109):
            if key % 12 not in self.BLACK_NOTES:
                white_index[key] = count
                x = count * self.WHITE_WIDTH
                tag = f"key_{key}"
                self.canvas.create_rectangle(x, 0, x + self.WHITE_WIDTH,
                    self.WHITE_HEIGHT, fill="#FFFFFF", outline="#BDD2E4",
                    activefill="#DDECFB", tags=(tag, "white"))
                if key % 12 == 0 or key in (21, 108):
                    self.canvas.create_text(x + self.WHITE_WIDTH / 2,
                        self.WHITE_HEIGHT - 17, text=midi_note_name(key),
                        font=("Segoe UI", 8), fill="#334155", tags=(tag,))
                count += 1
        for key in range(21, 109):
            if key % 12 in self.BLACK_NOTES:
                prior = key - 1
                x = (white_index[prior] + 1) * self.WHITE_WIDTH - self.BLACK_WIDTH / 2
                tag = f"key_{key}"
                self.canvas.create_rectangle(x, 0, x + self.BLACK_WIDTH,
                    self.BLACK_HEIGHT, fill="#263E53", outline="#F8FBFE",
                    activefill="#348BD5", tags=(tag, "black"))
        self.canvas.configure(scrollregion=(0, 0, count * self.WHITE_WIDTH, self.WHITE_HEIGHT))
        for key in range(21, 109):
            self.canvas.tag_bind(f"key_{key}", "<ButtonPress-1>",
                                 lambda _event, k=key: self._press_key(k))

    def _show_key(self, key: int) -> None:
        white_before = sum(1 for value in range(21, key)
                           if value % 12 not in self.BLACK_NOTES)
        full_width = 52 * self.WHITE_WIDTH
        self.canvas.xview_moveto(min(1.0, white_before * self.WHITE_WIDTH / full_width))

    def _jump_to_octave(self, _event: tk.Event) -> None:
        octave = self.octave.get()
        key = 21 if octave == "A0" else min(108, 12 * (int(octave[1:]) + 1))
        self._show_key(key)

    def _press_key(self, key: int) -> None:
        if self.held_key == key:
            return
        if self.held_key is not None:
            self._release_key()
        if self.controller.send_piano_key_for(key, self.controller.piano_velocity.get(), True):
            self.held_key = key
            self.status.set(f"{midi_note_name(key)} · MIDI {key} · "
                            f"{440.0 * 2.0 ** ((key - 69) / 12.0):.3f} Hz")

    def _release_key(self, _event: tk.Event | None = None) -> None:
        if self.held_key is not None:
            if self.controller.port is not None and self.controller.port.is_open:
                self.controller.send_piano_key_for(
                    self.held_key, self.controller.piano_velocity.get(), False)
            self.held_key = None

    def _pedal_changed(self, _event: tk.Event) -> None:
        self.controller.send_piano_pedal()

    def pedal_up(self) -> None:
        self.controller.piano_pedal.set(0)
        self.controller.send_piano_pedal()

    def on_hide(self) -> None:
        self._release_key()

    def close(self) -> None:
        self.controller.unbind("<ButtonRelease-1>", self._release_binding)
        self._release_key()
        try:
            self.controller.draw_project = self.drawn_panel.project()
        except ValueError:
            pass
        if self.controller.draw_upload_busy:
            self.controller.restore_piano()
        if self.controller.piano_pedal.get():
            self.controller.piano_pedal.set(0)
            if self.controller.port is not None and self.controller.port.is_open:
                self.controller.send_piano_pedal()
        self.controller.piano_keyboard = None
        self.destroy()


class GuitarController(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Tang Mega 演奏控制台")
        self.geometry("1220x760")
        self.minsize(980, 660)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.port = None
        self.port_map: dict[str, str] = {}
        self.selected_string = tk.IntVar(value=6)
        self.selected_fret = tk.IntVar(value=0)
        self.velocity = tk.IntVar(value=110)
        self.piano_key = tk.IntVar(value=60)
        self.piano_velocity = tk.IntVar(value=90)
        self.piano_pedal = tk.IntVar(value=0)
        self.connection_text = tk.StringVar(value="未连接")
        self.mode_text = tk.StringVar(value="板端模式：32复音（复位默认）")
        self.current_mode = MODE_POLY4
        self.current_timbre = TIMBRE_GUITAR
        self.timbre_text = tk.StringVar(value="音色：木吉他")
        self.envelope_text = tk.StringVar(value="吉他包络：板载算法")
        self.note_text = tk.StringVar()
        self.fret_buttons: dict[tuple[int, int], tk.Button] = {}
        self.envelope_editor: EmbeddedPage | None = None
        self.piano_keyboard: PianoKeyboard | None = None
        self.draw_project = None
        self.draw_upload_busy = False
        self.draw_upload_token = 0
        self.draw_upload_done = None
        self.drawn_enabled_requested = False
        self.effects_window = None
        self.space_effects_window = None
        self.drum_window = None
        self.mixer_window = None
        self.bus_levels = [127, 127, 127]
        self.auto_balance = tk.BooleanVar(value=True)
        self.riff_playing = False
        self.riff_active = 0
        self.riff_attack_count = 0
        self.riff_sustain = tk.IntVar(value=0)
        self.riff_after_ids: list[str] = []
        self.riff_token = 0
        self.riff_status = tk.StringVar(value=RIFF_IDLE_TEXT)

        from guitar_pitch import PitchControl
        self.pitch_control = PitchControl()
        self.pitch_page = None

        self._build_ui()
        self.refresh_ports()
        self._update_note_display()
        self.bind("<space>", lambda event: self.guitar_shortcut(event, lambda: self.send_command(CMD_PLUCK)))
        self.bind("<Left>", lambda event: self.guitar_shortcut(event, lambda: self.move_fret(-1)))
        self.bind("<Right>", lambda event: self.guitar_shortcut(event, lambda: self.move_fret(1)))

    def _build_ui(self) -> None:
        from ui_main import build
        build(self)


    def log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_view.configure(state="normal")
        self.log_view.insert("end", f"[{timestamp}] {message}\n")
        self.log_view.see("end")
        self.log_view.configure(state="disabled")

    def refresh_ports(self) -> None:
        if list_ports is None:
            self.port_map = {}
            self.port_combo["values"] = ()
            self.connection_text.set("缺少 pyserial")
            return
        ports = sorted(list_ports.comports(), key=lambda item: item.device)
        self.port_map = {
            f"{item.device} — {item.description}"
            f"{f' — SN:{item.serial_number}' if item.serial_number else ''}": item.device
            for item in ports
        }
        values = tuple(self.port_map)
        self.port_combo["values"] = values
        if values and not self.port_combo.get():
            preferred = next((v for v in values if v.upper().endswith("B")), None)
            if preferred is None:
                preferred = next(
                    (v for v in values if any(tag in v.upper() for tag in ("BL616", "JTAG", "UART", "SIPEED", "USB"))),
                    values[0],
                )
            self.port_combo.set(preferred)
        self.log(f"发现 {len(values)} 个串口")

    def toggle_connection(self) -> None:
        if self.port is not None:
            self.disconnect()
            return
        if serial is None:
            messagebox.showerror("缺少依赖", "请先运行：python -m pip install -r requirements.txt")
            return
        display_name = self.port_combo.get()
        device = self.port_map.get(display_name)
        if not device:
            messagebox.showwarning("没有设备", "请选择一个COM口。")
            return
        try:
            self.port = SerializedPort(serial.Serial(
                device, 115200, bytesize=8, parity="N", stopbits=1,
                timeout=0, write_timeout=2.0
            ))
            self.connection_text.set(f"已连接 {device}")
            self.connect_button.configure(text="断开")
            self.log(f"连接 {device} 成功：115200 8N1 单向触发")
            for bus, value in enumerate(self.bus_levels):
                self.send_bus_level(bus, value)
        except Exception as exc:
            self.port = None
            messagebox.showerror("连接失败", str(exc))

    def auto_connect(self, device: str) -> None:
        """Optional launch helper; normal manual connection behaviour is unchanged."""
        if self.port is not None:
            return
        display_name = next(
            (label for label, path in self.port_map.items() if path.upper() == device.upper()),
            None,
        )
        if display_name is None:
            self.log(f"自动连接失败：未发现 {device}")
            return
        self.port_combo.set(display_name)
        self.toggle_connection()

    def disconnect(self) -> None:
        if hasattr(self, "pitch_control"):
            self.pitch_control.reset()
            page = getattr(self, "pitch_page", None)
            if page is not None and page.winfo_exists():
                page.sync()
        verify = getattr(self, 'verification_page', None)
        if verify is not None and verify.winfo_exists():
            verify.on_disconnect()
        if getattr(self, "drum_window", None) is not None and self.drum_window.winfo_exists():
            self.drum_window.stop()
        # Lightweight protocol-test harnesses reuse this method without the UI
        # sequencer attributes, hence the feature-detection guard.
        if hasattr(self, "stop_riff"):
            self.stop_riff("串口断开")
        self.draw_upload_token += 1
        self._finish_draw_upload(False, "串口已断开，上传已取消；板端状态未知")
        if self.port is not None:
            try:
                self.port.close()
            except Exception:
                pass
        self.port = None
        self.connection_text.set("未连接")
        self.connect_button.configure(text="连接")
        self.log("设备已断开")

    def select_note(self, string_number: int, fret: int, send: bool = False) -> None:
        if self.current_timbre == TIMBRE_BASS and string_number < 3:
            return
        old = (self.selected_string.get(), self.selected_fret.get())
        self.selected_string.set(string_number)
        self.selected_fret.set(fret)
        self._update_note_display(old)
        # Selection stays in the GUI until PLUCK sends one trigger frame.

    def pluck_note(self, string_number: int, fret: int) -> None:
        if self.current_timbre == TIMBRE_BASS and string_number < 3:
            return
        self.select_note(string_number, fret, False)
        self.send_command(CMD_PLUCK)

    def move_fret(self, delta: int) -> None:
        self.select_note(
            self.selected_string.get(),
            min(20, max(0, self.selected_fret.get() + delta)),
            False,
        )

    def _update_note_display(self, old: tuple[int, int] | None = None) -> None:
        string_number = self.selected_string.get()
        fret = self.selected_fret.get()
        name = self.display_note_name(string_number, fret)
        frequency = self.display_note_frequency(string_number, fret)
        self.note_text.set(
            f"{string_number}弦 · {fret}品 · {name} · {frequency:.6f} Hz"
        )
        from ui_main import update_note
        update_note(self, old)

    def display_note_name(self, string_number: int, fret: int) -> str:
        return (bass_note_name if self.current_timbre == TIMBRE_BASS else note_name)(string_number, fret)

    def display_note_frequency(self, string_number: int, fret: int) -> float:
        return (bass_note_frequency if self.current_timbre == TIMBRE_BASS else note_frequency)(string_number, fret)

    def send_command(self, command: int) -> None:
        if self.current_timbre == TIMBRE_BASS and self.selected_string.get() < 3:
            return
        if self.draw_upload_busy:
            self.log("双曲线上传中，暂不接受拨弦命令")
            return
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return
        try:
            frame = make_command(
                command,
                self.selected_string.get(),
                self.selected_fret.get(),
                self.velocity.get(),
            )
            self.port.write(frame)
            self.log(f"TX {frame.hex(' ').upper()}  拨弦")
        except Exception as exc:
            self.log(f"发送失败：{exc}")
            messagebox.showerror("发送失败", str(exc))
            self.disconnect()

    def send_mode(self, mode: int) -> None:
        if self.draw_upload_busy:
            return
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return
        try:
            frame = make_mode_command(mode)
            self.port.write(frame)
            label = ("Bass 8复音" if self.current_timbre == TIMBRE_BASS else "32复音") if mode == MODE_POLY4 else "单音直通"
            self.current_mode = mode
            self.mode_text.set(f"板端模式：{label}")
            self.log(f"TX {frame.hex(' ').upper()}  切换至{label}")
        except Exception as exc:
            self.log(f"模式切换失败：{exc}")
            messagebox.showerror("发送失败", str(exc))
            self.disconnect()

    def send_piano_key(self, note_on: bool) -> None:
        self.send_piano_key_for(int(self.piano_key.get()),
                                int(self.velocity.get()), note_on)

    def send_piano_key_for(self, key: int, velocity: int, note_on: bool) -> bool:
        if self.draw_upload_busy:
            return False
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return False
        if note_on and self.current_timbre != TIMBRE_PIANO:
            if not self.send_timbre(TIMBRE_PIANO):
                return False
        try:
            frame = make_piano_key_command(key, velocity, note_on)
            self.port.write(frame)
            action = "按下" if note_on else "松开"
            self.log(
                f"TX {frame.hex(' ').upper()}  钢琴{action} "
                f"{midi_note_name(key)} ({440.0 * 2.0 ** ((key - 69) / 12.0):.3f} Hz)"
            )
            return True
        except Exception as exc:
            self.log(f"钢琴按键发送失败：{exc}")
            messagebox.showerror("发送失败", str(exc))
            self.disconnect()
            return False

    def send_piano_pedal(self) -> None:
        if self.draw_upload_busy:
            self.log("请等待手绘波表与包络上传结束后再改变踏板")
            return
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return
        try:
            level = int(self.piano_pedal.get())
            frame = make_piano_pedal_command(level)
            self.port.write(frame)
            self.log(f"TX {frame.hex(' ').upper()}  钢琴踏板层 {level}/4")
        except Exception as exc:
            self.log(f"钢琴踏板发送失败：{exc}")
            messagebox.showerror("发送失败", str(exc))
            self.disconnect()

    def open_envelope_editor(self) -> None:
        self.show_page("piano")

    def open_piano_keyboard(self) -> None:
        self.show_page("piano")

    def send_timbre(self, timbre: int) -> bool:
        if self.draw_upload_busy:
            return False
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return False
        try:
            frame = make_timbre_command(timbre)
            self.port.write(frame)
            self.port.flush()
            if timbre == TIMBRE_BASS and self.riff_playing:
                self.stop_riff("已切换 Bass，停止原吉他 Riff")
            self.current_timbre = timbre
            if hasattr(self, "pitch_control"):
                self.pitch_control.reset()
                page = getattr(self, "pitch_page", None)
                if page is not None and page.winfo_exists():
                    page.sync()
            label = {TIMBRE_GUITAR: "木吉他", TIMBRE_PIANO: "独立钢琴", TIMBRE_BASS: "独立 Bass · 低四弦"}[timbre]
            old = (self.selected_string.get(), self.selected_fret.get())
            if timbre == TIMBRE_BASS and self.selected_string.get() < 3:
                self.selected_string.set(6)
            self.timbre_text.set(f"音色：{label}")
            self.mode_text.set("板端模式：" + (("Bass 8复音" if timbre == TIMBRE_BASS else "32复音") if self.current_mode == MODE_POLY4 else "单音直通"))
            from ui_main import update_instrument
            update_instrument(self)
            self._update_note_display(old)
            self.log(f"TX {frame.hex(' ').upper()}  切换至{label}；旧音清除")
            return True
        except Exception as exc:
            self.log(f"音色切换失败：{exc}")
            messagebox.showerror("发送失败", str(exc))
            self.disconnect()
            return False

    def send_envelope_mode(self, custom: bool) -> None:
        if self.draw_upload_busy:
            self.log("请等待手绘波表与包络上传结束")
            return
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return
        try:
            frame = make_envelope_control(CMD_ENV_SELECT, 1 if custom else 0)
            self.port.write(frame)
            self.port.flush()
            label = "自定义RAM" if custom else "吉他板载算法"
            self.envelope_text.set(f"包络：{label}")
            self.log(f"TX {frame.hex(' ').upper()}  选择{label}")
        except Exception as exc:
            self.log(f"包络模式发送失败：{exc}")
            messagebox.showerror("发送失败", str(exc))
            self.disconnect()

    def send_custom_envelope(self, values: list[float], callback) -> None:
        if self.draw_upload_busy:
            callback(False, "请先等待双曲线上传结束")
            return
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            callback(False, "未连接串口，未发送包络")
            return
        words = [round(max(0.0, min(1.0, value)) * 32768.0) for value in values]
        if len(words) != ENVELOPE_POINTS:
            callback(False, f"包络点数必须为{ENVELOPE_POINTS}")
            return
        # Exact-zero endpoints prevent a Note-On or voice-release discontinuity.
        words[0] = 0
        words[-1] = 0
        payload = make_envelope_upload(words)
        try:
            # The protocol has no ACK.  Explicitly flush the voice bank before
            # BEGIN so envelope_write_allowed cannot silently reject an upload
            # while an old voice is still allocated.
            controls = make_envelope_control(CMD_ENV_SELECT, 0)
            controls += make_mode_command(self.current_mode)
            self.port.write(controls)
            self.port.flush()
            self.envelope_text.set("吉他包络：板载算法（等待上传）")
            self.log("已切回原有ADSR并清空声部；0.1秒后上传4096点自定义包络")
        except Exception as exc:
            callback(False, f"切换原有ADSR失败：{exc}")
            self.disconnect()
            return

        def perform_upload() -> None:
            if self.draw_upload_busy:
                callback(False, "双曲线上传已开始，取消本次吉他包络上传")
                return
            if self.port is None or not self.port.is_open:
                callback(False, "等待期间串口已断开")
                return
            try:
                written = self.port.write(payload)
                self.port.flush()
                if written != len(payload):
                    raise IOError(f"只写入{written}/{len(payload)}字节")
                self.envelope_text.set("包络：自定义RAM（已发送，无ACK）")
                self.log(
                    f"自定义包络上传完成：{ENVELOPE_POINTS}点，"
                    f"{len(payload)}字节，CRC16分包校验"
                )
                callback(True, "上传已发送并选择自定义RAM包络（板端无ACK）；现在可以拨弦")
            except Exception as exc:
                callback(False, f"发送失败：{exc}")
                self.disconnect()

        self.after(100, perform_upload)

    def restore_piano(self) -> bool:
        self.draw_upload_token += 1
        self._finish_draw_upload(False, "已取消上传，恢复原钢琴")
        if self.port is not None and self.port.is_open:
            try:
                frame = control_frame(CMD_DRAW_SELECT, 0)
                if self.port.write(frame) != len(frame):
                    raise IOError("恢复命令未完整写入")
                if not self.send_timbre(TIMBRE_PIANO):
                    return False
                self.log("恢复原钢琴；手绘波表和包络未删除")
                return True
            except Exception as exc:
                self.log(f"恢复钢琴失败：{exc}")
                self.disconnect()
        return False

    def _finish_draw_upload(self, success: bool, message: str) -> None:
        self.draw_upload_busy = False
        self.drawn_enabled_requested = success
        done, self.draw_upload_done = self.draw_upload_done, None
        if done is not None:
            done(success, message)

    def send_drawn_synth(self, wave, envelope, duration_ms, progress, callback) -> None:
        if self.draw_upload_busy:
            callback(False, "已有双曲线上传正在进行")
            return
        if self.port is None or not self.port.is_open:
            callback(False, "未连接串口，未发送")
            return
        frames = make_upload_frames(wave, envelope, duration_ms)
        try:
            if not self.send_timbre(TIMBRE_PIANO):
                callback(False, "未切换到钢琴控制通路")
                return
            frame = control_frame(CMD_DRAW_SELECT, 0)
            if self.port.write(frame) != len(frame):
                raise IOError("退出手绘模式命令未完整写入")
            self.port.flush()
        except Exception as exc:
            callback(False, f"准备上传失败：{exc}")
            return
        self.draw_upload_token += 1
        token = self.draw_upload_token
        self.draw_upload_busy = True
        self.draw_upload_done = callback
        self.drawn_enabled_requested = False
        index = 0
        progress(0, len(frames))

        def send_next():
            nonlocal index
            if token != self.draw_upload_token:
                return
            if self.port is None or not self.port.is_open:
                self._finish_draw_upload(False, "串口已断开，手绘合成未启用")
                return
            try:
                if index < len(frames):
                    frame = frames[index]
                    if self.port.write(frame) != len(frame):
                        raise IOError("串口未写入完整分包")
                    index += 1
                    if index % 8 == 0 or index == len(frames):
                        progress(index, len(frames))
                    self.after(4, send_next)
                elif self.port.out_waiting:
                    self.after(20, send_next)
                else:
                    self.timbre_text.set("音色：手绘波表 × 手绘包络（已发送，无ACK）")
                    self.log(f"双曲线已发送：8×1024波表、4096点包络、{duration_ms:g}ms；使用88键选择频率")
                    self._finish_draw_upload(True, "两张表及启用命令已发送（板端无ACK）。按住琴键听完整包络；松键约76ms淡出。修改画布后需重新上传。")
            except Exception as exc:
                self._finish_draw_upload(False, f"发送失败：{exc}；不保证板端已接收")
                self.disconnect()

        self.after(100, send_next)

    def open_effects(self) -> None:
        self.show_page("effects")

    def open_master_effects(self) -> None:
        self.show_page("mix")

    def open_drums(self) -> None:
        self.show_page("drums")

    def open_mixer(self) -> None:
        self.show_page("mix")

    def send_bus_level(self, bus: int, value: int) -> bool:
        if self.draw_upload_busy or self.port is None or not self.port.is_open:
            return False
        try:
            data = level_frame(bus, value)
            if self.port.write(data) != len(data):
                raise IOError("演奏混音命令未完整写入")
            self.bus_levels[bus] = value
            return True
        except Exception as exc:
            self.log(f"演奏混音发送失败：{exc}")
            self.disconnect()
            return False

    def balance_for_drums(self) -> bool:
        """Keep an already playing Riff below a newly started drum loop."""
        if not self.auto_balance.get() or self.bus_levels[0] <= DUET_LEVELS[0]:
            return True
        if not self.send_bus_level(0, DUET_LEVELS[0]):
            return False
        if self.mixer_window is not None and self.mixer_window.winfo_exists():
            self.mixer_window.levels[0].set(DUET_LEVELS[0])
        self.log("鼓＋Riff 平衡：吉他总线设为 72/127")
        return True

    def send_drums(self, data: bytes) -> bool:
        if self.draw_upload_busy:
            self.log("请等待双曲线上传完成，再发送鼓机设置")
            return False
        if self.port is None or not self.port.is_open:
            self.log("鼓机未发送：请先连接串口")
            return False
        try:
            if self.port.write(data) != len(data):
                raise IOError("鼓机命令未完整写入")
            return True
        except Exception as exc:
            self.log(f"鼓机发送失败：{exc}")
            # Invalidate local transport before closing; do not recursively
            # call stop/send on a failed serial handle.
            if getattr(self, "drum_window", None) is not None and self.drum_window.winfo_exists():
                self.drum_window.stop(send=False)
            failed_port, self.port = self.port, None
            try:
                failed_port.close()
            except Exception:
                pass
            self.disconnect()
            return False

    def send_effects(self, frames) -> bool:
        if self.draw_upload_busy:
            self.log("请等待双曲线上传完成，再发送效果设置")
            return False
        if self.port is None or not self.port.is_open:
            self.log("效果未发送：请先连接串口")
            return False
        try:
            if self.current_timbre not in (TIMBRE_GUITAR, TIMBRE_BASS) and not self.send_timbre(TIMBRE_GUITAR):
                return False
            for frame in frames:
                if self.port.write(frame) != len(frame):
                    raise IOError("效果命令未完整写入；未确认板端提交")
            self.log("吉他 / Bass 效果设置已发送（无 ACK）；保留当前音源，钢琴 / 手绘通路不受影响")
            return True
        except Exception as exc:
            self.log(f"效果发送失败：{exc}")
            self.disconnect()
            return False

    def send_master_effects(self, frames) -> bool:
        if self.draw_upload_busy:
            self.log("请等待双曲线上传完成，再发送总线效果设置")
            return False
        if self.port is None or not self.port.is_open:
            self.log("总线效果未发送：请先连接串口")
            return False
        try:
            for frame in frames:
                if self.port.write(frame) != len(frame):
                    raise IOError("总线效果命令未完整写入")
            self.log("总线合唱 / 延迟已发送（无 ACK）；覆盖所有乐器和鼓机")
            return True
        except Exception as exc:
            self.log(f"总线效果发送失败：{exc}")
            self.disconnect()
            return False

    def toggle_riff(self, riff_number: int = 1) -> None:
        if self.riff_playing and self.riff_active == riff_number:
            self.stop_riff("手动停止")
        else:
            if self.riff_playing:
                self.stop_riff("切换曲目")
            self.start_riff(riff_number)

    def start_riff(self, riff_number: int = 1) -> None:
        """Schedule the riff without blocking Tk, keeping every FX control live."""
        if riff_number not in RIFF_PROFILES:
            raise ValueError("unknown riff number")
        profile = RIFF_PROFILES[riff_number]
        if self.draw_upload_busy:
            self.log("双曲线上传中，暂不能播放 Riff")
            return
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return

        # Always synchronize the board before a riff.  The UART is one-way, so
        # after reconnecting the GUI cannot otherwise know whether the FPGA was
        # left in piano/mono mode; that state mismatch looked like silent play.
        # These commands do not touch the user's guitar FX registers.
        try:
            level_settle_ms = 0
            if (self.auto_balance.get() and self.drum_window is not None and
                    self.drum_window.winfo_exists() and self.drum_window.playing and
                    self.bus_levels[0] > DUET_LEVELS[0]):
                if not self.balance_for_drums():
                    return
                level_settle_ms = 5
            setup = make_timbre_command(TIMBRE_GUITAR) + make_mode_command(MODE_POLY4)
            if self.port.write(setup) != len(setup):
                raise IOError("Riff 模式初始化未完整写入")
            self.port.flush()
            self.current_timbre = TIMBRE_GUITAR
            self.current_mode = MODE_POLY4
            self.timbre_text.set("音色：木吉他")
            from ui_main import update_instrument
            update_instrument(self)
            self._update_note_display()
            self.mode_text.set("板端模式：" + ("Bass 8复音" if self.current_timbre == TIMBRE_BASS else "32复音"))
        except Exception as exc:
            self.log(f"Riff 启动失败：{exc}")
            self.disconnect()
            return

        self.stop_riff(log_reason=None)
        self.riff_token += 1
        token = self.riff_token
        self.riff_playing = True
        self.riff_active = riff_number
        self.riff_attack_count = 0
        active_button = {1: self.riff_button, 2: self.riff2_button, 3: self.riff3_button}[riff_number]
        active_button.configure(text=f"■ 停止 {profile['title']}")
        self.riff_status.set(f"{profile['title']} 正在播放 · 已同步木吉他 / 32复音")
        step_ms = 60000.0 / profile["bpm"] / profile["subdivision"]

        for step, voicing, accent in profile["events"]:
            after_id = self.after(
                level_settle_ms + round(step * step_ms),
                lambda v=voicing, a=accent, t=token, n=riff_number: self._play_riff_event(t, n, v, a),
            )
            self.riff_after_ids.append(after_id)
        self.riff_after_ids.append(
            self.after(level_settle_ms + round(profile["steps"] * step_ms), lambda t=token: self._finish_riff(t))
        )
        self.log(f"开始播放 {profile['title']}：{profile['description']}；首个和弦即将写入")

    def _play_riff_event(self, token: int, riff_number: int, voicing: str, accent: int) -> None:
        if token != self.riff_token or not self.riff_playing:
            return
        if self.port is None or not self.port.is_open:
            self.stop_riff("连接丢失")
            return
        try:
            velocity = max(1, min(127, int(self.velocity.get()) + accent))
            sustain = max(0, min(RIFF_SUSTAIN_MAX, int(self.riff_sustain.get())))
            frames = make_riff_attack_frames(riff_number, voicing, velocity, sustain)
            if self.port.write(frames) != len(frames):
                raise IOError("Riff 音符未完整写入")
            self.port.flush()
            self.riff_attack_count += 1
            profile = RIFF_PROFILES[riff_number]
            tail_ms = riff_tail_ms(riff_number, sustain, voicing)
            tail_label = "自然长尾" if tail_ms is None else f"尾音 {tail_ms} ms"
            self.riff_status.set(
                f"{profile['title']} · 已发送 {self.riff_attack_count}/{len(profile['events'])} · "
                f"{voicing} · {tail_label}"
            )
            if self.riff_attack_count == 1:
                self.log(f"{profile['title']} 首个和弦已写入 COM 口（{len(frames)} 字节）")
            if tail_ms is not None:
                attack_number = self.riff_attack_count
                tail_id = self.after(
                    tail_ms,
                    lambda t=token, a=attack_number: self._cut_riff_tail(t, a),
                )
                self.riff_after_ids.append(tail_id)
        except Exception as exc:
            self.log(f"Riff 播放失败：{exc}")
            self.stop_riff("播放失败")
            self.disconnect()

    def _cut_riff_tail(self, token: int, attack_number: int) -> None:
        """End the current chord cleanly without cutting a newer attack."""
        if (token != self.riff_token or not self.riff_playing or
                attack_number != self.riff_attack_count):
            return
        if self.port is None or not self.port.is_open:
            return
        try:
            frame = make_mode_command(MODE_POLY4)
            if self.port.write(frame) != len(frame):
                raise IOError("Riff 短延音切断命令未完整写入")
            self.port.flush()
        except Exception as exc:
            self.log(f"Riff 尾音切断失败：{exc}")
            self.stop_riff("播放失败")
            self.disconnect()

    def _finish_riff(self, token: int) -> None:
        if token != self.riff_token:
            return
        self.stop_riff("播放完成")

    def stop_riff(self, log_reason: str | None = "手动停止") -> None:
        was_playing = self.riff_playing
        self.riff_token += 1
        self.riff_playing = False
        self.riff_active = 0
        for after_id in self.riff_after_ids:
            try:
                self.after_cancel(after_id)
            except (tk.TclError, ValueError):
                pass
        self.riff_after_ids.clear()
        if hasattr(self, "riff_button"):
            self.riff_button.configure(text="▶ Riff 1 · 强节奏")
        if hasattr(self, "riff2_button"):
            self.riff2_button.configure(text="▶ Riff 2 · 慢速 4/4")
        if hasattr(self, "riff3_button"):
            self.riff3_button.configure(text="▶ Riff 3 · 铁轨")
        if hasattr(self, "riff_status"):
            self.riff_status.set(RIFF_IDLE_TEXT)
        if was_playing and log_reason:
            self.log(f"Riff {log_reason}")

    def send_test_chord(self) -> None:
        if self.draw_upload_busy:
            return
        if self.port is None or not self.port.is_open:
            messagebox.showwarning("未连接", "请先连接 Guitar Controller COM口。")
            return
        notes = ((6, 3), (5, 2), (4, 0), (3, 0))
        try:
            frames = make_mode_command(MODE_POLY4)
            frames += b"".join(
                make_command(CMD_PLUCK, string, fret, self.velocity.get())
                for string, fret in notes
            )
            self.port.write(frames)
            self.current_mode = MODE_POLY4
            self.mode_text.set("板端模式：" + ("Bass 8复音" if self.current_timbre == TIMBRE_BASS else "32复音"))
            self.log(f"TX {frames.hex(' ').upper()}  复音G和弦")
        except Exception as exc:
            self.log(f"复音和弦测试发送失败：{exc}")
            messagebox.showerror("发送失败", str(exc))
            self.disconnect()

    def handle_pitch_encoder_delta(self, field, detents, fine=False):
        """Future encoder events use the same bounds and steps as the UI."""
        value = self.pitch_control.handle_encoder_delta(field, detents, fine=fine)
        if self.pitch_page is not None and self.pitch_page.winfo_exists():
            self.pitch_page.sync()
        return value

    def show_page(self, key):
        from ui_pages import show_page
        return show_page(self, key)

    def show_notice(self, title, message):
        self._notice_text.set(str(title) + " · " + str(message))
        self._notice_bar.pack(fill="x", before=self.page_area)
        self.log(str(title) + ": " + str(message))

    def guitar_shortcut(self, event, command):
        if self.active_page != "guitar":
            return
        if event.widget.winfo_class() in ("TEntry", "Entry", "TCombobox", "TSpinbox", "TScale", "Text", "TButton", "TCheckbutton"):
            return
        command()
        return "break"

    def close(self) -> None:
        for name in ("pitch_page", "verification_page", "piano_keyboard", "effects_window", "space_effects_window", "mixer_window", "drum_window"):
            panel = getattr(self, name, None)
            if panel is not None and panel.winfo_exists():
                panel.close()
        self.disconnect()
        self.destroy()


def main() -> int:
    if serial is None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "缺少 pyserial",
            "请在工程目录运行：\npython -m pip install -r requirements.txt",
        )
        root.destroy()
        return 1
    app = GuitarController()
    if len(sys.argv) == 3 and sys.argv[1] == "--auto-connect":
        app.after(250, lambda: app.auto_connect(sys.argv[2]))
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
