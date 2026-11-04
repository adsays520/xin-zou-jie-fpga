"""Drum layout; coordinate geometry and all original editing events retained."""
import tkinter as tk
from tkinter import ttk
from ui_theme import COLORS as C, window, card, button, scroll_body


def build(win):
    from drum_patterns import NAMES, KITS, PRESETS
    from drum_editor import ROW_HEIGHT
    window(win, '原声采样鼓机', '真实鼓单击采样 · 12 件乐器 · 4/4 × 4 小节 · 16 拍循环', 1340, 880, 1100, 860, 'teal')
    body = scroll_body(win, padding=(20, 0, 20, 16))
    top = card(body, padding=15)
    top.pack(fill='x', pady=(0, 12))
    row = ttk.Frame(top)
    row.pack(fill='x')
    ttk.Label(row, text='节奏预设', style='Muted.TLabel').pack(side='left')
    win.preset_box = ttk.Combobox(row, state='readonly', values=PRESETS, width=25)
    win.preset_box.set(PRESETS[0])
    win.preset_box.pack(side='left', padx=8)
    button(row, '载入预设', win.load_preset, 'Teal').pack(side='left')
    button(row, '预设直接播放', win.play_preset, 'Accent').pack(side='left', padx=8)
    ttk.Label(top, text='动＝底鼓 · 次＝踩镲 · 打＝军鼓；基础节奏按强弱拍循环，选择后可直接播放。',
              style='Muted.TLabel').pack(anchor='w', pady=(8, 0))
    row = ttk.Frame(top)
    row.pack(fill='x', pady=(12, 0))
    ttk.Label(row, text='BPM', style='Muted.TLabel').pack(side='left', padx=(18, 5))
    ttk.Spinbox(row, from_=30, to=300, textvariable=win.bpm, width=5).pack(side='left')
    ttk.Label(row, text='Swing %', style='Muted.TLabel').pack(side='left', padx=(15, 5))
    ttk.Spinbox(row, from_=0, to=50, textvariable=win.swing, width=4).pack(side='left')
    button(row, '应用速度', win.apply_tempo).pack(side='left', padx=8)
    ttk.Combobox(row, state='readonly', textvariable=win.kit, values=KITS, width=23).pack(side='right')
    row = ttk.Frame(top)
    row.pack(fill='x', pady=(12, 0))
    win.play_button = button(row, '▶ 上传并循环', win.start, 'Accent')
    win.play_button.pack(side='left')
    button(row, '■ 停止 / 静音', win.stop).pack(side='left', padx=8)
    button(row, '保存节奏', win.save, width=8).pack(side='left')
    button(row, '打开节奏', win.load, width=8).pack(side='left', padx=8)
    button(row, '复制第 1 小节到全部', win.copy_bar).pack(side='left')
    button(row, '清空', win.clear, width=4).pack(side='left', padx=8)
    row = ttk.Frame(top)
    row.pack(fill='x', pady=(12, 0))
    ttk.Label(row, text='节奏细分视图', style='Muted.TLabel').pack(side='left', padx=(0, 8))
    view = ttk.Combobox(row, state='readonly', textvariable=win.view,
                        values=('16格 / 每格1拍', '32格 / 八分音符', '64格 / 十六分音符'), width=21)
    view.pack(side='left')
    view.bind('<<ComboboxSelected>>', lambda e: win.redraw())
    gridbox = card(body, padding=14)
    gridbox.pack(fill='both', expand=True)
    gridbox.rowconfigure(0, weight=1)
    gridbox.columnconfigure(1, weight=1)
    side = ttk.Frame(gridbox)
    side.grid(row=0, column=0, sticky='nsw', padx=(0, 8))
    header = ttk.Frame(side, height=37)
    header.pack(fill='x')
    header.pack_propagate(False)
    ttk.Label(header, text='乐器 / 试听           音量    静音', style='Muted.TLabel').pack(anchor='w', pady=9)
    style = ttk.Style(win)
    style.configure('Audition.Teal.TButton', padding=(6, 3), font=('Microsoft YaHei UI', 9))
    style.configure('Drum.TSpinbox', padding=3, font=('Microsoft YaHei UI', 9))
    win.level_widgets, win.mute_widgets = [], []
    for voice, name in enumerate(NAMES):
        row = ttk.Frame(side)
        row.pack(fill='x')
        row.rowconfigure(0, minsize=ROW_HEIGHT)
        ttk.Button(row, text=name, width=16, style='Audition.Teal.TButton',
                   command=lambda v=voice: win.audition(v)).grid(row=0, column=0, sticky='w')
        spin = ttk.Spinbox(row, from_=0, to=127, textvariable=win.levels[voice], width=4,
                           style='Drum.TSpinbox', command=lambda v=voice: win.send_level(v))
        spin.grid(row=0, column=1, padx=5)
        spin.bind('<Return>', lambda e, v=voice: win.send_level(v))
        spin.bind('<FocusOut>', lambda e, v=voice: win.send_level(v))
        muted = tk.BooleanVar(value=False)
        check = ttk.Checkbutton(row, variable=muted, command=lambda v=voice, m=muted: win.mute(v, m.get()))
        check.grid(row=0, column=2, padx=(3, 0))
        win.level_widgets.append(spin)
        win.mute_widgets.append(check)
    grid = ttk.Frame(gridbox)
    grid.grid(row=0, column=1, sticky='nsew')
    win.canvas = tk.Canvas(grid, bg='#FFFFFF', highlightthickness=0, height=37+12*ROW_HEIGHT)
    win.canvas.pack(fill='both', expand=True)
    scroll = ttk.Scrollbar(grid, orient='horizontal', command=win.canvas.xview)
    scroll.pack(fill='x')
    win.canvas.configure(xscrollcommand=scroll.set)
    win.canvas.bind('<Configure>', lambda e: win.redraw())
    win.canvas.bind('<Button-1>', win.click)
    win.canvas.bind('<Button-3>', win.details)
    win.detail_slot = ttk.Frame(body, style='Page.TFrame')
    win.detail_slot.pack(fill='x', pady=(12, 0))
    row = ttk.Frame(body, style='Page.TFrame')
    row.pack(fill='x', pady=(12, 0))
    ttk.Label(row, text='新音力度', style='Page.TLabel').pack(side='left')
    ttk.Spinbox(row, from_=1, to=127, textvariable=win.velocity, width=5).pack(side='left', padx=8)
    ttk.Label(row, text='单击添加 / 清空整拍 · 右键编辑 1 / e / & / a', style='Page.TLabel').pack(side='left', padx=12)
    ttk.Label(body, textvariable=win.status, style='Page.TLabel', wraplength=1260).pack(anchor='w', pady=(9, 0))
    ttk.Label(body, text='算法合成 · 光标为上位机估计，串口无 ACK；修改节奏后需重新上传。',
              style='Page.TLabel').pack(anchor='w', pady=(4, 0))


