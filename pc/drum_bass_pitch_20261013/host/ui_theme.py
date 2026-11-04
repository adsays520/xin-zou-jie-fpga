"""Presentation-only Tk theme. No third-party runtime dependency."""
import math
import tkinter as tk
from tkinter import ttk

COLORS = dict(page='#F2F7FC', card='#FFFFFF', ink='#263E53', muted='#657F94',
              line='#DCE8F2', blue='#348BD5', blue_soft='#E8F3FF',
              orange='#EC934C', orange_soft='#FFF2E5', teal='#168C85',
              teal_soft='#E7F6F2', violet='#7861B8', violet_soft='#F1EDFA',
              nav='#E8F2FC', red='#B85656')


def _tile(root, fill, edge, radius=9, background='#FFFFFF'):
    """Small transparent rounded tile, stretched by ttk's nine-slice border."""
    # A wide center avoids thousands of GDI tile copies when a card is large.
    size = 96
    photo = tk.PhotoImage(master=root, width=size, height=size)
    # Opaque corner pixels avoid costly alpha blending in Windows Tk 8.6.
    photo.put(background, to=(0, 0, size, size))
    for y in range(size):
        offset = 0
        if y < radius:
            offset = round(radius - math.sqrt(max(0, radius * radius - (radius-y-.5)**2)))
        elif y >= size-radius:
            offset = round(radius - math.sqrt(max(0, radius * radius - (y-(size-radius)+.5)**2)))
        photo.put(edge, to=(offset, y, size-offset, y+1))
        inset = 1 if y in (0, size-1) else 0
        if y not in (0, size-1):
            photo.put(fill, to=(offset+1, y, size-offset-1, y+1))
    return photo


