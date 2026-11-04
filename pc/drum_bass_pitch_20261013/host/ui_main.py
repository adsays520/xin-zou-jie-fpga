"""Layout A: a calm blue workspace with restrained instrument accents."""
import tkinter as tk
from tkinter import ttk
from ui_theme import COLORS as C, install, card, button


def build(app):
    # Import here so the controller can retain its public protocol module.
    from guitar_controller import CMD_PLUCK, MODE_MONO, MODE_POLY4, TIMBRE_GUITAR, TIMBRE_BASS, OPEN_NAMES, note_name
    from ui_pages import build_shell
    body = build_shell(app)
    heading = ttk.Frame(body, style='Page.TFrame')
    heading.pack(fill='x', pady=(0, 15))
    ttk.Label(heading, text='吉他演奏', style='Title.TLabel').pack(side='left')
    button(heading, '滑音 / 颤音', lambda: app.show_page('pitch'), 'Violet').pack(side='right')
    button(heading, 'G 和弦测试', app.send_test_chord).pack(side='right', padx=8)
    overview = ttk.Frame(body, style='Page.TFrame')
    overview.pack(fill='x', pady=(0, 14))
    for i, weight in enumerate((24, 25, 51)):
        overview.columnconfigure(i, weight=weight, uniform='overview')
    current = card(overview, '当前音符', padding=16)
    current.grid(row=0, column=0, sticky='nsew', padx=(0, 7))
    app._large_note = tk.StringVar(value='E2')
    app._note_detail = tk.StringVar(value='6 弦 · 0 品 · 82.410000 Hz')
    ttk.Label(current, textvariable=app._large_note, style='Note.TLabel').pack(anchor='w')
    ttk.Label(current, textvariable=app._note_detail, style='Muted.TLabel').pack(anchor='w', pady=(0, 9))
    dynamics = ttk.Frame(current)
    dynamics.pack(fill='x')
    ttk.Label(dynamics, text='力度', style='Muted.TLabel').pack(side='left')
    ttk.Label(dynamics, textvariable=app.velocity, style='Value.TLabel').pack(side='right')
    ttk.Scale(current, from_=1, to=127, variable=app.velocity, orient='horizontal').pack(fill='x', pady=(7, 11))
    button(current, '▷  拨弦 · Space', lambda: app.send_command(CMD_PLUCK), 'Accent').pack(fill='x')
    modes = card(overview, '音色与模式', padding=16)
    modes.grid(row=0, column=1, sticky='nsew', padx=7)
    row = ttk.Frame(modes)
    row.pack(fill='x', pady=(0, 8))
    guitar_button = button(row, '木吉他', lambda: app.send_timbre(TIMBRE_GUITAR), 'Blue')
    guitar_button.pack(side='left', fill='x', expand=True)
    piano_button = button(row, '钢琴', app.restore_piano)
    piano_button.pack(side='left', fill='x', expand=True, padx=(5, 0))
    bass_button = button(modes, 'Bass · 低四弦 / 降八度音源', lambda: app.send_timbre(TIMBRE_BASS), 'Teal')
    bass_button.pack(fill='x', pady=(0, 8))
    ttk.Label(modes, textvariable=app.timbre_text, style='Muted.TLabel').pack(anchor='w', pady=(0, 12))
    row = ttk.Frame(modes)
    row.pack(fill='x', pady=(0, 8))
    mono_button = button(row, '单音直通', lambda: app.send_mode(MODE_MONO))
    mono_button.pack(side='left', fill='x', expand=True)
    poly_button = button(row, '32 复音', lambda: app.send_mode(MODE_POLY4), 'Blue')
    poly_button.pack(side='left', fill='x', expand=True, padx=(5, 0))
    def mark_mode(*_):
        poly = app.current_mode == MODE_POLY4
        mono_button.configure(style='TButton' if poly else 'Blue.TButton')
        poly_button.configure(style='Blue.TButton' if poly else 'TButton')
        poly_button.configure(text='8 复音' if app.current_timbre == TIMBRE_BASS else '32 复音')
    def mark_timbre(*_):
        text = app.timbre_text.get()
        guitar_button.configure(style='Blue.TButton' if '木吉他' in text else 'TButton')
        piano_button.configure(style='Blue.TButton' if '钢琴' in text else 'TButton')
        bass_button.configure(style='Teal.TButton' if 'Bass' in text else 'TButton')
        mark_mode()
    app._visual_traces = [app.mode_text.trace_add('write', mark_mode),
                          app.timbre_text.trace_add('write', mark_timbre)]
    ttk.Label(modes, textvariable=app.mode_text, style='Muted.TLabel', wraplength=235).pack(anchor='w')
    button(modes, '打开电吉他效果', app.open_effects, 'Violet').pack(fill='x', pady=(14, 0))
    riffs = card(overview, 'Riff 演奏', accent='teal', padding=16)
    riffs.grid(row=0, column=2, sticky='nsew', padx=(7, 0))
    riff_row = ttk.Frame(riffs)
    riff_row.pack(fill='x', pady=(7, 14))
    app.riff_button = button(riff_row, '▶ Riff 1 · 强节奏', lambda: app.toggle_riff(1), 'Teal')
    app.riff2_button = button(riff_row, '▶ Riff 2 · 慢速 4/4', lambda: app.toggle_riff(2), 'Teal')
    app.riff3_button = button(riff_row, '▶ Riff 3 · 铁轨', lambda: app.toggle_riff(3), 'Teal')
    # A stacked row remains legible at the minimum window size.
    for i, b in enumerate((app.riff_button, app.riff2_button, app.riff3_button)):
        riff_row.columnconfigure(i, weight=1, uniform='riffs')
        b.configure(text=('▶ Riff 1', '▶ Riff 2', '▶ Riff 3 · 铁轨')[i], width=1)
        b.grid(row=0, column=i, sticky='ew', padx=(0, 5) if i<2 else 0)
    ttk.Label(riffs, text='强节奏      /      慢速 4/4      /      铁轨闷音', style='Muted.TLabel').pack(anchor='w', pady=(0, 8))
    ttk.Label(riffs, textvariable=app.riff_status, style='Muted.TLabel', wraplength=440).pack(anchor='w')
    ttk.Label(riffs, text='效果可实时调节 · 铁轨闷音建议延音 0', style='Muted.TLabel').pack(anchor='w', pady=(7, 0))
    app._overview_compact = None
    def fit_overview(event):
        compact = event.width < 1000
        if compact == app._overview_compact:
            return
        app._overview_compact = compact
        for i, weight in enumerate((1, 1, 0) if compact else (24, 25, 51)):
            overview.columnconfigure(i, weight=weight, uniform='' if compact and i==2 else 'overview')
        riffs.grid(row=1 if compact else 0, column=0 if compact else 2,
                   columnspan=2 if compact else 1, padx=0 if compact else (7, 0),
                   pady=(12, 0) if compact else 0)
    overview.bind('<Configure>', fit_overview)
    fretbox = card(body, '吉他指板', padding=16)
    fretbox.pack(fill='x', pady=(0, 14))
    canvas = tk.Canvas(fretbox, height=260, background='white', highlightthickness=0)
    scroll = ttk.Scrollbar(fretbox, orient='horizontal', command=canvas.xview)
    canvas.configure(xscrollcommand=scroll.set)
    canvas.pack(fill='x')
    scroll.pack(fill='x', pady=(3, 5))
    board = ttk.Frame(canvas)
    board_item = canvas.create_window((0, 0), window=board, anchor='nw')
    board.columnconfigure(0, minsize=68)
    for i in range(1, 22):
        board.columnconfigure(i, weight=1, uniform='frets', minsize=40)
    ttk.Label(board, text='弦 / 品', style='Muted.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 6))
    for fret in range(21):
        ttk.Label(board, text=str(fret), style='Muted.TLabel', anchor='center').grid(row=0, column=fret+1, sticky='ew')
    app._string_labels = {}
    for string in range(1, 7):
        label = ttk.Label(board, text='%d  %s' % (string, OPEN_NAMES[string-1]), style='Muted.TLabel')
        label.grid(row=string, column=0, sticky='w', pady=3)
        app._string_labels[string] = label
        for fret in range(21):
            style = 'Marker.Fret' if fret in (0, 3, 5, 7, 9, 12, 15, 17, 19) else 'Fret'
            b = button(board, note_name(string, fret).replace('#', '♯'),
                       lambda s=string, f=fret: app.select_note(s, f, False), style, width=3)
            b.grid(row=string, column=fret+1, sticky='ew', padx=2, pady=3)
            b.bind('<Double-Button-1>', lambda _e, s=string, f=fret: app.pluck_note(s, f))
            app.fret_buttons[(string, fret)] = b
    def fit_board(event=None):
        width = max(canvas.winfo_width(), board.winfo_reqwidth())
        canvas.itemconfigure(board_item, width=width)
        canvas.configure(height=board.winfo_reqheight(), scrollregion=canvas.bbox('all'))
    canvas.bind('<Configure>', fit_board)
    board.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
    app.after_idle(fit_board)
    hint = ttk.Frame(fretbox)
    hint.pack(fill='x', pady=(5, 0))
    ttk.Label(hint, text='单击选择音符 · 双击拨弦', style='Muted.TLabel').pack(side='left')
    ttk.Label(hint, text='← / → 切换品位    Space 拨弦', style='Muted.TLabel').pack(side='right')
    logbox = card(body, padding=14)
    logbox.pack(fill='x')
    loghead = ttk.Frame(logbox)
    loghead.pack(fill='x', pady=(0, 8))
    ttk.Label(loghead, text='通信日志', style='Section.TLabel').pack(side='left')
    def toggle_log():
        expanded = int(app.log_view.cget('height')) == 3
        app.log_view.configure(height=8 if expanded else 3)
        logbutton.configure(text='收起日志' if expanded else '展开日志')
    logbutton = button(loghead, '展开日志', toggle_log)
    logbutton.pack(side='right')
    logrow = ttk.Frame(logbox)
    logrow.pack(fill='x')
    app.log_view = tk.Text(logrow, height=3, state='disabled', font=('Consolas', 9),
                           background='#F8FBFE', foreground=C['muted'], relief='flat',
                           borderwidth=0, padx=10, pady=6, wrap='word',
                           selectbackground='#D5E9FA', insertbackground=C['ink'])
    logs = ttk.Scrollbar(logrow, orient='vertical', command=app.log_view.yview)
    logs.pack(side='right', fill='y')
    app.log_view.configure(yscrollcommand=logs.set)
    app.log_view.pack(fill='x', expand=True)
    ttk.Label(body, text='115200 · 8N1 · 串口单向通信', style='Page.TLabel').pack(anchor='w', pady=(12, 0))


def update_note(app, old=None):
    from guitar_controller import note_name, note_frequency
    string, fret = app.selected_string.get(), app.selected_fret.get()
    if hasattr(app, '_large_note'):
        app._large_note.set(app.display_note_name(string, fret).replace('#', '♯'))
        app._note_detail.set('%d 弦 · %d 品 · %.6f Hz' % (string, fret, app.display_note_frequency(string, fret)))
    if old in app.fret_buttons:
        marked = old[1] in (0, 3, 5, 7, 9, 12, 15, 17, 19)
        app.fret_buttons[old].configure(style='Marker.Fret.TButton' if marked else 'Fret.TButton')
    chosen = app.fret_buttons.get((string, fret))
    if chosen is not None:
        chosen.configure(style='Selected.Fret.TButton')


def update_instrument(app):
    from guitar_controller import TIMBRE_BASS, OPEN_NAMES, bass_note_name, note_name
    bass = app.current_timbre == TIMBRE_BASS
    for (string, fret), widget in app.fret_buttons.items():
        allowed = not bass or string >= 3
        widget.configure(state='normal' if allowed else 'disabled',
                         text=((bass_note_name if bass else note_name)(string, fret)
                               if allowed else '—').replace('#', '♯'))
    for string, label in getattr(app, '_string_labels', {}).items():
        name = bass_note_name(string, 0) if bass and string >= 3 else OPEN_NAMES[string-1]
        label.configure(text='%d  %s' % (string, name if not bass or string >= 3 else '停用'))


def update_instrument(app):
    from guitar_controller import TIMBRE_BASS, OPEN_NAMES, bass_note_name, note_name
    bass = app.current_timbre == TIMBRE_BASS
    for (string, fret), widget in app.fret_buttons.items():
        allowed = not bass or string >= 3
        widget.configure(state='normal' if allowed else 'disabled',
                         text=((bass_note_name if bass else note_name)(string, fret)
                               if allowed else '—').replace('#', '♯'))
    for string, label in getattr(app, '_string_labels', {}).items():
        name = bass_note_name(string, 0) if bass and string >= 3 else OPEN_NAMES[string-1]
        label.configure(text='%d  %s' % (string, name if not bass or string >= 3 else '停用'))
