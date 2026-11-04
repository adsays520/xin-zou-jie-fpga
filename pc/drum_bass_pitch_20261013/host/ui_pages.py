"""Single-window navigation. Instrument panels persist when another page is shown."""
import re
import tkinter as tk
from tkinter import ttk
from ui_theme import COLORS as C, install, card, button, scroll_body

PAGE_TITLES = {'guitar': '吉他演奏', 'piano': '88 键钢琴', 'drums': '原声鼓机',
               'pitch': '吉他滑音 / 颤音', 'effects': '电吉他效果', 'mix': '混音与空间效果', 'verify': '现场验证与视听'}


class EmbeddedPage(ttk.Frame):
    """A real Frame; legacy sizing methods refer to the single application window."""
    def __init__(self, controller, parent=None, section=False):
        parent = controller.page_area if parent is None else parent
        super().__init__(parent, style='Page.TFrame')
        self.controller = controller
        self._section = section
        self._page_jobs = set()
        self._destroying = False
        if parent is controller.page_area:
            self.grid(row=0, column=0, sticky='nsew')
            self.tkraise()

    def attributes(self, *args):
        return self.controller.attributes(*args)

    def geometry(self, value=None):
        if value is None:
            return '%dx%d' % (self.winfo_width(), self.winfo_height())
        match = re.match(r'(\d+)x(\d+)', value)
        if match:
            width, height = map(int, match.groups())
            self.controller.geometry('%dx%d' % (width+188, height+65))

    def after(self, ms, func=None, *args):
        if func is None:
            return super().after(ms)
        holder = []
        def run():
            if holder:
                self._page_jobs.discard(holder[0])
            if not self._destroying:
                func(*args)
        token = super().after(ms, run)
        holder.append(token)
        self._page_jobs.add(token)
        return token

    def after_cancel(self, token):
        self._page_jobs.discard(token)
        return super().after_cancel(token)

    def destroy(self):
        if self._destroying:
            return
        self._destroying = True
        for token in tuple(self._page_jobs):
            try:
                super().after_cancel(token)
            except tk.TclError:
                pass
        self._page_jobs.clear()
        super().destroy()


def build_shell(app):
    install(app)
    width, height = app.winfo_screenwidth(), app.winfo_screenheight()
    app.geometry('%dx%d' % (min(1440, width-80), min(930, height-100)))
    app.minsize(980, 660)
    app._pages = {}
    app.active_page = 'guitar'
    app._nav_buttons = {}
    shell = ttk.Frame(app, style='Page.TFrame')
    shell.pack(fill='both', expand=True)
    nav = ttk.Frame(shell, style='Nav.TFrame', width=188, padding=(14, 24, 14, 18))
    nav.pack(side='left', fill='y')
    nav.pack_propagate(False)
    ttk.Label(nav, text='TANG MEGA', style='Brand.Nav.TLabel').pack(anchor='w', padx=8)
    ttk.Label(nav, text='演奏控制台', style='Nav.TLabel').pack(anchor='w', padx=8, pady=(4, 28))
    ttk.Label(nav, text='演奏与音色', style='Nav.TLabel').pack(anchor='w', padx=8, pady=(0, 12))
    for key, title in PAGE_TITLES.items():
        item = button(nav, title, lambda k=key: app.show_page(k),
                      'Active.Nav' if key=='guitar' else 'Nav')
        item.pack(fill='x', pady=4)
        app._nav_buttons[key] = item
    button(nav, 'Bass · 低四弦', lambda: (app.show_page('guitar'), app.send_timbre(2)), 'Nav').pack(fill='x', pady=4)
    foot = ttk.Frame(nav, style='Nav.TFrame')
    foot.pack(side='bottom', fill='x')
    ttk.Label(foot, text='FPGA AUDIO', style='Nav.TLabel').pack(anchor='w', padx=8)
    ttk.Label(foot, text='Tang Mega 138K Pro', style='Nav.TLabel').pack(anchor='w', padx=8, pady=6)
    right = ttk.Frame(shell, style='Page.TFrame')
    right.pack(side='left', fill='both', expand=True)
    top = ttk.Frame(right, padding=(22, 14))
    top.pack(fill='x')
    app.page_title = tk.StringVar(value='演奏工作台  /  吉他演奏')
    ttk.Label(top, textvariable=app.page_title, style='Muted.TLabel').pack(side='left')
    app.connect_button = button(top, '连接设备', app.toggle_connection, 'Primary')
    app.connect_button.pack(side='right')
    button(top, '刷新', app.refresh_ports).pack(side='right', padx=8)
    app.port_combo = ttk.Combobox(top, state='readonly', width=24)
    app.port_combo.pack(side='right', padx=8)
    ttk.Label(top, textvariable=app.connection_text, style='Muted.TLabel').pack(side='right', padx=8)
    app._notice_text = tk.StringVar()
    app._notice_bar = ttk.Frame(right, style='Warm.TFrame', padding=(16, 8))
    ttk.Label(app._notice_bar, textvariable=app._notice_text, style='Warm.TLabel',
              wraplength=1000).pack(side='left', fill='x', expand=True)
    button(app._notice_bar, '关闭提示', lambda: app._notice_bar.pack_forget()).pack(side='right', padx=8)
    app.page_area = ttk.Frame(right, style='Page.TFrame')
    app.page_area.pack(fill='both', expand=True)
    app.page_area.rowconfigure(0, weight=1)
    app.page_area.columnconfigure(0, weight=1)
    guitar = EmbeddedPage(app)
    app._pages['guitar'] = guitar
    def wheel(event):
        page = app._pages.get(app.active_page)
        canvas = getattr(page, '_scroll_canvas', None)
        if canvas is not None and event.widget.winfo_class() not in ('TCombobox', 'TSpinbox', 'TScale', 'Text'):
            canvas.yview_scroll(-int(event.delta/120), 'units')
    app.bind('<MouseWheel>', wheel, add='+')
    return scroll_body(guitar, padding=(22, 18, 22, 16))


