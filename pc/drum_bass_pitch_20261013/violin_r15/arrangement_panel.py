"""A small hardware-aware arranger embedded in the existing controller."""
from copy import deepcopy
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from arrangement_model import (Automation, BAR, Clip, COLORS, DISCRETE, DRUM_NAMES,
                               History, INSTRUMENTS, Note, PARAMETERS, PPQ, Point,
                               Project, Track, demo_project, ensemble_demo_project, duplicate_clip, pitch_name, snap)
from arrangement_playback import TIMBRES, compile_plan, score_notes
from arrangement_worker import ThreadedArrangementPlayer
from ensemble_protocol import CapabilityProbe
from serial_transport import PlaybackSender, SerializedPort
from ui_pages import EmbeddedPage


class ArrangementPanel(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.history = History(demo_project())
        self.saved = self.project.to_dict()
        self.path = None
        self.track_id = self.project.tracks[0].id
        self.clip_id = self.project.tracks[0].clips[0].id
        self.note_id = None
        self.point_tick = None
        self.playhead = 0
        self.pixels_per_beat = 72
        self.row_height = 52
        self.header_height = 30
        self.note_height = 18
        self.drag = None
        self.status = tk.StringVar(value='离线编辑就绪。双击时间轴创建片段，双击卷帘添加音符。')
        self.position_text = tk.StringVar(value='1 : 1.00')
        self.hardware = tk.BooleanVar(value=False)
        self.ensemble = tk.BooleanVar(value=False)
        self.probe = CapabilityProbe()
        self._probe_job = None
        self.capability_text = tk.StringVar(value='未探测；v8合奏需配套新位流，不能只更新上位机')
        self.loop = tk.BooleanVar(value=False)
        self.name = tk.StringVar(value=self.project.name)
        self.bpm = tk.IntVar(value=self.project.bpm)
        self.bars = tk.IntVar(value=self.project.bars)
        self.guitar_sustain = tk.IntVar(value=self.project.guitar_sustain)
        self.violin_legato = tk.BooleanVar(value=self.project.violin_legato)
        self.grid_value = tk.StringVar(value='1/16')
        self.zoom = tk.StringVar(value='100%')
        self.instrument = tk.StringVar(value=INSTRUMENTS['piano'])
        self.track_name = tk.StringVar()
        self.track_level = tk.IntVar(value=100)
        self.clip_name = tk.StringVar()
        self.clip_start = tk.DoubleVar(value=0)
        self.clip_length = tk.DoubleVar(value=4)
        self.pitch = tk.IntVar(value=60)
        self.velocity = tk.IntVar(value=100)
        self.note_start = tk.DoubleVar(value=0)
        self.note_length = tk.DoubleVar(value=1)
        self.target = tk.StringVar(value=PARAMETERS['space.delay_mix'][0])
        self.interpolation = tk.StringVar(value='linear')
        self.base_value = tk.IntVar(value=0)
        self.point_beat = tk.DoubleVar(value=0)
        self.point_value = tk.IntVar(value=0)
        self.loop_first = tk.IntVar(value=1)
        self.loop_last = tk.IntVar(value=5)
        self.player = ThreadedArrangementPlayer()
        self._display_snapshot = self.player.snapshot()
        self._display_player_state = 'stopped'
        self._controls_version = 0
        self._build()
        self.render()
        self.after(25, self._poll_player)

    @property
    def project(self):
        return self.history.project

    @property
    def grid_ticks(self):
        return {'1/4': PPQ, '1/8': PPQ // 2, '1/16': PPQ // 4, '1/32': PPQ // 8}[self.grid_value.get()]

    def _button(self, parent, title, action):
        result = ttk.Button(parent, text=title, command=action)
        result.pack(side='left', padx=2)
        return result

    def _entry(self, parent, label, variable, width=6, limits=None):
        ttk.Label(parent, text=label).pack(side='left', padx=(8, 3))
        if limits:
            widget = ttk.Spinbox(parent, from_=limits[0], to=limits[1], textvariable=variable, width=width)
        else:
            widget = ttk.Entry(parent, textvariable=variable, width=width)
        widget.pack(side='left', padx=2)
        return widget

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)
        heading = ttk.Frame(self, padding=(16, 10, 16, 4))
        heading.grid(row=0, column=0, sticky='ew')
        ttk.Label(heading, text='编曲工作台 · 后台调度', style='Title.TLabel').pack(side='left')
        for title, action in [('新建', self.new), ('演示工程', self.demo), ('打开', self.open),
                              ('保存', self.save), ('另存', lambda: self.save(True)),
                              ('撤销', self.undo), ('重做', self.redo), ('导出事件CSV', self.export)]:
            self._button(heading, title, action)
        settings = ttk.Frame(self, padding=(8, 2))
        settings.grid(row=1, column=0, sticky='ew')
        self._entry(settings, '工程', self.name, 20)
        self._entry(settings, 'BPM', self.bpm, limits=(30, 300))
        self._entry(settings, '小节', self.bars, limits=(1, 256))
        self._entry(settings, '吉他延音', self.guitar_sustain, 4, (0, 127))
        self._button(settings, '应用', self.apply_project)
        ttk.Label(settings, text='网格').pack(side='left', padx=(8, 3))
        ttk.Combobox(settings, values=('1/4', '1/8', '1/16', '1/32'), state='readonly',
                     textvariable=self.grid_value, width=6).pack(side='left')
        zoom = ttk.Combobox(settings, values=('50%', '75%', '100%', '150%', '200%'),
                            state='readonly', textvariable=self.zoom, width=6)
        zoom.pack(side='left', padx=8)
        zoom.bind('<<ComboboxSelected>>', self._zoom)
        transport = ttk.Frame(self, padding=(12, 4))
        transport.grid(row=2, column=0, sticky='ew')
        self._button(transport, '▶ 播放 / 走带', self.play)
        self._button(transport, '■ 停止', self.stop)
        self._button(transport, '回到开头', self.rewind)
        ttk.Checkbutton(transport, text='实机发送', variable=self.hardware,
                        command=lambda: self.stop('发送模式已改变，需重新播放')).pack(side='left', padx=8)
        ttk.Checkbutton(transport, text='循环', variable=self.loop).pack(side='left')
        self._entry(transport, '起始小节', self.loop_first, 4, (1, 256))
        self._entry(transport, '结束边界', self.loop_last, 4, (2, 257))
        self._button(transport, '设循环', self.apply_loop)
        self._button(transport, '检查实机兼容性', self.check)
        ttk.Label(transport, textvariable=self.position_text).pack(side='right', padx=10)
        ttk.Label(self, text='v7：一种主乐器 + 鼓组；v8候选：吉他/钢琴/Bass/小提琴/鼓合奏。离线走带静音；不伪造板端能力。',
                  style='Muted.TLabel', padding=(16, 3)).grid(row=3, column=0, sticky='w')
        capabilities = ttk.Frame(self, padding=(12, 3))
        capabilities.grid(row=4, column=0, sticky='ew')
        self._button(capabilities, '探测v8能力', self.probe_capabilities)
        ttk.Checkbutton(capabilities, text='v8独立合奏（需探测成功）', variable=self.ensemble,
                        command=lambda: self.stop('合奏模式已改变，需重新播放')).pack(side='left', padx=8)
        self._button(capabilities, '合奏示例', self.demo_ensemble)
        ttk.Checkbutton(capabilities, text='提琴连弓（应用后生效）', variable=self.violin_legato).pack(side='left', padx=6)
        ttk.Label(capabilities, textvariable=self.capability_text, style='Muted.TLabel').pack(side='left', padx=6)
        panes = ttk.Panedwindow(self, orient='vertical')
        panes.grid(row=5, column=0, sticky='nsew', padx=12)
        arrangement = ttk.Frame(panes)
        panes.add(arrangement, weight=1)
        track_tools = ttk.Frame(arrangement)
        track_tools.pack(fill='x', pady=3)
        ttk.Combobox(track_tools, values=tuple(INSTRUMENTS.values()), textvariable=self.instrument,
                     state='readonly', width=12).pack(side='left')
        for title, action in [('＋轨道', self.add_track), ('删轨', self.delete_track),
                              ('Mute', lambda: self.toggle_track('muted')),
                              ('Solo', lambda: self.toggle_track('solo')),
                              ('＋片段', self.add_clip), ('复制片段', self.copy_clip), ('删片段', self.delete_clip)]:
            self._button(track_tools, title, action)
        self._entry(track_tools, '轨道名', self.track_name, 12)
        self._entry(track_tools, '力度%', self.track_level, 4, (0, 127))
        self._button(track_tools, '应用轨道', self.apply_track)
        area = ttk.Frame(arrangement)
        area.pack(fill='both', expand=True)
        area.columnconfigure(1, weight=1)
        area.rowconfigure(0, weight=1)
        self.headers = tk.Canvas(area, width=176, height=225, background='#FFFFFF', highlightthickness=0)
        self.headers.grid(row=0, column=0, sticky='ns')
        self.timeline = tk.Canvas(area, height=225, background='#F5F8FC', highlightthickness=0)
        self.timeline.grid(row=0, column=1, sticky='nsew')
        vertical = ttk.Scrollbar(area, orient='vertical', command=self._scroll_tracks)
        vertical.grid(row=0, column=2, sticky='ns')
        self.timeline.configure(yscrollcommand=vertical.set)
        horizontal = ttk.Scrollbar(area, orient='horizontal', command=self.timeline.xview)
        horizontal.grid(row=1, column=1, sticky='ew')
        self.timeline.configure(xscrollcommand=horizontal.set)
        self.headers.bind('<Button-1>', self._header_click)
        self.timeline.bind('<Button-1>', self._timeline_press)
        self.timeline.bind('<B1-Motion>', self._timeline_motion)
        self.timeline.bind('<ButtonRelease-1>', self._timeline_release)
        self.timeline.bind('<Double-Button-1>', self._timeline_double)
        self.timeline.bind('<Button-3>', lambda event: self.delete_clip())
        self.timeline.bind('<MouseWheel>', self._wheel_tracks)
        self.headers.bind('<MouseWheel>', self._wheel_tracks)
        editor = ttk.Notebook(panes)
        panes.add(editor, weight=2)
        roll_page = ttk.Frame(editor)
        fx_page = ttk.Frame(editor)
        editor.add(roll_page, text='钢琴卷帘 / 鼓编辑')
        editor.add(fx_page, text='效果器 / 自动化')
        self.editors = editor
        clip_tools = ttk.Frame(roll_page)
        clip_tools.pack(fill='x', pady=3)
        self._entry(clip_tools, '片段名', self.clip_name, 12)
        self._entry(clip_tools, '起点(拍)', self.clip_start)
        self._entry(clip_tools, '长度(拍)', self.clip_length)
        self._button(clip_tools, '应用片段', self.apply_clip)
        self._button(clip_tools, '＋音符', self.add_note)
        self._button(clip_tools, '删音符', self.delete_note)
        note_tools = ttk.Frame(roll_page)
        note_tools.pack(fill='x', pady=3)
        self._entry(note_tools, 'MIDI/鼓编号', self.pitch, 5, (0, 127))
        self._entry(note_tools, '力度', self.velocity, 4, (1, 127))
        self._entry(note_tools, '片内起点(拍)', self.note_start)
        self._entry(note_tools, '时值(拍)', self.note_length)
        self._button(note_tools, '应用音符', self.apply_note)
        roll_area = ttk.Frame(roll_page)
        roll_area.pack(fill='both', expand=True)
        roll_area.columnconfigure(0, weight=1)
        roll_area.rowconfigure(0, weight=1)
        self.roll = tk.Canvas(roll_area, height=210, background='white', highlightthickness=0)
        self.roll.grid(row=0, column=0, sticky='nsew')
        roll_y = ttk.Scrollbar(roll_area, orient='vertical', command=self.roll.yview)
        roll_y.grid(row=0, column=1, sticky='ns')
        roll_x = ttk.Scrollbar(roll_area, orient='horizontal', command=self.roll.xview)
        roll_x.grid(row=1, column=0, sticky='ew')
        self.roll.configure(yscrollcommand=roll_y.set, xscrollcommand=roll_x.set)
        self.roll.bind('<Double-Button-1>', self._roll_double)
        self.roll.bind('<Button-1>', self._roll_press)
        self.roll.bind('<B1-Motion>', self._roll_motion)
        self.roll.bind('<ButtonRelease-1>', self._roll_release)
        self.roll.bind('<Button-3>', self._roll_delete)
        self.roll.bind('<MouseWheel>', self._wheel_roll)
        fx_tools = ttk.Frame(fx_page)
        fx_tools.pack(fill='x', pady=4)
        target = ttk.Combobox(fx_tools, values=tuple(spec[0] for spec in PARAMETERS.values()),
                              textvariable=self.target, width=24, state='readonly')
        target.pack(side='left')
        target.bind('<<ComboboxSelected>>', self._target_changed)
        self._entry(fx_tools, '基础值', self.base_value, 5, (0, 127))
        self._button(fx_tools, '应用基础值', self.apply_base)
        ttk.Combobox(fx_tools, values=('step', 'linear'), textvariable=self.interpolation,
                     width=7, state='readonly').pack(side='left', padx=4)
        self._button(fx_tools, '应用插值', self.apply_interpolation)
        self._button(fx_tools, '清空此自动化', self.clear_automation)
        points = ttk.Frame(fx_page)
        points.pack(fill='x', pady=3)
        self._entry(points, '时间(拍)', self.point_beat)
        self._entry(points, '参数值', self.point_value, 5, (0, 127))
        self._button(points, '添加/更新点', self.apply_point)
        self._button(points, '删除选中点', self.delete_point)
        ttk.Label(points, text='双击加点 · 拖动移动 · 右键删除；linear按20Hz量化发送。',
                  style='Muted.TLabel').pack(side='left', padx=10)
        self.fx = tk.Canvas(fx_page, height=195, background='#F6F8FC', highlightthickness=0)
        self.fx.pack(fill='both', expand=True)
        fx_scroll = ttk.Scrollbar(fx_page, orient='horizontal', command=self.fx.xview)
        fx_scroll.pack(fill='x')
        self.fx.configure(xscrollcommand=fx_scroll.set)
        self.fx.bind('<Double-Button-1>', self._fx_double)
        self.fx.bind('<Button-1>', self._fx_press)
        self.fx.bind('<B1-Motion>', self._fx_motion)
        self.fx.bind('<ButtonRelease-1>', self._fx_release)
        self.fx.bind('<Button-3>', self._fx_delete)
        self.fx.bind('<Configure>', lambda event: self.render_fx())
        ttk.Label(self, textvariable=self.status, wraplength=1120, padding=(14, 7)).grid(row=6, column=0, sticky='ew')
        self.bind('<Control-s>', lambda event: self.save())

    def track(self):
        return next((track for track in self.project.tracks if track.id == self.track_id), None)

    def clip(self):
        track = self.track()
        return next((clip for clip in track.clips if clip.id == self.clip_id), None) if track else None

    def note(self):
        clip = self.clip()
        return next((note for note in clip.notes if note.id == self.note_id), None) if clip else None

    def target_key(self):
        return next(key for key, spec in PARAMETERS.items() if spec[0] == self.target.get())

    def lane(self):
        return next((lane for lane in self.project.automation if lane.target == self.target_key()), None)

    def _edit(self, operation, message='已修改；播放中编辑会先停止走带'):
        self.stop()
        try:
            self.history.edit(operation)
            self.status.set(message)
        except (ValueError, tk.TclError, OverflowError) as error:
            self.status.set(f'未修改：{error}')
        self.render()

    def render(self):
        if self.track() is None:
            self.track_id = self.project.tracks[0].id if self.project.tracks else None
        if self.clip() is None:
            track = self.track()
            self.clip_id = track.clips[0].id if track and track.clips else None
        self.name.set(self.project.name)
        self.bpm.set(self.project.bpm)
        self.bars.set(self.project.bars)
        self.guitar_sustain.set(self.project.guitar_sustain)
        self.violin_legato.set(self.project.violin_legato)
        self.loop_first.set(self.project.loop_start // BAR + 1)
        self.loop_last.set(self.project.loop_end // BAR + 1)
        track, clip, note = self.track(), self.clip(), self.note()
        if track:
            self.track_name.set(track.name)
            self.track_level.set(track.level)
        if clip:
            self.clip_name.set(clip.name)
            self.clip_start.set(clip.start / PPQ)
            self.clip_length.set(clip.length / PPQ)
        if note:
            self.pitch.set(note.pitch)
            self.velocity.set(note.velocity)
            self.note_start.set(note.start / PPQ)
            self.note_length.set(note.duration / PPQ)
        self.render_timeline()
        self.render_roll()
        self.render_fx()

    def _zoom(self, event=None):
        self.pixels_per_beat = round(72 * int(self.zoom.get().rstrip('%')) / 100)
        self.render()

    def _x(self, tick, origin=0):
        return origin + tick / PPQ * self.pixels_per_beat

    def _tick_at(self, canvas, screen_x, origin=0):
        return snap((canvas.canvasx(screen_x) - origin) * PPQ / self.pixels_per_beat, self.grid_ticks)

    def _grid_lines(self, canvas, length, height, origin=0):
        for tick in range(0, length + 1, PPQ):
            position = self._x(tick, origin)
            canvas.create_line(position, 0, position, height, fill='#CFDBE8' if tick % BAR == 0 else '#E6EDF5')
            if tick % BAR == 0:
                canvas.create_text(position + 5, 12, text=str(tick // BAR + 1), anchor='w', fill='#657F94')

    def render_timeline(self):
        canvas = self.timeline
        canvas.delete('all')
        self.headers.delete('all')
        height = max(230, self.header_height + len(self.project.tracks) * self.row_height)
        width = max(800, self._x(self.project.length) + 20)
        canvas.configure(scrollregion=(0, 0, width, height))
        self.headers.configure(scrollregion=(0, 0, 176, height))
        self._grid_lines(canvas, self.project.length, height)
        canvas.create_rectangle(self._x(self.project.loop_start), 20, self._x(self.project.loop_end), 29,
                                fill='#BCE5DA', outline='')
        self.headers.create_text(10, 14, text='轨道              M  S', anchor='w', fill='#657F94')
        active = {track.id for track in self.project.active_tracks()}
        for row, track in enumerate(self.project.tracks):
            top = self.header_height + row * self.row_height
            selected = track.id == self.track_id
            self.headers.create_rectangle(0, top, 176, top + self.row_height,
                                          fill='#E8F3FF' if selected else '#FFFFFF', outline='#DFE7F0')
            self.headers.create_rectangle(0, top + 4, 4, top + self.row_height - 4, fill=COLORS[track.instrument], outline='')
            self.headers.create_text(12, top + 14, text=track.name[:13], anchor='w', fill='#263E53')
            self.headers.create_text(12, top + 35, text=INSTRUMENTS[track.instrument], anchor='w', fill='#657F94')
            for horizontal, enabled, label in ((143, track.muted, 'M'), (164, track.solo, 'S')):
                self.headers.create_text(horizontal, top + 26, text=label,
                                         fill='#D05665' if enabled else '#A8B5C2', font=('Segoe UI', 10, 'bold'))
            canvas.create_line(0, top + self.row_height, width, top + self.row_height, fill='#DFE7F0')
            for clip in track.clips:
                left, right = self._x(clip.start), self._x(clip.start + clip.length)
                tag = 'clip:' + clip.id
                canvas.create_rectangle(left + 1, top + 4, right - 1, top + self.row_height - 4,
                                        fill=COLORS[track.instrument] if track.id in active else '#ACB7C1',
                                        outline='#243E55' if clip.id == self.clip_id else '',
                                        width=2, tags=(tag,))
                canvas.create_text(left + 7, top + 14, text=clip.name[:max(1, int((right-left)/13))],
                                   anchor='w', fill='white', tags=(tag,))
                for note in clip.notes:
                    note_y = top + 23 + (11 - note.pitch if track.instrument == 'drums' else (84 - note.pitch) % 24) * 0.8
                    canvas.create_line(self._x(clip.start + note.start) + 2, note_y,
                                       self._x(clip.start + note.start + note.duration) - 2, note_y,
                                       fill='#E5F1FF', width=2, tags=(tag,))
        canvas.create_line(self._x(self.playhead), 0, self._x(self.playhead), height,
                           fill='#E05061', width=2, tags=('playhead',))

    def _scroll_tracks(self, *arguments):
        self.timeline.yview(*arguments)
        self.headers.yview(*arguments)

    def _wheel_tracks(self, event):
        self._scroll_tracks('scroll', -int(event.delta / 120), 'units')
        return 'break'

    def _header_click(self, event):
        row = int((self.headers.canvasy(event.y) - self.header_height) // self.row_height)
        if 0 <= row < len(self.project.tracks):
            self.track_id = self.project.tracks[row].id
            self.clip_id, self.note_id = None, None
            if event.x >= 130:
                self.toggle_track('solo' if event.x >= 154 else 'muted')
            else:
                self.render()

    def _hit(self, canvas, event, prefix):
        items = canvas.find_overlapping(canvas.canvasx(event.x) - 3, canvas.canvasy(event.y) - 3,
                                        canvas.canvasx(event.x) + 3, canvas.canvasy(event.y) + 3)
        for item in reversed(items):
            for tag in canvas.gettags(item):
                if tag.startswith(prefix):
                    return tag[len(prefix):]
        return None

    def _timeline_press(self, event):
        self.timeline.focus_set()
        self.drag = None
        if self.timeline.canvasy(event.y) < self.header_height:
            self.stop()
            self.playhead = min(self.project.length - 1, self._tick_at(self.timeline, event.x))
            self.render_timeline()
            return
        identifier = self._hit(self.timeline, event, 'clip:')
        if identifier:
            for track in self.project.tracks:
                for clip in track.clips:
                    if clip.id == identifier:
                        self.track_id, self.clip_id, self.note_id = track.id, clip.id, None
                        resizing = self.timeline.canvasx(event.x) >= self._x(clip.start + clip.length) - 8
                        self.drag = ('clip', self.timeline.canvasx(event.x), clip.start, clip.length, resizing)
                        self.render()
                        return

    def _timeline_motion(self, event):
        if self.drag and self.drag[0] == 'clip':
            _, origin, start, length, resizing = self.drag
            delta = snap(abs(self.timeline.canvasx(event.x) - origin) * PPQ / self.pixels_per_beat,
                         self.grid_ticks) * (1 if self.timeline.canvasx(event.x) >= origin else -1)
            position = self._x(start + length + delta if resizing else max(0, start + delta))
            self.timeline.delete('drag')
            self.timeline.create_line(position, 0, position, 2000, fill='#263E53', dash=(3, 3), tags='drag')

    def _timeline_release(self, event):
        drag, self.drag = self.drag, None
        self.timeline.delete('drag')
        if not drag or drag[0] != 'clip':
            return
        _, origin, start, length, resizing = drag
        raw = (self.timeline.canvasx(event.x) - origin) * PPQ / self.pixels_per_beat
        delta = snap(abs(raw), self.grid_ticks) * (1 if raw >= 0 else -1)
        if not delta:
            return
        if resizing:
            self._edit(lambda project: setattr(self.clip(), 'length', length + delta))
        else:
            self._edit(lambda project: setattr(self.clip(), 'start', max(0, start + delta)))

    def _timeline_double(self, event):
        self.drag = None
        if self._hit(self.timeline, event, 'clip:'):
            self.editors.select(0)
            return
        row = int((self.timeline.canvasy(event.y) - self.header_height) // self.row_height)
        if 0 <= row < len(self.project.tracks):
            self.track_id = self.project.tracks[row].id
            self.add_clip(self._tick_at(self.timeline, event.x))

    def _pitch_range(self):
        instrument = self.track().instrument if self.track() else 'piano'
        return {'piano': (21, 108), 'guitar': (40, 84), 'bass': (28, 63),
                'violin': (55, 100), 'drums': (0, 11)}[instrument]

    def render_roll(self):
        self.roll.delete('all')
        clip, track = self.clip(), self.track()
        if not clip:
            self.roll.create_text(20, 30, anchor='w', text='请选择或新建片段，再双击网格放置音符。', fill='#657F94')
            return
        lowest, highest = self._pitch_range()
        height = (highest - lowest + 1) * self.note_height + 25
        width = max(800, self._x(clip.length, 70) + 20)
        self.roll.configure(scrollregion=(0, 0, width, height))
        for pitch in range(highest, lowest - 1, -1):
            top = (highest - pitch) * self.note_height + 25
            black = track.instrument != 'drums' and pitch % 12 in (1, 3, 6, 8, 10)
            self.roll.create_rectangle(0, top, width, top + self.note_height,
                                       fill='#F0F3F7' if black else '#FFFFFF', outline='#E8EDF3')
            self.roll.create_text(5, top + 9, text=DRUM_NAMES[pitch] if track.instrument == 'drums' else pitch_name(pitch),
                                  anchor='w', fill='#657F94', font=('Segoe UI', 8))
        self._grid_lines(self.roll, clip.length, height, 70)
        for note in clip.notes:
            top = (highest - note.pitch) * self.note_height + 25
            self.roll.create_rectangle(self._x(note.start, 70) + 1, top + 1,
                                       self._x(note.start + note.duration, 70) - 1, top + self.note_height - 1,
                                       fill=COLORS[track.instrument],
                                       outline='#233F56' if note.id == self.note_id else '', width=2,
                                       tags=('note:' + note.id,))
        if getattr(self, '_roll_clip', None) != clip.id:
            self._roll_clip = clip.id
            center = (highest - (clip.notes[0].pitch if clip.notes else min(60, highest))) * self.note_height
            self.roll.yview_moveto(max(0, (center - 50) / height))

    def _roll_pitch(self, event):
        lowest, highest = self._pitch_range()
        return max(lowest, min(highest, highest - int((self.roll.canvasy(event.y) - 25) // self.note_height)))

    def _roll_double(self, event):
        self.drag = None
        if self.clip() and not self._hit(self.roll, event, 'note:') and self.roll.canvasx(event.x) >= 70:
            self.note_start.set(self._tick_at(self.roll, event.x, 70) / PPQ)
            self.note_length.set(self.grid_ticks / PPQ)
            self.pitch.set(self._roll_pitch(event))
            self.add_note()

    def _roll_press(self, event):
        self.drag = None
        identifier = self._hit(self.roll, event, 'note:')
        if not identifier:
            return
        self.note_id = identifier
        note = self.note()
        self.drag = ('note', self.roll.canvasx(event.x), self.roll.canvasy(event.y), deepcopy(note),
                     self.roll.canvasx(event.x) >= self._x(note.start + note.duration, 70) - 7)
        self.render()

    def _roll_motion(self, event):
        if self.drag and self.drag[0] == 'note':
            self.roll.delete('drag')
            self.roll.create_line(self.roll.canvasx(event.x), 0, self.roll.canvasx(event.x), 2500,
                                  fill='#263E53', dash=(3, 3), tags='drag')

    def _roll_release(self, event):
        drag, self.drag = self.drag, None
        self.roll.delete('drag')
        if not drag or drag[0] != 'note':
            return
        _, horizontal, vertical, old, resizing = drag
        raw = (self.roll.canvasx(event.x) - horizontal) * PPQ / self.pixels_per_beat
        delta = snap(abs(raw), self.grid_ticks) * (1 if raw >= 0 else -1)
        pitch_delta = round((vertical - self.roll.canvasy(event.y)) / self.note_height)
        if delta == 0 and (resizing or pitch_delta == 0):
            return

        def move(project):
            note = self.note()
            if resizing:
                note.duration = max(self.grid_ticks, old.duration + delta)
            else:
                note.start = max(0, old.start + delta)
                note.pitch = old.pitch + pitch_delta
        self._edit(move)

    def _roll_delete(self, event):
        self.note_id = self._hit(self.roll, event, 'note:')
        self.delete_note()

    def _wheel_roll(self, event):
        self.roll.yview_scroll(-int(event.delta / 120), 'units')
        return 'break'

    def render_fx(self):
        if not hasattr(self, 'fx'):
            return
        self.fx.delete('all')
        target = self.target_key()
        self.base_value.set(self.project.parameters[target])
        lane = self.lane()
        if lane:
            self.interpolation.set(lane.interpolation)
        height = max(140, self.fx.winfo_height())
        self.fx.configure(scrollregion=(0, 0, max(800, self._x(self.project.length, 50) + 20), height))
        self._grid_lines(self.fx, self.project.length, height, 50)
        maximum = PARAMETERS[target][2]
        for value in (0, maximum // 2, maximum):
            top = self._fy(value)
            self.fx.create_line(45, top, self._x(self.project.length, 50), top, fill='#DCE5EF')
            self.fx.create_text(5, top, text=str(value), anchor='w', fill='#657F94')
        if lane and lane.points:
            points = sorted(lane.points, key=lambda point: point.tick)
            vertices = [(0, self.project.parameters[target])] if points[0].tick else []
            vertices += [(point.tick, point.value) for point in points]
            vertices.append((self.project.length, points[-1].value))
            for previous, current in zip(vertices, vertices[1:]):
                left, top = self._x(previous[0], 50), self._fy(previous[1])
                right, bottom = self._x(current[0], 50), self._fy(current[1])
                if lane.interpolation == 'step':
                    self.fx.create_line(left, top, right, top, right, bottom, fill='#8266BB', width=2)
                else:
                    self.fx.create_line(left, top, right, bottom, fill='#8266BB', width=2)
            for point in points:
                horizontal, vertical = self._x(point.tick, 50), self._fy(point.value)
                self.fx.create_oval(horizontal - 5, vertical - 5, horizontal + 5, vertical + 5,
                                    fill='#E39B49' if point.tick == self.point_tick else '#8266BB',
                                    outline='white', tags=('point:' + str(point.tick),))
        else:
            self.fx.create_line(50, self._fy(self.project.parameters[target]), self._x(self.project.length, 50),
                                self._fy(self.project.parameters[target]), fill='#8266BB', dash=(4, 3))

    def _fy(self, value):
        height = max(140, self.fx.winfo_height())
        return height - 20 - value / PARAMETERS[self.target_key()][2] * (height - 50)

    def _fx_value(self, event):
        height = max(140, self.fx.winfo_height())
        maximum = PARAMETERS[self.target_key()][2]
        return max(0, min(maximum, round((height - 20 - event.y) / (height - 50) * maximum)))

    def _target_changed(self, event=None):
        self.point_tick = None
        self.interpolation.set('step' if self.target_key() in DISCRETE else 'linear')
        self.render_fx()

    def _fx_double(self, event):
        self.drag = None
        self.point_beat.set(min(self.project.length, self._tick_at(self.fx, event.x, 50)) / PPQ)
        self.point_value.set(self._fx_value(event))
        self.apply_point()

    def _fx_press(self, event):
        self.drag = None
        tick = self._hit(self.fx, event, 'point:')
        if tick is not None:
            self.point_tick = int(tick)
            point = next(point for point in self.lane().points if point.tick == self.point_tick)
            self.point_beat.set(point.tick / PPQ)
            self.point_value.set(point.value)
            self.drag = ('point', point.tick)
            self.render_fx()

    def _fx_motion(self, event):
        if self.drag and self.drag[0] == 'point':
            self.point_beat.set(min(self.project.length, self._tick_at(self.fx, event.x, 50)) / PPQ)
            self.point_value.set(self._fx_value(event))

    def _fx_release(self, event):
        drag, self.drag = self.drag, None
        if drag and drag[0] == 'point':
            self.apply_point(replace=drag[1])

    def _fx_delete(self, event):
        tick = self._hit(self.fx, event, 'point:')
        self.point_tick = int(tick) if tick is not None else None
        self.delete_point()

    def add_track(self):
        instrument = next(key for key, name in INSTRUMENTS.items() if name == self.instrument.get())
        track = Track(instrument, f'{len(self.project.tracks) + 1:02d} {INSTRUMENTS[instrument]}')
        self.track_id, self.clip_id, self.note_id = track.id, None, None
        self._edit(lambda project: project.tracks.append(track))

    def delete_track(self):
        if self.track():
            self._edit(lambda project: project.tracks.remove(self.track()))

    def toggle_track(self, field):
        if self.track():
            self._edit(lambda project: setattr(self.track(), field, not getattr(self.track(), field)))

    def apply_track(self):
        if self.track():
            def apply(project):
                self.track().name = self.track_name.get()
                self.track().level = self.track_level.get()
            self._edit(apply)

    def add_clip(self, start=None):
        track = self.track()
        if not track:
            self.status.set('先添加或选择一条轨道')
            return
        start = min(self.project.length - self.grid_ticks, self.playhead if start is None else start)
        clip = Clip('新片段', start, min(BAR, self.project.length - start))
        self.clip_id, self.note_id = clip.id, None
        self._edit(lambda project: self.track().clips.append(clip))

    def copy_clip(self):
        clip = self.clip()
        if clip:
            duplicate = duplicate_clip(clip, clip.start + clip.length)
            self._edit(lambda project: self.track().clips.append(duplicate))
            if duplicate.start + duplicate.length <= self.project.length:
                self.clip_id = duplicate.id
                self.render()

    def delete_clip(self):
        if self.clip():
            self._edit(lambda project: self.track().clips.remove(self.clip()))

    def apply_clip(self):
        if self.clip():
            def apply(project):
                self.clip().name = self.clip_name.get()
                self.clip().start = round(self.clip_start.get() * PPQ)
                self.clip().length = round(self.clip_length.get() * PPQ)
            self._edit(apply)

    def add_note(self):
        if not self.clip():
            self.status.set('先创建片段')
            return
        def add(project):
            note = Note(round(self.note_start.get() * PPQ), round(self.note_length.get() * PPQ),
                        self.pitch.get(), self.velocity.get())
            self.clip().notes.append(note)
            self.note_id = note.id
        self._edit(add)

    def apply_note(self):
        if self.note():
            def apply(project):
                note = self.note()
                note.start, note.duration = round(self.note_start.get() * PPQ), round(self.note_length.get() * PPQ)
                note.pitch, note.velocity = self.pitch.get(), self.velocity.get()
            self._edit(apply)

    def delete_note(self):
        if self.note():
            self._edit(lambda project: self.clip().notes.remove(self.note()))

    def apply_base(self):
        self._edit(lambda project: project.parameters.__setitem__(self.target_key(), self.base_value.get()))

    def apply_interpolation(self):
        def apply(project):
            lane = self.lane()
            if lane:
                lane.interpolation = self.interpolation.get()
        self._edit(apply)

    def apply_point(self, replace=None):
        def apply(project):
            tick = round(self.point_beat.get() * PPQ)
            point = Point(tick, self.point_value.get())
            lane = self.lane()
            if lane is None:
                lane = Automation(self.target_key(), self.interpolation.get())
                project.automation.append(lane)
            lane.points = [previous for previous in lane.points if previous.tick not in (tick, replace)] + [point]
            lane.points.sort(key=lambda value: value.tick)
            self.point_tick = tick
        self._edit(apply)

    def delete_point(self):
        if self.lane() and self.point_tick is not None:
            self._edit(lambda project: setattr(self.lane(), 'points',
                                               [point for point in self.lane().points if point.tick != self.point_tick]))

    def clear_automation(self):
        if self.lane():
            self._edit(lambda project: project.automation.remove(self.lane()))

    def apply_project(self):
        def apply(project):
            project.name, project.bpm, project.bars = self.name.get(), self.bpm.get(), self.bars.get()
            project.guitar_sustain = self.guitar_sustain.get()
            project.violin_legato = self.violin_legato.get()
            project.loop_end = min(project.loop_end, project.length)
        self._edit(apply)

    def apply_loop(self):
        def apply(project):
            project.loop_start = (self.loop_first.get() - 1) * BAR
            project.loop_end = (self.loop_last.get() - 1) * BAR
        self._edit(apply)

    def undo(self):
        self.stop()
        self.history.undo()
        self.render()
        self.status.set('已撤销')

    def redo(self):
        self.stop()
        self.history.redo()
        self.render()
        self.status.set('已重做')

    def confirm_discard(self):
        return self.project.to_dict() == self.saved or messagebox.askyesno('未保存编曲', '放弃未保存的编曲修改？', parent=self)

    def _replace(self, project, path=None):
        self.stop()
        self.history = History(project)
        self.path, self.saved = path, project.to_dict()
        self.track_id = project.tracks[0].id if project.tracks else None
        self.clip_id, self.note_id = None, None
        self.playhead = 0
        self.render()

    def new(self):
        if self.confirm_discard():
            self._replace(Project())

    def demo(self):
        if self.confirm_discard():
            self._replace(demo_project())

    def demo_ensemble(self):
        if self.confirm_discard():
            self._replace(ensemble_demo_project())
            self.ensemble.set(True)
            self.hardware.set(False)
            self.status.set('已载入五路合奏示例，保持静音走带；实机需配套v8并探测成功')

    def open(self):
        if not self.confirm_discard():
            return
        path = filedialog.askopenfilename(parent=self, filetypes=[('Tang编曲', '*.tang.json'), ('JSON', '*.json')])
        if path:
            try:
                self._replace(Project.load(path), path)
                self.status.set('工程已载入；没有发送任何板端命令')
            except (ValueError, OSError) as error:
                self.status.set(f'打开失败：{error}')

    def save(self, save_as=False):
        path = self.path
        if save_as or not path:
            path = filedialog.asksaveasfilename(parent=self, defaultextension='.tang.json',
                                               filetypes=[('Tang编曲', '*.tang.json')])
        if path:
            try:
                self.project.save(path)
                self.path, self.saved = path, self.project.to_dict()
                self.status.set('已保存：' + path)
            except (ValueError, OSError) as error:
                self.status.set(f'保存失败：{error}')

    def export(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.csv', filetypes=[('事件列表', '*.csv')])
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as stream:
                    writer = csv.writer(stream)
                    writer.writerow(('start_beats', 'duration_beats', 'instrument', 'pitch_or_drum', 'velocity', 'start_seconds'))
                    for note in score_notes(self.project):
                        writer.writerow((note.start / PPQ, (note.end - note.start) / PPQ, note.instrument,
                                         note.pitch, note.velocity, note.start / PPQ * 60 / self.project.bpm))
                self.status.set('已导出启用轨道的音符事件CSV（不含效果自动化，不是音频）')
            except OSError as error:
                self.status.set(f'导出失败：{error}')

    def check(self):
        try:
            plan = compile_plan(self.project, True, ensemble=self.ensemble.get())
            self.status.set(f'实机编译检查通过：{len(plan.events)}事件，{plan.duration:.1f}秒；尚未发送/听音。' + plan.warnings[0])
        except ValueError as error:
            self.status.set('实机检查不通过：' + str(error))

    def _blocked(self):
        app = self.controller
        if app.draw_upload_busy:
            return '请先完成音色上传'
        if app.riff_playing:
            return '请先停止Riff'
        if app.song_panel.player.state != 'stopped':
            return '请先停止乐曲播放器'
        drum = app.drum_window
        if drum is not None and (drum.playing or drum.uploading):
            return '请先停止原鼓步进器'
        if app.port is None or not app.port.is_open:
            return '请连接顶部FPGA UART串口（不是Hall原生USB端口）'
        return None

    def play(self):
        if self.player.state != 'stopped' and not self.stop():
            return
        if self.hardware.get():
            self._serialize_port()
            reason = self._blocked()
            if reason:
                self.status.set(reason)
                return
            if self.ensemble.get():
                if not self.probe.usable(self.controller.port):
                    self.status.set('未与当前串口的v8位流确认能力，拒绝合奏发送；请先探测')
                    return
                if any(track.instrument == 'piano' and any(clip.notes for clip in track.clips)
                       for track in self.project.active_tracks()) and not self.probe.flags & 4:
                    self.status.set('v8尚未报告钢琴参数就绪，等待SD加载后重新探测')
                    return
        try:
            start = self.project.loop_start if self.loop.get() else (0 if self.playhead >= self.project.length else self.playhead)
            end = self.project.loop_end if self.loop.get() else self.project.length
            plan = compile_plan(self.project, self.hardware.get(), start, end, ensemble=self.ensemble.get())
            sender = PlaybackSender(self.controller.port) if plan.hardware else None
            self.player.play(plan, loop=self.loop.get(), send=sender)
            self._refresh_player()
        except ValueError as error:
            self.status.set('未播放：' + str(error))

    def _serialize_port(self):
        original = self.controller.port
        if original is not None:
            port = SerializedPort.wrap(original)
            if self.probe.port is original:
                self.probe.port = port
            self.controller.port = port

    def _apply_controls(self, frames):
        app = self.controller
        for frame in frames:
            if frame[1] == 4:
                app.current_timbre = frame[2]
                app.timbre_text.set('音色：' + INSTRUMENTS[next(key for key, value in TIMBRES.items() if value == frame[2])])
                app.violin_keys.held.clear()
            elif frame[1] == 3:
                app.current_mode = frame[2]
            elif frame[1] == 0x13:
                app.envelope_text.set('包络：' + ('编曲短延音RAM' if frame[2] else '吉他板载算法'))
            elif frame[1] == 0x70 and frame[2] < len(app.bus_levels):
                app.bus_levels[frame[2]] = frame[3]

    def _send(self, data):
        # GUI-only capability queries. Musical events use a captured PlaybackSender.
        app = self.controller
        if app.draw_upload_busy or app.port is None or not app.port.is_open:
            return False
        try:
            if app.port.write(data) != len(data):
                raise IOError('编曲UART帧未完整发送')
            self._apply_controls(data[offset:offset + 6] for offset in range(0, len(data), 6))
            return True
        except Exception as error:
            app.log(f'编曲发送失败：{error}')
            return False

    def _changed(self, player):
        if player.plan is not None and (player.state == 'playing' or self._display_player_state == 'playing'):
            self.playhead = min(self.project.length, player.tick)
            self.position_text.set(f'{self.playhead // BAR + 1} : {(self.playhead % BAR) / PPQ + 1:.2f}')
            self.timeline.coords('playhead', self._x(self.playhead), 0, self._x(self.playhead), 10000)
        event = player.last_event
        detail = ''
        if event and event.note:
            note = event.note
            name = DRUM_NAMES[note.pitch] if note.instrument == 'drums' else pitch_name(note.pitch)
            detail = f' | {INSTRUMENTS[note.instrument]} {name} 力度{note.velocity}'
        self.status.set(player.message + f' | 门控中{len(player.active)}音符（不含尾音）' + detail +
                        f' | 最长迟到{player.max_lateness * 1000:.1f}ms / 写入{player.max_write_seconds * 1000:.1f}ms')
        self._display_player_state = player.state

    def _refresh_player(self):
        snapshot = self.player.snapshot()
        if snapshot is self._display_snapshot:
            return
        self._display_snapshot = snapshot
        if snapshot.controls_version != self._controls_version:
            self._apply_controls(snapshot.controls)
            self._controls_version = snapshot.controls_version
        self._changed(snapshot)
        if snapshot.state == 'stopped' and any(word in snapshot.message for word in ('失败', '异常', '迟到超过', '状态未知')):
            self.controller.log('编曲：' + snapshot.message)

    def _poll_player(self):
        if self._destroying:
            return
        self._refresh_player()
        self.after(25, self._poll_player)

    def stop(self, message='已停止；鼓与空间效果可能保留自然尾音'):
        if self.player.state == 'stopped':
            return True
        accepted = self.player.stop(message)
        self._refresh_player()
        return accepted

    def rewind(self):
        self.stop()
        self.playhead = 0
        self.render_timeline()
        self.position_text.set('1 : 1.00')

    def on_hide(self):
        self.stop('离开编曲页，已停止发送')
        self.player.wait_ready()
        self._refresh_player()
        self.invalidate_capabilities()

    def probe_capabilities(self):
        self.stop('探测前停止编曲')
        if not self.player.wait_ready():
            self.capability_text.set('正在清理播放，请稍后再探测')
            return
        self._refresh_player()
        self._serialize_port()
        reason = self._blocked()
        if reason:
            self.capability_text.set(reason)
            return
        self.invalidate_capabilities()
        data = self.probe.begin(self.controller.port)
        if not self._send(data):
            self.invalidate_capabilities()
            self.capability_text.set('能力查询发送失败')
            return
        self.capability_text.set('等待带序号与校验的v8回复；旧位流无回复属正常')
        self._probe_job = self.after(25, self._poll_capabilities)

    def _poll_capabilities(self):
        self._probe_job = None
        port = self.controller.port
        if port is not self.probe.port or port is None or not port.is_open:
            self.invalidate_capabilities()
            return
        try:
            data = port.read(256)
            if self.probe.feed(data, port):
                self.capability_text.set('已确认v8独立合奏；钢琴参数' + ('就绪' if self.probe.flags & 4 else '尚未就绪'))
                return
        except Exception as error:
            self.invalidate_capabilities()
            self.capability_text.set('读取能力失败：' + str(error))
            return
        if self.probe.clock() >= self.probe.deadline:
            self.invalidate_capabilities()
            self.capability_text.set('未收到有效v8回复：保持v7限制，不允许合奏发送')
        else:
            self._probe_job = self.after(25, self._poll_capabilities)

    def invalidate_capabilities(self):
        if self._probe_job is not None:
            self.after_cancel(self._probe_job)
            self._probe_job = None
        self.probe.invalidate()
        self.capability_text.set('未探测；v8合奏需配套新位流，不能只更新上位机')

    def on_disconnect(self):
        self.stop('串口断开，停止编曲')
        self.player.wait_ready()
        self._refresh_player()
        self.invalidate_capabilities()

    def close(self):
        self.stop('关闭编曲工作台')
        self.invalidate_capabilities()
        self.destroy()

    def destroy(self):
        self.player.shutdown()
        super().destroy()
