"""Two simultaneous freehand canvases embedded above the 88-key keyboard."""
from __future__ import annotations

import json
import math
import tkinter as tk
from tkinter import filedialog, ttk
from ui_notices import messagebox

from drawn_synth import ENV_POINTS, WAVE_POINTS, piano_envelope, position_to_time, time_to_position


class CurveCanvas(tk.Canvas):
    def __init__(self, parent, values, envelope=False, duration=lambda: 1400):
        super().__init__(parent, height=190, background="#F8FBFE", highlightthickness=0, cursor="crosshair")
        self.values = values
        self.envelope = envelope
        self.duration = duration
        self.last = None
        self.bind("<Configure>", lambda event: self.redraw())
        self.bind("<Button-1>", self.start)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", lambda event: setattr(self, "last", None))

    def bounds(self):
        return 38, 18, max(80, self.winfo_width() - 12), max(70, self.winfo_height() - 30)

    def sample_position(self, position):
        if self.envelope:
            position = position_to_time(position, self.duration()) / self.duration()
        return position * (len(self.values) - 1)

    def point(self, event):
        left, top, right, bottom = self.bounds()
        position = max(0, min(1, (event.x - left) / (right - left)))
        value = max(0, min(1, (bottom - event.y) / (bottom - top)))
        return round(self.sample_position(position)), value if self.envelope else 2 * value - 1

    def start(self, event):
        self.last = self.point(event)
        self.values[self.last[0]] = self.last[1]
        self.redraw()

    def drag(self, event):
        point = self.point(event)
        if self.last is None:
            self.last = point
        if point[0] == self.last[0]:
            self.values[point[0]] = point[1]
        else:
            first, last = sorted((self.last, point))
            for index in range(first[0], last[0] + 1):
                amount = (index - first[0]) / (last[0] - first[0])
                self.values[index] = first[1] + amount * (last[1] - first[1])
        self.last = point
        self.redraw()

    def redraw(self):
        self.delete("all")
        left, top, right, bottom = self.bounds()
        for value in (0, .25, .5, .75, 1):
            y = bottom - value * (bottom - top)
            label = value if self.envelope else 2 * value - 1
            self.create_line(left, y, right, y, fill="#E1EBF3")
            self.create_text(left - 5, y, text=f"{label:g}", anchor="e", fill="#657F94")
        if self.envelope:
            duration = self.duration()
            ticks = sorted(set(t for t in (0, 3, 20, 30, 80, 250, 600, duration) if t <= duration))
            last_x = -100
            for t in ticks:
                x = left + time_to_position(t, duration) * (right - left)
                self.create_line(x, top, x, bottom, fill="#E1EBF3")
                if x - last_x > 29 or t == duration:
                    self.create_text(x, bottom + 13, text=f"{t:g}", fill="#657F94")
                    last_x = x
        else:
            for position in (0, .25, .5, .75, 1):
                x = left + position * (right - left)
                self.create_line(x, top, x, bottom, fill="#E1EBF3")
                self.create_text(x, bottom + 13, text=f"{position:g}", fill="#657F94")
        points = []
        for pixel in range(max(2, int(right - left) + 1)):
            position = pixel / max(1, right - left)
            sample = self.sample_position(position)
            index = min(len(self.values) - 1, int(sample))
            fraction = sample - index
            value = self.values[index] * (1 - fraction) + self.values[min(index + 1, len(self.values) - 1)] * fraction
            normalized = value if self.envelope else (value + 1) / 2
            points.extend((left + pixel, bottom - normalized * (bottom - top)))
        self.create_line(*points, fill="#7861B8" if self.envelope else "#168C85", width=2)

    def smooth(self):
        previous = self.values[:]
        for index in range(1, len(previous) - 1):
            self.values[index] = (previous[index - 1] + 2 * previous[index] + previous[index + 1]) / 4
        self.redraw()