def install(root):
    if getattr(root, '_audio_theme_installed', False):
        return
    root._audio_theme_installed = True
    root.configure(background=COLORS['page'])
    root.option_add('*Text.Font', ('Microsoft YaHei UI', 10))
    root.option_add('*TCombobox*Listbox.font', ('Microsoft YaHei UI', 10))
    root.option_add('*TCombobox*Listbox.background', '#FFFFFF')
    root.option_add('*TCombobox*Listbox.foreground', COLORS['ink'])
    root.option_add('*Background', COLORS['page'])
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Microsoft YaHei UI', 10), background=COLORS['card'],
                    foreground=COLORS['ink'], bordercolor=COLORS['line'],
                    lightcolor=COLORS['line'], darkcolor=COLORS['line'])
    style.configure('TFrame', background=COLORS['card'])
    style.configure('Page.TFrame', background=COLORS['page'])
    style.configure('Nav.TFrame', background=COLORS['nav'])
    style.configure('TLabel', background=COLORS['card'])
    for name, bg in [('Page', 'page'), ('Nav', 'nav'), ('Teal', 'teal_soft'),
                     ('Violet', 'violet_soft'), ('Warm', 'orange_soft'), ('Blue', 'blue_soft')]:
        style.configure(name+'.TFrame', background=COLORS[bg])
        style.configure(name+'.TLabel', background=COLORS[bg], foreground=COLORS['muted'])
    style.configure('Muted.TLabel', foreground=COLORS['muted'])
    style.configure('Title.TLabel', font=('Microsoft YaHei UI', 20, 'bold'), background=COLORS['page'])
    style.configure('Section.TLabel', font=('Microsoft YaHei UI', 12, 'bold'))
    style.configure('Note.TLabel', font=('Segoe UI', 32, 'bold'), foreground=COLORS['blue'])
    style.configure('Value.TLabel', foreground=COLORS['blue'], font=('Segoe UI', 11, 'bold'))
    style.configure('Brand.Nav.TLabel', font=('Segoe UI', 13, 'bold'), foreground=COLORS['ink'])
    style.configure('TCheckbutton', padding=(0, 3), indicatorbackground='white',
                    indicatorforeground=COLORS['blue'])
    style.map('TCheckbutton', background=[('active', COLORS['card'])])
    for kind in ('TCombobox', 'TSpinbox', 'TEntry'):
        style.configure(kind, padding=6, borderwidth=1, fieldbackground='#F8FBFE',
                        arrowcolor=COLORS['muted'], insertcolor=COLORS['ink'])
        style.map(kind, fieldbackground=[('readonly', '#F8FBFE'), ('disabled', '#F2F5F8')],
                  foreground=[('disabled', '#8E9FAC')], bordercolor=[('focus', COLORS['blue'])])
    style.configure('TLabelframe', background='white', borderwidth=1, relief='solid')
    style.configure('TLabelframe.Label', font=('Microsoft YaHei UI', 11, 'bold'))
    style.configure('Horizontal.TScale', background='white', troughcolor='#E5EDF4',
                    borderwidth=0, sliderlength=19, sliderrelief='flat')
    style.configure('Teal.Horizontal.TScale', troughcolor='#CFEAE4')
    style.configure('Violet.Horizontal.TScale', troughcolor='#E4DCF4')
    style.configure('Warm.Horizontal.TScale', troughcolor='#F6DEC8')
    style.configure('TScrollbar', background='#C9DBEB', troughcolor=COLORS['page'],
                    borderwidth=0, arrowsize=12, gripcount=0)
    style.configure('TProgressbar', background=COLORS['blue'], troughcolor=COLORS['blue_soft'], borderwidth=0)
    root._audio_ui_images = []
    # Rounded buttons preserve native ttk focus, keyboard and state semantics.
    palette = {
        'TButton': ('#FFFFFF', '#F0F6FC', '#E3EFFA', COLORS['ink'], COLORS['line']),
        'Primary.TButton': (COLORS['blue'], '#2479C1', '#2069A7', 'white', COLORS['blue']),
        'Accent.TButton': (COLORS['orange'], '#DF843D', '#CE7433', 'white', COLORS['orange']),
        'Blue.TButton': (COLORS['blue_soft'], '#D8EBFF', '#C6E1FC', '#276FAA', '#CEE4F8'),
        'Teal.TButton': (COLORS['teal_soft'], '#D6EDE7', '#C1E4DB', COLORS['teal'], '#CEE8E1'),
        'Violet.TButton': (COLORS['violet_soft'], '#E6DFF6', '#DAD0EF', COLORS['violet'], '#E2D9F1'),
        'Warm.TButton': (COLORS['orange_soft'], '#FBE4CB', '#F6D4B1', '#A4612F', '#F4DEC8'),
        'Nav.TButton': (COLORS['nav'], '#D9EAFB', '#CEE3F9', '#587B98', COLORS['nav']),
        'Active.Nav.TButton': ('#FFFFFF', '#FFFFFF', '#DDEDFB', COLORS['blue'], '#FFFFFF'),
        'Fret.TButton': ('#F8FBFE', '#E6F2FC', '#D9EBF8', '#53718A', '#E0EBF5'),
        'Marker.Fret.TButton': ('#ECF5FE', '#DDEFFD', '#C8E4F8', '#45779D', '#DCECF9'),
        'Selected.Fret.TButton': ('#FFF0E0', '#FFE8CF', '#FFDDBA', '#B26627', '#F5BE8A'),
    }
    for number, (name, (normal, hover, pressed, fg, border)) in enumerate(palette.items()):
        background = COLORS['nav'] if 'Nav' in name else '#FFFFFF'
        tiles = [_tile(root, color, border, 7 if 'Fret' in name else 9, background)
                 for color in (normal, hover, pressed)]
        disabled = _tile(root, '#F1F4F7', '#E1E8EF', background=background)
        focus = _tile(root, normal, '#6FA9D6', background=background)
        root._audio_ui_images.extend(tiles+[disabled, focus])
        element = 'AudioButton%d' % number
        style.element_create(element, 'image', tiles[0],
                             ('disabled', disabled), ('pressed', tiles[2]),
                             ('active', tiles[1]), ('focus', focus), border=7 if 'Fret' in name else 9,
                             width=20, height=20, padding=0, sticky='nsew')
        style.layout(name, [(element, {'sticky': 'nsew', 'children': [
            ('Button.padding', {'sticky': 'nsew', 'children': [
                ('Button.label', {'sticky': 'nsew'})]})]})])
        style.configure(name, padding=(13, 8), foreground=fg, anchor='center',
                        font=('Microsoft YaHei UI', 10), background='white')
        style.map(name, foreground=[('disabled', '#98A8B5')])
        if 'Fret' in name:
            style.configure(name, padding=(2, 5), font=('Segoe UI', 9))
        if 'Nav' in name:
            style.configure(name, padding=(14, 12), anchor='w', background=COLORS['nav'])
    # Native slider events remain intact; only its drawing changes.
    thumb = tk.PhotoImage(master=root, width=20, height=20)
    for y in range(20):
        for x in range(20):
            distance = (x-9.5)**2+(y-9.5)**2
            if distance <= 90:
                thumb.put('white' if distance < 46 else COLORS['blue'], (x, y))
    root._audio_ui_images.append(thumb)
    style.element_create('Audio.Scale.slider', 'image', thumb, sticky='')
    scale_styles = [('Horizontal.TScale', '#E5EDF4'), ('Teal.Horizontal.TScale', '#CFEAE4'),
                    ('Violet.Horizontal.TScale', '#E4DCF4'), ('Warm.Horizontal.TScale', '#F6DEC8')]
    for i, (name, color) in enumerate(scale_styles):
        track = tk.PhotoImage(master=root, width=96, height=20)
        track.put('#FFFFFF', to=(0, 0, 96, 20))
        track.put(color, to=(0, 8, 96, 12))
        root._audio_ui_images.append(track)
        element = 'AudioScale%d.trough' % i
        style.element_create(element, 'image', track, border=(3, 0, 3, 0),
                             width=20, height=20, padding=0, sticky='we')
        style.layout(name, [(element, {'sticky': 'we', 'children': [
            ('Audio.Scale.slider', {'side': 'left', 'sticky': ''})]})])
    tile = _tile(root, '#FFFFFF', COLORS['line'], 12, COLORS['page'])
    root._audio_ui_images.append(tile)
    style.element_create('AudioCard', 'image', tile, border=13, width=28, height=28, sticky='nsew')
    style.layout('Card.TFrame', [('AudioCard', {'sticky': 'nsew'})])
    style.configure('Card.TFrame', background='white')


