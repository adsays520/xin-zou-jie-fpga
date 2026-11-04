"""Embedded guitar pitch control and encoder rehearsal page."""
from dataclasses import replace
import json
import math
import time
import tkinter as tk
from tkinter import ttk, filedialog
from guitar_pitch import LIMITS, PitchSettings
from ui_pages import EmbeddedPage
from ui_theme import card, button, scroll_body

LABELS = {'slide_range_cents': '滑音范围（±音分）', 'slide_ms': '滑音时间（ms）',
          'vibrato_depth_cents': '颤音深度（±音分）', 'vibrato_rate_hz': '颤音速度（Hz）'}


class PitchPage(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.model = controller.pitch_control
        self.vars = {key: tk.DoubleVar(value=getattr(self.model.settings, key)) for key in LIMITS}
        self.value_labels = {key: tk.StringVar() for key in LIMITS}
        self.vibrato = tk.BooleanVar(value=False)
        self.encoder_target = tk.StringVar(value=LABELS['slide_range_cents'])
        self.fine = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value='上位机控制预览 · 板端吉他变调待接入')
        self.note = tk.StringVar()
        self.live = tk.StringVar()
        self.bounds = tk.StringVar()
        self.position = tk.DoubleVar(value=0)
        body = scroll_body(self, padding=(22, 18, 22, 18))
        ttk.Label(body, text='吉他滑音与音高颤音', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='当前仅上位机预览 · 100 音分 = 1 半音 · 1200 音分 = 1 八度', style='Page.TLabel').pack(anchor='w', pady=(4, 12))
        controls = card(body, '音高变化范围', accent='violet', padding=16)
        controls.pack(fill='x', pady=(0, 12))
        fields = ttk.Frame(controls)
        fields.pack(fill='x')
        for row, key in enumerate(LIMITS):
            ttk.Label(fields, text=LABELS[key], style='Muted.TLabel').grid(row=row, column=0, sticky='w', pady=6)
            ttk.Scale(fields, from_=LIMITS[key][0], to=LIMITS[key][1], variable=self.vars[key],
                      command=lambda value, k=key: self.configure_value(k, value)).grid(row=row, column=1, sticky='ew', padx=14)
            ttk.Label(fields, textvariable=self.value_labels[key], width=9, style='Value.TLabel').grid(row=row, column=2, sticky='e')
        fields.columnconfigure(1, weight=1)
        gestures = card(body, '演奏动作预览', accent='teal', padding=16)
        gestures.pack(fill='x', pady=(0, 12))
        row = ttk.Frame(gestures); row.pack(fill='x')
        for text, position in [('向下滑', -1), ('回到原音', 0), ('向上滑', 1)]:
            button(row, text, lambda p=position: self.slide(p), 'Teal').pack(side='left', padx=(0, 8))
        ttk.Checkbutton(row, text='启用音高颤音', variable=self.vibrato, command=self.toggle_vibrato).pack(side='left', padx=12)
        button(row, '停止并归零', self.stop).pack(side='right')
        ttk.Label(gestures, text='滑音目标位置 · −1 向下 / 0 原音 / +1 向上', style='Muted.TLabel').pack(anchor='w', pady=(12, 4))
        ttk.Scale(gestures, from_=-1, to=1, variable=self.position,
                  command=lambda value: self.slide(float(value))).pack(fill='x')
        encoder = card(body, '旋转编码器模拟', padding=16)
        encoder.pack(fill='x', pady=(0, 12))
        row = ttk.Frame(encoder); row.pack(fill='x')
        ttk.Combobox(row, state='readonly', values=list(LABELS.values()), textvariable=self.encoder_target,
                     width=25).pack(side='left')
        button(row, '↶  −1 格', lambda: self.encoder(-1)).pack(side='left', padx=8)
        button(row, '↷  +1 格', lambda: self.encoder(1)).pack(side='left')
        ttk.Checkbutton(row, text='精调（1/5 步长）', variable=self.fine).pack(side='left', padx=12)
        preview = card(body, '音高轨迹', accent='violet', padding=16)
        preview.pack(fill='x', pady=(0, 12))
        ttk.Label(preview, textvariable=self.note, style='Value.TLabel').pack(anchor='w')
        ttk.Label(preview, textvariable=self.live, style='Page.TLabel').pack(anchor='w', pady=5)
        ttk.Label(preview, textvariable=self.bounds, style='Muted.TLabel').pack(anchor='w')
        self.canvas = tk.Canvas(preview, height=160, background='#F8FBFE', highlightthickness=0)
        self.canvas.pack(fill='x', pady=(10, 0))
        self.canvas.bind('<Configure>', lambda _e: self.draw_curve())
        row = ttk.Frame(body, style='Page.TFrame'); row.pack(fill='x')
        button(row, '保存参数', self.save).pack(side='left')
        button(row, '载入参数', self.load).pack(side='left', padx=8)
        button(row, '恢复默认', self.defaults).pack(side='left')
        ttk.Label(body, textvariable=self.status, style='Page.TLabel', wraplength=900).pack(anchor='w', pady=(12, 0))
        self.sync()
        self.after(20, self.tick)

    def sync(self):
        self.position.set(self.model.slide_position)
        for key in LIMITS:
            value = getattr(self.model.settings, key)
            self.vars[key].set(value)
            self.value_labels[key].set(f'{value:.2f}' if key == 'vibrato_rate_hz' else f'{value:.0f}')
        self.vibrato.set(self.model.vibrato_enabled)
        self.draw_curve()

    def configure_value(self, key, value):
        self.model.set_settings(replace(self.model.settings, **{key: float(value)}))
        self.sync()

    def guitar_active(self):
        from guitar_controller import TIMBRE_GUITAR
        if self.controller.current_timbre != TIMBRE_GUITAR:
            self.status.set('请选择木吉他后预览；此音高控制只用于吉他。')
            return False
        return True

    def slide(self, position):
        if self.guitar_active():
            self.position.set(position)
            self.model.set_slide_position(position)
            self.status.set('滑音轨迹已启动 · 上位机预览，板端吉他变调待接入')

    def toggle_vibrato(self):
        if self.guitar_active():
            self.model.enable_vibrato(self.vibrato.get())
            self.status.set('音高颤音参数已应用到预览 · 板端吉他变调待接入')
        else:
            self.vibrato.set(False)
        self.draw_curve()

    def encoder(self, delta):
        key = next(key for key, label in LABELS.items() if label == self.encoder_target.get())
        self.controller.handle_pitch_encoder_delta(key, delta, fine=self.fine.get())
        self.sync()

    def stop(self):
        self.model.reset()
        self.position.set(0)
        self.sync()
        self.status.set('滑音与颤音已归零 · 参数范围保留')

    def tick(self):
        if self.controller.active_page == 'pitch':
            from guitar_controller import note_name, note_frequency
            string, fret = self.controller.selected_string.get(), self.controller.selected_fret.get()
            base = note_frequency(string, fret)
            sample = self.model.snapshot(base)
            lo, hi = self.model.frequency_bounds(base)
            self.note.set(f'参考吉他基音：{string} 弦 {fret} 品 · {note_name(string, fret)} · {base:.3f} Hz')
            self.live.set(f'当前音高：{sample["frequency_hz"]:.3f} Hz  /  {sample["cents"]:+.2f} 音分')
            self.bounds.set(f'完整可调范围：{lo:.3f}–{hi:.3f} Hz（滑音 ±{self.model.settings.slide_range_cents:.0f} + 颤音 ±{self.model.settings.vibrato_depth_cents:.0f} 音分）')
            self.vibrato.set(self.model.vibrato_enabled)
        self.after(20, self.tick)

    def draw_curve(self):
        canvas = self.canvas
        canvas.delete('all')
        width, height = max(200, canvas.winfo_width()), 160
        settings = self.model.settings
        scale = max(50, settings.slide_range_cents + settings.vibrato_depth_cents)
        duration = max(1.0, settings.slide_ms / 1000 * 1.25)
        canvas.create_line(28, 80, width-12, 80, fill='#B8CEDF')
        points = []
        for i in range(241):
            t = duration * i / 240
            x = 28 + (width-40) * i / 240
            u = min(1, t / (settings.slide_ms / 1000))
            cents = settings.slide_range_cents * u*u*(3-2*u)
            if self.model.vibrato_enabled:
                cents += settings.vibrato_depth_cents * math.sin(2 * math.pi * settings.vibrato_rate_hz * t)
            points.extend((x, 80-60*cents/scale))
        canvas.create_line(*points, fill='#7861B8', width=2)
        canvas.create_text(30, 148, text=f'向上滑示例 · 0–{duration:.2f} s', anchor='w', fill='#657F94')
        canvas.create_text(width-14, 148, text=f'±{scale:.0f} 音分', anchor='e', fill='#657F94')

    def save(self):
        filename = filedialog.asksaveasfilename(parent=self.controller, defaultextension='.json',
                    filetypes=[('音高参数', '*.json')], initialfile='guitar_pitch.json')
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.model.settings.to_dict(), f, ensure_ascii=False, indent=2)
                self.status.set('音高参数已保存')
            except OSError as exc:
                self.status.set(f'保存失败：{exc}')

    def load(self):
        filename = filedialog.askopenfilename(parent=self.controller, filetypes=[('音高参数', '*.json')])
        if filename:
            try:
                with open(filename, encoding='utf-8') as f:
                    settings = PitchSettings.from_dict(json.load(f))
                self.model.set_settings(settings)
                self.sync()
                self.status.set('音高参数已载入')
            except (OSError, ValueError, TypeError) as exc:
                self.status.set(f'载入失败：{exc}')

    def defaults(self):
        self.stop()
        self.model.set_settings(PitchSettings())
        self.sync()

    def close(self):
        self.model.reset()
        self.controller.pitch_page = None
        self.destroy()
