import tkinter as tk
from tkinter import ttk

from mario_score import MEASURES, numbered_measure
from melody_player import CommandPlayer, make_plan
from ui_pages import EmbeddedPage
from ui_theme import scroll_body


TIMBRE_NAMES = {0: '吉他弦品', 1: '钢琴键', 2: 'Bass弦品', 3: '小提琴音符'}


class SongPanel(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.bpm = tk.IntVar(value=100)
        self.velocity = tk.IntVar(value=100)
        self.transpose = tk.IntVar(value=0)
        self.gate = tk.IntVar(value=82)
        self.start_bar = tk.IntVar(value=1)
        self.score_repeat = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='先自行选择音色，再播放；播放器不会切换音色')
        self.progress = tk.DoubleVar(value=0)
        self.player = CommandPlayer(self._send, self.after, self.after_cancel, self._changed)
        content = scroll_body(self, padding=22)
        ttk.Label(content, text='超级马里奥 · 曲谱播放', style='Title.TLabel').pack(anchor='w')
        ttk.Label(content, text='按你提供的简谱录入：1=C，4/4，34个谱面小节；第23～34小节按反复记号再奏一次。',
                  wraplength=1000).pack(anchor='w', pady=(8, 4))
        ttk.Label(content, text='只发送音符命令，不发送音色、模式、效果或音量设置。请先在其他页面自行选择音色；使用主界面的FPGA串口，不占用S3霍尔串口。',
                  wraplength=1000).pack(anchor='w', pady=(0, 12))
        settings = ttk.LabelFrame(content, text='播放设置（开始播放时生效）', padding=12)
        settings.pack(fill='x')
        fields = [('速度 BPM', self.bpm, 40, 240), ('力度', self.velocity, 1, 127),
                  ('移调 半音', self.transpose, -36, 24), ('音长 %', self.gate, 10, 100),
                  ('起始小节', self.start_bar, 1, 34)]
        for column, (label, variable, minimum, maximum) in enumerate(fields):
            ttk.Label(settings, text=label).grid(row=0, column=column, sticky='w', padx=8)
            ttk.Spinbox(settings, from_=minimum, to=maximum, textvariable=variable, width=9).grid(row=1, column=column, sticky='w', padx=8, pady=6)
        ttk.Checkbutton(settings, text='执行谱中反复（23～34小节）', variable=self.score_repeat).grid(row=2, column=0, columnspan=3, sticky='w', padx=8)
        toolbar = ttk.Frame(content)
        toolbar.pack(fill='x', pady=12)
        ttk.Button(toolbar, text='▶ 从选定小节播放', command=self.play).pack(side='left')
        self.pause_button = ttk.Button(toolbar, text='暂停 / 继续', command=self.toggle_pause)
        self.pause_button.pack(side='left', padx=8)
        ttk.Button(toolbar, text='停止', command=self.stop).pack(side='left')
        ttk.Label(content, textvariable=self.status, wraplength=1000).pack(anchor='w')
        ttk.Progressbar(content, variable=self.progress, maximum=100).pack(fill='x', pady=8)
        ttk.Label(content, text='双击谱面行可选起始小节。分组以“/”分拍；上点用数字后的组合点表示。原图未标速度，默认100 BPM，可自行调节。',
                  wraplength=1000).pack(anchor='w', pady=(4, 8))
        table = ttk.Frame(content)
        table.pack(fill='both', expand=True)
        self.score = ttk.Treeview(table, columns=('bar', 'notes', 'rhythm'), show='headings', height=12)
        for name, title, width in [('bar', '小节', 60), ('notes', '简谱 · 每组一拍', 550), ('rhythm', '每音时值（以四分音符为1拍）', 430)]:
            self.score.heading(name, text=title)
            self.score.column(name, width=width, anchor='w', stretch=name != 'bar')
        self.score.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(table, orient='vertical', command=self.score.yview)
        scrollbar.pack(side='right', fill='y')
        self.score.configure(yscrollcommand=scrollbar.set)
        durations = {6: '¼', 8: '⅓', 12: '½', 24: '1'}
        for number, notes in enumerate(MEASURES, 1):
            self.score.insert('', 'end', iid=str(number), values=(number, numbered_measure(notes), ' '.join(durations[note.ticks] for note in notes)))
        self.score.bind('<Double-1>', self._select_bar)
        ttk.Label(content, text='吉他与Bass没有独立的松音命令：暂停/停止后自然尾音仍可能继续。Bass播放本曲建议移调−24半音；超出音域会拒绝播放，不会静默丢音。',
                  wraplength=1000).pack(anchor='w', pady=12)

    def _select_bar(self, event):
        selected = self.score.identify_row(event.y)
        if selected:
            self.start_bar.set(int(selected))

    def _send(self, data):
        controller = self.controller
        if controller.draw_upload_busy or controller.port is None or not controller.port.is_open:
            return False
        if self.player.plan is not None and controller.current_timbre != self.player.plan.timbre:
            return False
        try:
            if controller.port.write(data) != len(data):
                raise IOError('音符控制帧未完整发送')
            return True
        except Exception as error:
            controller.log(f'曲谱音符发送失败：{error}')
            return False

    def play(self):
        controller = self.controller
        if self.player.state != 'stopped' and not self.stop('重新开始播放'):
            return
        if controller.draw_upload_busy:
            self.status.set('上传正在进行，暂不发送曲谱音符')
            return
        if controller.port is None or not controller.port.is_open:
            self.status.set('请先连接主界面的FPGA串口；播放器不会自动连接设备')
            return
        if controller.riff_playing:
            self.status.set('请先停止现有Riff，避免两个播放器同时发送音符')
            return
        try:
            plan = make_plan(controller.current_timbre, self.bpm.get(), self.velocity.get(),
                             self.transpose.get(), self.gate.get() / 100,
                             self.start_bar.get(), self.score_repeat.get())
        except (ValueError, tk.TclError) as error:
            self.status.set(f'未播放：{error}')
            return
        if self.player.play(plan):
            controller.log(f'超级马里奥：{self.bpm.get()} BPM，{len(plan.bars)}小节，发送{TIMBRE_NAMES[plan.timbre]}命令；未切音色')

    def toggle_pause(self):
        if self.player.state == 'playing':
            self.player.pause()
        elif self.player.state == 'paused':
            self.player.resume()

    def _changed(self, player):
        self.progress.set(100 * player.position / player.plan.duration if player.plan else 0)
        note = player.event
        detail = f'第{note.bar}小节 · {note.token}' if note else '尚未发送音符'
        if note and note.pitch is not None:
            detail += f' · MIDI {note.pitch}'
        elapsed = int(player.position)
        total = int(player.plan.duration) if player.plan else 0
        target = f'{TIMBRE_NAMES[player.plan.timbre]}命令' if player.plan else '尚未选择发送格式'
        self.status.set(f'{player.message} | {target} | {detail} | {elapsed // 60}:{elapsed % 60:02d} / {total // 60}:{total % 60:02d}')
        if note:
            self.score.selection_set(str(note.bar))
            self.score.see(str(note.bar))

    def stop(self, message='已停止'):
        return self.player.stop(message)

    def on_hide(self):
        self.stop('已离开曲谱页，停止发送')