def redraw(win):
    """Retain canvas items so each playback tick updates only changed cells."""
    from drum_editor import ROW_HEIGHT
    if not hasattr(win, 'canvas'):
        return
    columns, width, stride = win.geometry_values()
    geometry = (columns, width, stride)
    cache = getattr(win, '_visual_grid_cache', None)
    if cache is None or cache['geometry'] != geometry:
        win.canvas.delete('all')
        win.canvas.configure(scrollregion=(0, 0, columns*width, 37+12*ROW_HEIGHT))
        cache = {'geometry': geometry, 'items': {}}
        win._visual_grid_cache = cache
        for col in range(columns):
            step, x = col*stride, col*width
            if step % 16 == 0:
                win.canvas.create_text(x+4, 7, anchor='nw', fill='#657F94', text='小节 %d' % (step//16+1))
            label = str(step//4+1) if stride==4 or step%4==0 else '·'
            win.canvas.create_text(x+width/2, 26, fill='#4A6D8B', text=label)
            for voice in range(12):
                y = 37+voice*ROW_HEIGHT
                rect = win.canvas.create_rectangle(x+2,y+2,x+width-2,y+ROW_HEIGHT-4,
                                                    outline='#B7D6EA' if step%16==0 else '#DCE8F2')
                text = win.canvas.create_text(x+width/2,y+ROW_HEIGHT/2,font=('Segoe UI',9))
                cache['items'][(voice,col)] = [rect,text,None]
    for col in range(columns):
        step = col*stride
        current = win.cursor in range(step,step+stride)
        for voice in range(12):
            vals = win.pattern.cells[voice][step:step+stride]
            color = '#F5BD8A' if current else '#D6ECE6' if any(vals) else '#F5F9FD'
            label = ' '.join('●' if v>=80 else '○' if v else '·' for v in vals)
            ink = '#785431' if current else '#3F7E78' if any(vals) else '#7D9DB6'
            rect, text, previous = cache['items'][(voice,col)]
            value = (color,label,ink)
            if value != previous:
                if previous is None or color != previous[0]:
                    win.canvas.itemconfigure(rect,fill=color)
                if previous is None or (label,ink) != previous[1:]:
                    win.canvas.itemconfigure(text,text=label,fill=ink)
                cache['items'][(voice,col)][2] = value
