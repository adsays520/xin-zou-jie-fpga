"""Tk editor; sound and sample-clock sequencing live on the FPGA."""
from __future__ import annotations
import time
import tkinter as tk
from ui_pages import EmbeddedPage
from tkinter import ttk, filedialog
from ui_notices import messagebox
from drum_patterns import Pattern, NAMES, KITS, PRESETS, preset, frame, tempo_frame, hit_frame
ROW_HEIGHT = 36

class DrumEditor(EmbeddedPage):
    def __init__(self, controller, parent=None, section=False):
        super().__init__(controller, parent=parent, section=section)
        self.controller = controller
        self.pattern = preset(PRESETS[0])
        self.bpm = tk.IntVar(value=self.pattern.bpm)
        self.swing = tk.IntVar(value=self.pattern.swing)
        self.kit = tk.StringVar(value=KITS[self.pattern.kit])
        self.view = tk.StringVar(value="16格 / 每格1拍")
        self.velocity = tk.IntVar(value=100)
        self.status = tk.StringVar(value="默认16格＝16拍。右键格子编辑4个十六分音符；左键添加／清空整拍。")
        self.playing = False; self.uploading = False; self.token = 0; self.after_id = None
        self.upload_after = None; self.cursor = -1; self.muted = [False] * 12
        self.levels = [tk.IntVar(value=v) for v in self.pattern.levels]
        from ui_drums import build
        build(self)
        self.redraw()

    def sync(self):
        # Validate an entire candidate before mutating the running clock model.
        # Invalid typed input (e.g. BPM=0) must leave playback state valid.
        candidate = Pattern(self.pattern.name, self.bpm.get(), self.swing.get(),
                            KITS.index(self.kit.get()), self.pattern.cells,
                            [v.get() for v in self.levels])
        candidate.validate()
        self.pattern.bpm = candidate.bpm; self.pattern.swing = candidate.swing
        self.pattern.kit = candidate.kit; self.pattern.levels = candidate.levels

    def send(self, data):
        return self.controller.send_drums(data)

    def send_level(self, voice):
        try:
            value = self.levels[voice].get()
            if not 0 <= value <= 127: raise ValueError("音量须为 0..127")
            self.send(frame(0x57, voice, 0 if self.muted[voice] else value))
        except (ValueError, tk.TclError) as exc: self.status.set(str(exc))

    def mute(self, voice, muted):
        self.muted[voice] = muted; self.send_level(voice)

    def audition(self, voice):
        try:
            self.sync()
            if self.muted[voice]:
                self.status.set("该轨已静音；取消静音后可试听。")
                return
            self.send(frame(0x56, self.pattern.kit) + frame(0x57, voice, self.levels[voice].get()) + hit_frame(voice, self.velocity.get()))
        except (ValueError, tk.TclError) as exc: self.status.set(str(exc))

    def apply_tempo(self):
        try:
            self.sync()
            if self.send(tempo_frame(self.pattern.bpm, self.pattern.swing)):
                self.status.set(f"已发送 {self.pattern.bpm} BPM / Swing {self.pattern.swing}%（无ACK）")
        except (ValueError, tk.TclError) as exc: self.status.set(str(exc))

    def geometry_values(self):
        columns = (16, 32, 64)[("16格 / 每格1拍", "32格 / 八分音符", "64格 / 十六分音符").index(self.view.get())]
        width = max(48 if columns == 16 else 29, max(1, self.canvas.winfo_width()) / columns)
        return columns, width, 64 // columns

    def redraw(self):
        from ui_drums import redraw
        redraw(self)


    def position(self, event):
        columns, width, stride = self.geometry_values()
        col = int(self.canvas.canvasx(event.x) // width); voice = int((event.y - 37) // ROW_HEIGHT)
        return (voice, col * stride, stride) if 0 <= col < columns and 0 <= voice < 12 else None

    def click(self, event):
        pos = self.position(event)
        if pos is None: return
        try:
            velocity = self.velocity.get()
            if not 1 <= velocity <= 127: raise ValueError("力度须为1..127")
            v, step, stride = pos
            values = self.pattern.cells[v][step:step + stride]
            self.pattern.cells[v][step:step + stride] = [0] * stride if any(values) else [velocity] + [0] * (stride - 1)
            self.status.set("节奏已编辑；点击“上传并循环”将新节奏发送到FPGA。")
            self.redraw()
        except (ValueError, tk.TclError) as exc: self.status.set(str(exc))

    def details(self, event):
        pos = self.position(event)
        if pos is None: return
        v, step, _ = pos; base = (step // 4) * 4
        from ui_theme import card, button
        for child in self.detail_slot.winfo_children(): child.destroy()
        box = card(self.detail_slot, f"{NAMES[v]} · 第{base // 4 + 1}拍细分", accent="teal", padding=14)
        box.pack(fill="x")
        values = [tk.IntVar(value=x) for x in self.pattern.cells[v][base:base + 4]]
        self.detail_values = values
        ttk.Label(box, text="1 / e / & / a；0＝空，1–127＝力度").pack(anchor="w")
        row = ttk.Frame(box); row.pack(fill="x", pady=(10, 0))
        for label, value in zip(("1", "e", "&", "a"), values):
            ttk.Label(row, text=label).pack(side="left", padx=(0, 5))
            ttk.Spinbox(row, from_=0, to=127, textvariable=value, width=5).pack(side="left", padx=(0, 16))
        def accept():
            try:
                result = [x.get() for x in values]
                if any(not 0 <= x <= 127 for x in result): raise ValueError("力度须为0..127")
                self.pattern.cells[v][base:base + 4] = result
                box.destroy(); self.redraw()
                self.status.set("细分已应用；重新上传后生效。")
            except (ValueError, tk.TclError) as exc: self.status.set(str(exc))
        self.apply_detail = accept
        button(row, "应用", accept, "Teal").pack(side="right")
        button(row, "取消", box.destroy).pack(side="right", padx=8)
        self.after_idle(lambda: self._scroll_canvas.yview_moveto(1))

    def replace(self, pattern):
        self.stop(); self.pattern = pattern
        self.bpm.set(pattern.bpm); self.swing.set(pattern.swing); self.kit.set(KITS[pattern.kit])
        for var, level in zip(self.levels, pattern.levels): var.set(level)
        self.status.set(f"已载入 {pattern.name} · {pattern.bpm} BPM · 4/4 × 4小节")
        self.redraw()

    def load_preset(self): self.replace(preset(self.preset_box.get()))
    def play_preset(self):
        self.load_preset()
        self.start()
    def clear(self):
        try:
            self.sync()
            self.replace(Pattern(bpm=self.pattern.bpm, swing=self.pattern.swing,
                                 kit=self.pattern.kit, levels=self.pattern.levels.copy()))
        except (ValueError, tk.TclError) as exc: self.status.set(str(exc))
    def copy_bar(self):
        for row in self.pattern.cells: row[:] = row[:16] * 4
        self.redraw(); self.status.set("已将第1小节复制到第2–4小节；重新上传后生效。")

    def save(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".json", filetypes=[("鼓机节奏", "*.json")])
        if path:
            try: self.sync(); self.pattern.save(path); self.status.set("节奏已保存")
            except Exception as exc: messagebox.showerror("保存失败", str(exc), parent=self)
    def load(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("鼓机节奏", "*.json")])
        if path:
            try: self.replace(Pattern.load(path))
            except Exception as exc: messagebox.showerror("打开失败", str(exc), parent=self)

    def start(self):
        if self.uploading: return
        try: self.sync(); packets = self.pattern.upload_frames()
        except (ValueError, tk.TclError) as exc: self.status.set(str(exc)); return
        if not self.controller.port or not self.controller.port.is_open:
            self.status.set("请先在主窗口连接 JTAG/UART 串口。"); return
        if self.controller.draw_upload_busy:
            self.status.set("请等待双曲线上传完成。"); return
        self.stop(); self.token += 1; token = self.token; self.uploading = True
        if getattr(self.controller, "riff_playing", False) and hasattr(self.controller, "balance_for_drums"):
            if not self.controller.balance_for_drums():
                self.uploading = False
                self.status.set("吉他/鼓平衡发送失败，未启动鼓机。")
                return
        self.play_button.configure(state="disabled"); self.status.set("正在上传4小节节奏…")
        index = 0
        def batch():
            nonlocal index
            self.upload_after = None
            if token != self.token: return
            data = b"".join(packets[index:index + 24])
            if not self.send(data): self.stop(send=False); self.status.set("上传失败，未启动循环。"); return
            index += 24
            if index < len(packets):
                self.upload_after = self.after(10, batch)
            else:
                for v, muted in enumerate(self.muted):
                    if muted and not self.send(frame(0x57, v, 0)): self.stop(send=False); return
                if not self.send(frame(0x52, 1)): self.stop(send=False); return
                self.uploading = False; self.playing = True; self.play_button.configure(state="normal")
                self.cursor = 0; self.next_cursor = time.monotonic() + self.pattern.step_seconds(0); self.update_cursor(token)
                self.status.set(f"循环命令已发送（无ACK）· {self.pattern.bpm} BPM · 16拍／4小节；光标为估计值。")
        batch()

    def update_cursor(self, token):
        self.after_id = None
        if token != self.token or not self.playing: return
        now = time.monotonic()
        while self.next_cursor <= now:
            self.cursor = (self.cursor + 1) % 64
            self.next_cursor += self.pattern.step_seconds(self.cursor)
        self.redraw(); self.after_id = self.after(25, lambda: self.update_cursor(token))

    def stop(self, send=True):
        self.token += 1; self.playing = False; self.uploading = False
        for attr in ("after_id", "upload_after"):
            ident = getattr(self, attr, None)
            if ident:
                try: self.after_cancel(ident)
                except tk.TclError: pass
                setattr(self, attr, None)
        if send and self.controller.port and self.controller.port.is_open: self.send(frame(0x52, 0))
        self.cursor = -1; self.play_button.configure(state="normal"); self.redraw()
        self.status.set("已停止；板端停止命令为单向发送。")

    def close(self): self.stop(); self.destroy()
