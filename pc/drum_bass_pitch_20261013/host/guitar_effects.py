"""Guitar-only FX controls. Names describe voicings, not circuit emulations."""
from __future__ import annotations
import tkinter as tk
from ui_pages import EmbeddedPage
from tkinter import ttk

def control_frame(command, payload):
    frame=bytearray((0xA5,command,(payload>>16)&255,(payload>>8)&255,payload&255))
    checksum=0
    for value in frame:checksum ^= value
    frame.append(checksum)
    return bytes(frame)

AMPS = ("清音 / 原声旁路", "TS808 风格过载", "Plexi Crunch", "JCM800 风格失真",
        "Silver Jubilee / Slash Lead", "Fuzz Face 风格", "Octave Fuzz",
        "Treble Booster 高频推子", "Blues 低增益过载", "Mesa 高增益金属", "Rectifier 紧金属")
MODS = ("关闭", "Tremolo 音量颤音", "Vibrato 音高颤音", "Phaser 相移",
        "Flanger 镶边", "Auto Wah 自动哇音")

def effect_frames(amp=0, drive=64, tone=64, level=80, mix=127,
                  cabinet=True, gate=True, compressor=False,
                  modulation=0, rate=40, depth=64, threshold=32):
    values = (amp, drive, tone, level, mix, modulation, rate, depth, threshold)
    if any(type(v) is not int for v in values):
        raise ValueError("效果参数必须为整数")
    if not 0 <= amp < len(AMPS) or not 0 <= modulation < len(MODS):
        raise ValueError("未知效果")
    if any(not 0 <= v <= 127 for v in (drive,tone,level,mix,rate,depth,threshold)):
        raise ValueError("旋钮范围为 0..127")
    flags = int(bool(cabinet)) | int(bool(gate)) << 1 | int(bool(compressor)) << 2
    # Shadow registers; only COMMIT changes the audio configuration atomically.
    return [control_frame(0x40, (amp << 16) | (drive << 8) | tone),
            control_frame(0x41, (level << 16) | (mix << 8) | flags),
            control_frame(0x42, (modulation << 16) | (rate << 8) | depth),
            control_frame(0x43, threshold << 16), control_frame(0x44, 0)]

class GuitarEffects(EmbeddedPage):
    def __init__(self, controller, parent=None, section=False):
        super().__init__(controller, parent=parent, section=section)
        self.controller = controller
        self.vars = {k: tk.IntVar(value=v) for k,v in dict(drive=64,tone=64,level=80,
                     mix=127,rate=40,depth=64,threshold=32).items()}
        self.amp = tk.StringVar(value=AMPS[0])
        self.mod = tk.StringVar(value=MODS[0])
        self.cabinet=tk.BooleanVar(value=True)
        self.gate=tk.BooleanVar(value=True)
        self.compressor=tk.BooleanVar(value=False)
        self.live=tk.BooleanVar(value=True)
        self._live_after=None
        self.sustain_text=tk.StringVar()
        self.status=tk.StringVar(value="尚未发送；上电默认完全旁路。调整旋钮后点击发送。")
        from ui_panels import guitar_fx
        guitar_fx(self)
        for variable in (*self.vars.values(), self.amp, self.mod,
                         self.cabinet, self.gate, self.compressor):
            variable.trace_add("write", self._schedule_live_send)
        self._sustain_trace=controller.riff_sustain.trace_add("write", self._riff_sustain_changed)
        self._riff_sustain_changed()

    def _riff_sustain_changed(self, *_args):
        value=int(self.controller.riff_sustain.get())
        if value >= 127:
            text="127：恢复上一个版本的自然长尾；不做拍前清尾或定时切断。"
        elif value == 0:
            text="0：Riff 1 约190 ms，Riff 2 约290 ms；铁轨闷音70 ms／重和弦225 ms。"
        else:
            text=f"{value}：中间延音；下一次 Riff 和弦起即时生效。"
        self.sustain_text.set(text)

    def close(self):
        if self._live_after is not None:
            self.after_cancel(self._live_after)
            self._live_after=None
        self.controller.riff_sustain.trace_remove("write", self._sustain_trace)
        self.destroy()

    def _schedule_live_send(self, *_args):
        """Debounce control motion so a live tweak produces one atomic commit."""
        if not self.live.get():
            return
        if self._live_after is not None:
            self.after_cancel(self._live_after)
        self._live_after=self.after(90,self._send_live)

    def _send_live(self):
        self._live_after=None
        if self.winfo_exists() and self.live.get():
            self.send(live=True)

    def slash(self):
        self.amp.set(AMPS[4]); self.mod.set(MODS[0])
        for k,v in dict(drive=54,tone=48,level=72,mix=127,threshold=26).items(): self.vars[k].set(v)
        self.cabinet.set(True);self.gate.set(True);self.compressor.set(False)
        self.status.set("已载入建议值，尚未发送。先以单音试听；音源仍是现有合成吉他，并非拾音器录音。")

    def clean(self):
        self.amp.set(AMPS[0]);self.mod.set(MODS[0])
        self.gate.set(False);self.compressor.set(False)
        self.send()

    def send(self, live=False):
        settings={k:int(v.get()) for k,v in self.vars.items()}
        frames=effect_frames(amp=AMPS.index(self.amp.get()),modulation=MODS.index(self.mod.get()),
                             cabinet=self.cabinet.get(),gate=self.gate.get(),compressor=self.compressor.get(),**settings)
        ok=self.controller.send_effects(frames)
        if ok:
            prefix="实时设置" if live else "设置"
            self.status.set(f"{prefix}已发送（单向串口，无板端 ACK）；约 12 ms 淡出切换。")
        else:
            self.status.set("未完成发送，请检查连接 / 上传状态。")