def window(win, title, subtitle, width, height, minwidth=None, minheight=None, accent='blue'):
    if isinstance(win, ttk.Frame):
        win.configure(style='Page.TFrame')
    else:
        win.configure(background=COLORS['page'])
        win.geometry('%dx%d' % (width, height))
        win.minsize(minwidth or width, minheight or height)
    header = ttk.Frame(win, style='Page.TFrame', padding=(22, 18, 22, 12))
    header.pack(fill='x')
    tk.Frame(header, background=COLORS[accent], width=5, height=42).pack(side='left', padx=(0, 12))
    texts = ttk.Frame(header, style='Page.TFrame')
    texts.pack(side='left')
    ttk.Label(texts, text=title, style='Title.TLabel').pack(anchor='w')
    ttk.Label(texts, text=subtitle, style='Page.TLabel').pack(anchor='w', pady=(3, 0))
    return header


def card(parent, title=None, accent='blue', padding=18):
    frame = ttk.Frame(parent, style='Card.TFrame', padding=padding)
    if title:
        heading = ttk.Frame(frame)
        heading.pack(fill='x', pady=(0, 12))
        tk.Frame(heading, background=COLORS[accent], width=4, height=20).pack(side='left', padx=(0, 9))
        ttk.Label(heading, text=title, style='Section.TLabel').pack(side='left')
    return frame


def button(parent, text, command, kind='', **kwargs):
    return ttk.Button(parent, text=text, command=command,
                      style=(kind+'.TButton') if kind else 'TButton', **kwargs)


def parameter(parent, text, variable, maximum=127, style='Horizontal.TScale', command=None):
    frame = ttk.Frame(parent)
    row = ttk.Frame(frame)
    row.pack(fill='x', pady=(0, 8))
    ttk.Label(row, text=text).pack(side='left')
    ttk.Label(row, textvariable=variable, style='Value.TLabel', width=4, anchor='e').pack(side='right')
    options = dict(from_=0, to=maximum, variable=variable, orient='horizontal', style=style)
    if command is not None:
        options['command'] = command
    ttk.Scale(frame, **options).pack(fill='x')
    return frame


def compact_keyboard(win):
    """Keep both drawing canvases and the 88-key keyboard visible at 1000×730."""
    style = ttk.Style(win)
    style.configure('Compact.TButton', padding=(8, 4), font=('Microsoft YaHei UI', 9))
    style.configure('Compact.Primary.TButton', padding=(8, 4), font=('Microsoft YaHei UI', 9))
    style.configure('Compact.TSpinbox', padding=3, font=('Microsoft YaHei UI', 9))
    style.configure('Compact.TCombobox', padding=3, font=('Microsoft YaHei UI', 9))
    style.configure('Keyboard.TLabelframe.Label', font=('Microsoft YaHei UI', 10, 'bold'))
    def visit(widget):
        if isinstance(widget, ttk.Button):
            widget.configure(style='Compact.'+(widget.cget('style') or 'TButton'))
        elif isinstance(widget, ttk.Spinbox):
            widget.configure(style='Compact.TSpinbox')
        elif isinstance(widget, ttk.Combobox):
            widget.configure(style='Compact.TCombobox')
        elif isinstance(widget, ttk.Label) and widget.cget('style') not in ('Title.TLabel', 'Section.TLabel'):
            widget.configure(font=('Microsoft YaHei UI', 9))
        for child in widget.winfo_children():
            visit(child)
    visit(win)
    win.drawn_panel.configure(style='Keyboard.TLabelframe', padding=6)


def scroll_body(win, padding=(20, 0, 20, 18)):
    row = ttk.Frame(win, style='Page.TFrame')
    row.pack(fill='both', expand=True)
    scroll = ttk.Scrollbar(row, orient='vertical')
    scroll.pack(side='right', fill='y')
    canvas = tk.Canvas(row, bg=COLORS['page'], highlightthickness=0, yscrollcommand=scroll.set)
    canvas.pack(fill='both', expand=True)
    scroll.configure(command=canvas.yview)
    body = ttk.Frame(canvas, style='Page.TFrame', padding=padding)
    item = canvas.create_window((0, 0), window=body, anchor='nw')
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(item, width=e.width))
    body.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
    win._scroll_canvas = canvas
    return body