def show_page(app, key):
    key = 'mix' if key in ('mixer', 'space', 'reverb') else key
    if key not in PAGE_TITLES:
        raise ValueError('Unknown page: '+str(key))
    old = app._pages.get(app.active_page)
    if key != app.active_page and old is not None and hasattr(old, 'on_hide'):
        old.on_hide()
    if key != app.active_page and old is not None:
        old.grid_remove()
    page = app._pages.get(key)
    if page is None or not page.winfo_exists():
        if key == 'piano':
            from guitar_controller import PianoKeyboard
            page = PianoKeyboard(app)
            app.piano_keyboard = page
        elif key == 'drums':
            from drum_editor import DrumEditor
            page = DrumEditor(app)
            app.drum_window = page
        elif key == 'pitch':
            from ui_pitch import PitchPage
            page = PitchPage(app)
            app.pitch_page = page
        elif key == 'effects':
            from guitar_effects import GuitarEffects
            page = GuitarEffects(app)
            app.effects_window = page
        elif key == 'mix':
            page = AudioPage(app)
        elif key == 'verify':
            from verification_page import VerificationPage
            page = VerificationPage(app)
            app.verification_page = page
        else:
            raise RuntimeError('Guitar page missing')
        app._pages[key] = page
    if key == 'mix':
        page.ensure_sections()
    page.grid(row=0, column=0, sticky='nsew')
    page.tkraise()
    app.active_page = key
    if key == 'verify':
        page.render()
    app.page_title.set('演奏工作台  /  '+PAGE_TITLES[key])
    for name, item in app._nav_buttons.items():
        item.configure(style='Active.Nav.TButton' if name==key else 'Nav.TButton')
    return page


class AudioPage(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        body = scroll_body(self, padding=(22, 18, 22, 18))
        ttk.Label(body, text='混音与空间效果', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='三路乐器音量 · 合唱 · 延迟', style='Page.TLabel').pack(anchor='w', pady=(5, 18))
        self.columns = ttk.Frame(body, style='Page.TFrame')
        self.columns.pack(fill='x')
        self.left = ttk.Frame(self.columns, style='Page.TFrame')
        self.right = ttk.Frame(self.columns, style='Page.TFrame')
        self.left.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        self.right.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        self.columns.columnconfigure(0, weight=44, uniform='audio')
        self.columns.columnconfigure(1, weight=56, uniform='audio')
        self._compact = None
        def fit(event):
            compact = event.width < 1080
            if compact == self._compact:
                return
            self._compact = compact
            self.columns.columnconfigure(0, weight=1 if compact else 44, uniform='audio')
            self.columns.columnconfigure(1, weight=0 if compact else 56, uniform='' if compact else 'audio')
            self.left.grid(padx=0 if compact else (0, 10))
            self.right.grid(row=1 if compact else 0, column=0 if compact else 1,
                            padx=0 if compact else (10, 0), pady=(18, 0) if compact else 0)
        self.columns.bind('<Configure>', fit)
        self.ensure_sections()
        reserved = card(body, '混响', accent='violet', padding=14)
        reserved.pack(fill='x', pady=(18, 0))
        ttk.Label(reserved, text='待接入 · 后续混响调节将在此与合唱、延迟一起显示。',
                  style='Muted.TLabel').pack(anchor='w')

    def ensure_sections(self):
        app = self.controller
        if app.mixer_window is None or not app.mixer_window.winfo_exists():
            from performance_mixer import PerformanceMixer
            app.mixer_window = PerformanceMixer(app, parent=self.left, section=True)
            app.mixer_window.pack(fill='both', expand=True)
        if app.space_effects_window is None or not app.space_effects_window.winfo_exists():
            from master_space_effects import MasterSpaceEffects
            app.space_effects_window = MasterSpaceEffects(app, parent=self.right, section=True)
            app.space_effects_window.pack(fill='both', expand=True)