class DrawnSynthPanel(ttk.LabelFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, text="手绘合成 · 周期波表 × 每音独立幅度包络", padding=8)
        self.controller = controller
        self.duration = tk.StringVar(value="1400")
        self.status = tk.StringVar(value="先画两张曲线 → 上传并启用 → 用下方钢琴键选择频率。原吉他/钢琴音色保留。")
        self.wave = [math.sin(2 * math.pi * i / WAVE_POINTS) for i in range(WAVE_POINTS)]
        self.envelope = piano_envelope()
        settings = ttk.Frame(self)
        settings.pack(fill="x", pady=(0, 5))
        ttk.Label(settings, text="包络总时长 ms").pack(side="left")
        ttk.Spinbox(settings, from_=50, to=8000, increment=50, width=7,
                    textvariable=self.duration, command=self.redraw_envelope).pack(side="left", padx=5)
        ttk.Label(settings, text="起音区放大；时长改变会缩放整条曲线").pack(side="left", padx=8)
        ttk.Button(settings, text="保存两张曲线", command=self.save).pack(side="right", padx=3)
        ttk.Button(settings, text="载入", command=self.load).pack(side="right", padx=3)
        body = ttk.Frame(self)
        body.pack(fill="x")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        wave_box = ttk.Frame(body)
        env_box = ttk.Frame(body)
        wave_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        env_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ttk.Label(wave_box, text="波表：横轴一个周期 / 相位 0–1；纵轴 -1–+1").pack(anchor="w")
        ttk.Label(env_box, text="幅度包络：横轴时间 ms（非等距）；纵轴增益 0–1").pack(anchor="w")
        self.wave_canvas = CurveCanvas(wave_box, self.wave)
        self.env_canvas = CurveCanvas(env_box, self.envelope, True, self.duration_ms)
        self.wave_canvas.pack(fill="x", pady=3)
        self.env_canvas.pack(fill="x", pady=3)
        wave_tools = ttk.Frame(wave_box)
        wave_tools.pack(fill="x")
        for label, kind in (("正弦", "sine"), ("三角", "triangle"), ("锯齿", "saw"), ("方波", "square"), ("清空", "zero")):
            ttk.Button(wave_tools, text=label, width=5,
                       command=lambda k=kind: self.reset_wave(k)).pack(side="left", padx=2)
        ttk.Button(wave_tools, text="平滑", width=5, command=self.wave_canvas.smooth).pack(side="left", padx=2)
        env_tools = ttk.Frame(env_box)
        env_tools.pack(fill="x")
        ttk.Button(env_tools, text="AD 衰减示例", command=self.reset_envelope).pack(side="left", padx=3)
        ttk.Button(env_tools, text="清空（静音）", command=self.clear_envelope).pack(side="left", padx=3)
        ttk.Button(env_tools, text="平滑", command=self.env_canvas.smooth).pack(side="left", padx=3)
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        self.upload_button = ttk.Button(actions, style="Primary.TButton", text="发送两张表并启用手绘合成", command=self.upload)
        self.upload_button.pack(side="left", padx=3)
        ttk.Button(actions, text="恢复原钢琴 / 取消上传", command=self.restore).pack(side="left", padx=3)
        self.progress = ttk.Progressbar(actions, mode="determinate", length=180)
        self.progress.pack(side="right")
        ttk.Label(self, textvariable=self.status, wraplength=1100).pack(fill="x", pady=(4, 0))
        if controller.draw_project is not None:
            self.apply_project(controller.draw_project)
        self.duration.trace_add("write", lambda *_: self.redraw_envelope())

    def duration_ms(self):
        try:
            value = float(self.duration.get())
            return value if math.isfinite(value) and 50 <= value <= 8000 else 1400.0
        except ValueError:
            return 1400.0

    def redraw_envelope(self):
        if hasattr(self, "env_canvas"):
            self.env_canvas.redraw()

    def reset_wave(self, kind):
        for i in range(WAVE_POINTS):
            phase = i / WAVE_POINTS
            sine = math.sin(2 * math.pi * phase)
            self.wave[i] = sine if kind == "sine" else (2 / math.pi * math.asin(sine) if kind == "triangle"
                else (2 * phase - 1 if kind == "saw" else ((1 if phase < .5 else -1) if kind == "square" else 0)))
        self.wave_canvas.redraw()

    def reset_envelope(self):
        self.envelope[:] = piano_envelope()
        self.env_canvas.redraw()

    def clear_envelope(self):
        self.envelope[:] = [0.0] * ENV_POINTS
        self.env_canvas.redraw()

    def project(self):
        duration = float(self.duration.get())
        if not math.isfinite(duration) or not 50 <= duration <= 8000:
            raise ValueError("包络时长必须是 50–8000 ms")
        return {"format": "drawn-synth-v1", "duration_ms": duration,
                "wave": self.wave[:], "envelope": self.envelope[:]}

    def apply_project(self, data):
        if data.get("format") != "drawn-synth-v1" or len(data.get("wave", [])) != WAVE_POINTS or len(data.get("envelope", [])) != ENV_POINTS:
            raise ValueError("不是有效的双曲线合成项目")
        duration = float(data["duration_ms"])
        if not math.isfinite(duration) or not 50 <= duration <= 8000:
            raise ValueError("包络时长必须是 50–8000 ms")
        wave, envelope = [float(v) for v in data["wave"]], [float(v) for v in data["envelope"]]
        if any(not math.isfinite(v) or abs(v) > 1 for v in wave) or any(not math.isfinite(v) or not 0 <= v <= 1 for v in envelope):
            raise ValueError("曲线数值超出允许范围")
        self.wave[:] = wave
        self.envelope[:] = envelope
        self.duration.set(f"{duration:g}")
        self.wave_canvas.redraw()
        self.env_canvas.redraw()

    def save(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".json", filetypes=(("双曲线项目", "*.json"),))
        if path:
            try:
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(self.project(), handle, ensure_ascii=False, indent=2, allow_nan=False)
                self.status.set("两张曲线和总时长已保存。")
            except Exception as exc:
                messagebox.showerror("保存失败", str(exc), parent=self)

    def load(self):
        path = filedialog.askopenfilename(parent=self, filetypes=(("双曲线项目", "*.json"),))
        if path:
            try:
                with open(path, encoding="utf-8") as handle:
                    self.apply_project(json.load(handle))
                self.status.set("已载入；需重新上传，画布修改不会直接改变板端。")
            except Exception as exc:
                messagebox.showerror("载入失败", str(exc), parent=self)

    def upload(self):
        try:
            duration = float(self.duration.get())
            if not math.isfinite(duration) or not 50 <= duration <= 8000:
                raise ValueError("包络时长必须是 50–8000 ms")
            self.controller.draw_project = self.project()
            self.controller.send_drawn_synth(self.wave[:], self.envelope[:], duration, self.on_progress, self.on_done)
        except Exception as exc:
            messagebox.showerror("无法上传", str(exc), parent=self)

    def on_progress(self, done, total):
        if self.winfo_exists():
            self.upload_button.configure(state="disabled")
            self.progress["value"] = 100 * done / max(1, total)
            self.status.set(f"正在发送 {done}/{total} 包；上传期间琴键暂停。")

    def on_done(self, success, message):
        if self.winfo_exists():
            self.upload_button.configure(state="normal")
            self.status.set(message)

    def restore(self):
        sent = self.controller.restore_piano()
        self.upload_button.configure(state="normal")
        self.status.set("已发送恢复原钢琴命令（无ACK）；手绘曲线仍保留在画布。" if sent
                        else "已取消本机上传；串口未连接或发送失败，板端状态未知。曲线仍保留。")
