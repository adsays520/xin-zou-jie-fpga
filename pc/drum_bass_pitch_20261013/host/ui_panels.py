"""Visual builders using the original variables and command callbacks."""
import tkinter as tk
from tkinter import ttk
from ui_theme import COLORS as C, window, card, button, parameter, scroll_body


def guitar_fx(win):
    from guitar_effects import AMPS, MODS
    window(win, '电吉他 / Bass 效果', '放大 / 失真 / 箱体 / 调制 · 处理吉他 / Bass', 870, 810, 790, 770, 'violet')
    body = scroll_body(win)
    controls = card(body, '放大与失真', accent='violet')
    controls.pack(fill='x')
    ttk.Combobox(controls, textvariable=win.amp, values=AMPS, state='readonly').pack(fill='x', pady=(0, 12))
    grid = ttk.Frame(controls)
    grid.pack(fill='x')
    for col in (0, 1):
        grid.columnconfigure(col, weight=1, uniform='fx')
    labels = [('drive', 'Drive', '相对预设 ±12 dB'), ('tone', 'Tone', '3–8 kHz'),
              ('level', '输出 Level', '0 静音 / 含预设补偿'), ('mix', '失真干湿 Mix', '干声已对齐')]
    for i, (key, title, hint) in enumerate(labels):
        frame = parameter(grid, title, win.vars[key], style='Warm.Horizontal.TScale' if key=='drive' else 'Horizontal.TScale')
        frame.grid(row=i//2, column=i%2, sticky='ew', padx=(0, 14) if i%2==0 else (14, 0), pady=(0, 13))
        ttk.Label(frame, text=hint, style='Muted.TLabel').pack(anchor='w', pady=(5, 0))
    mod = card(body, '调制与延音', accent='teal', padding=16)
    mod.pack(fill='x', pady=12)
    ttk.Combobox(mod, textvariable=win.mod, values=MODS, state='readonly').pack(fill='x', pady=(0, 10))
    grid = ttk.Frame(mod)
    grid.pack(fill='x')
    for col in (0, 1):
        grid.columnconfigure(col, weight=1, uniform='mod')
    for i, (key, label) in enumerate([('rate', '调制速率 · 0.2–8 Hz'), ('depth', '调制深度'), ('threshold', '门限 · 约 −78 至 −40 dBFS')]):
        frame = parameter(grid, label, win.vars[key], style='Teal.Horizontal.TScale')
        frame.grid(row=i//2, column=i%2, sticky='ew', padx=(0, 14) if i%2==0 else (14, 0), pady=(0, 12))
    parameter(grid, 'Riff 延音 · 短尾 ↔ 自然长尾', win.controller.riff_sustain,
              style='Warm.Horizontal.TScale').grid(row=1, column=1, sticky='ew', padx=(14, 0), pady=(0, 12))
    ttk.Label(mod, textvariable=win.sustain_text, style='Muted.TLabel', wraplength=780).pack(anchor='w')
    ttk.Label(mod, text='自动哇音：Depth 控制包络灵敏度，Rate 不生效；调制一次选一种。',
              style='Muted.TLabel').pack(anchor='w', pady=(5, 0))
    options = ttk.Frame(body, padding=(8, 2))
    options.pack(fill='x')
    for label, var in [('箱体滤波（失真）', win.cabinet), ('平滑噪声门', win.gate),
                       ('压缩 / 延音', win.compressor), ('实时试听（拖动自动发送）', win.live)]:
        ttk.Checkbutton(options, text=label, variable=var).pack(side='left', padx=(0, 14))
    actions = ttk.Frame(body, style='Page.TFrame')
    actions.pack(fill='x', pady=12)
    button(actions, 'Slash Lead 建议值', win.slash, 'Violet').pack(side='left')
    button(actions, '恢复完全清音', win.clean).pack(side='left', padx=8)
    button(actions, '发送设置 · 保持吉他 / Bass', win.send, 'Primary').pack(side='right')
    ttk.Label(body, textvariable=win.status, style='Page.TLabel', wraplength=790).pack(anchor='w')
    ttk.Label(body, text='品牌为调音方向，不是原机电路复刻。先降低耳机音量，再发送试听。',
              style='Page.TLabel').pack(anchor='w', pady=(5, 0))


def mixer(win):
    from performance_mixer import BUS_NAMES, DUET_LEVELS
    if not win._section:
        window(win, '演奏混音', '三路独立音量 · 0–127 · 鼓件音量在鼓机页面调节', 650, 650, 610, 620, 'orange')
    body = ttk.Frame(win, style='Page.TFrame', padding=0 if win._section else (20, 0, 20, 18))
    body.pack(fill='both', expand=True)
    if win._section:
        ttk.Label(body, text='演奏混音', style='Section.TLabel').pack(anchor='w', pady=(0, 12))
    names = [('吉他 / Bass', 'Warm', 'orange'), ('钢琴 / 手绘', 'Violet', 'violet'), ('鼓机总线', 'Teal', 'teal')]
    for bus, (name, tint, accent) in enumerate(names):
        block = card(body, padding=15)
        block.pack(fill='x', pady=(0, 12))
        header = ttk.Frame(block)
        header.pack(fill='x', pady=(0, 8))
        tk.Frame(header, background=C[accent], width=4, height=20).pack(side='left', padx=(0, 9))
        ttk.Label(header, text=name, style='Section.TLabel').pack(side='left')
        button(header, '静音', lambda b=bus: win.set_level(b, 0)).pack(side='right')
        ttk.Label(header, textvariable=win.levels[bus], style='Value.TLabel', width=4).pack(side='right', padx=12)
        ttk.Scale(block, from_=0, to=127, orient='horizontal', variable=win.levels[bus],
                  style=tint+'.Horizontal.TScale', command=lambda _v, b=bus: win.schedule(b)).pack(fill='x')
    actions = ttk.Frame(body, style='Page.TFrame')
    actions.pack(fill='x', pady=(0, 12))
    button(actions, '鼓＋Riff 平衡', lambda: win.preset(DUET_LEVELS), 'Warm').pack(side='left', fill='x', expand=True)
    button(actions, '全部总线 127', lambda: win.preset((127, 127, 127))).pack(side='left', fill='x', expand=True, padx=(10, 0))
    block = card(body, padding=14)
    block.pack(fill='x')
    ttk.Checkbutton(block, text='鼓机播放时启动 Riff 自动压低吉他', variable=win.controller.auto_balance).pack(anchor='w')
    ttk.Label(block, text='R5 位流：鼓机独立预增益约 +12 dB，并有立体声峰值保护。鼓总线滑块仍是后级音量；合奏请避免所有总线同时拉满。',
              style='Muted.TLabel', wraplength=570).pack(anchor='w', pady=(5, 0))
    ttk.Label(body, textvariable=win.status, style='Page.TLabel', wraplength=590).pack(anchor='w', pady=(12, 0))


def space_fx(win):
    if not win._section:
        window(win, '合唱 / 延迟', '最终立体声混音后的独立效果 · 合唱与延迟可同时使用', 800, 560, 760, 540, 'violet')
    body = ttk.Frame(win, style='Page.TFrame', padding=0 if win._section else (20, 0, 20, 18))
    body.pack(fill='both', expand=True)
    if win._section:
        ttk.Label(body, text='合唱 / 延迟', style='Section.TLabel').pack(anchor='w', pady=(0, 12))
    blocks = ttk.Frame(body, style='Page.TFrame')
    blocks.pack(fill='x')
    for col, (title, tint, accent, labels) in enumerate([
        ('立体声合唱', 'Teal', 'teal', [('chorus_mix', '合唱干湿', 127), ('chorus_rate', '合唱速率 · 0.2–8 Hz', 127), ('chorus_depth', '合唱深度', 127)]),
        ('延迟', 'Violet', 'violet', [('delay_mix', '延迟干湿', 127), ('delay_time', '延迟时间 · 约 50–643 ms', 127), ('delay_feedback', '延迟反馈 · 最高 75%', 96)])]):
        blocks.columnconfigure(col, weight=1, uniform='space')
        block = card(blocks, title, accent)
        block.grid(row=0, column=col, sticky='nsew', padx=(0, 6) if col==0 else (6, 0))
        for key, label, maximum in labels:
            parameter(block, label, win.vars[key], maximum, tint+'.Horizontal.TScale').pack(fill='x', pady=(10, 18))
    live = ttk.Frame(body, style='Page.TFrame')
    live.pack(fill='x', pady=(14, 0))
    ttk.Checkbutton(live, text='实时试听（松开滑块后发送）', variable=win.live).pack(anchor='w')
    actions = ttk.Frame(body, style='Page.TFrame')
    actions.pack(fill='x', pady=14)
    button(actions, '硬摇滚空间', win.hard_rock, 'Violet').pack(side='left')
    button(actions, '全部关闭', win.off).pack(side='left', padx=8)
    button(actions, '发送总线效果', win.send, 'Primary').pack(side='right')
    ttk.Label(body, textvariable=win.status, style='Page.TLabel', wraplength=745).pack(anchor='w')
