"""Embedded osu-style rhythm page using existing scores, transport and synths."""
from copy import deepcopy
import json
from pathlib import Path
import time
import tkinter as tk
from tkinter import filedialog, ttk

from ui_pages import EmbeddedPage
from arrangement_model import INSTRUMENTS, Project
from arrangement_worker import ThreadedArrangementPlayer
from ensemble_protocol import CapabilityProbe
from serial_transport import SerializedPort, PlaybackSender
from rhythm_audio import LEAD_IN, LiveStriker, game_plan, strike_frames
from rhythm_input import HallInput
from rhythm_model import DIFFICULTIES, Session, make_chart, training_project
from rhythm_view import RhythmView


ROOT = Path(__file__).resolve().parents[2]


class ResultStore:
    def __init__(self, path):
        self.path = Path(path)

    def record(self, summary, profile):
        if summary['autoplay'] or summary['judged'] != summary['objects']:
            return False
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                data = {}
        except (OSError, ValueError):
            data = {}
        key = summary['chart_sha256']+':'+profile
        previous = data.get(key, {})
        if summary['score'] <= previous.get('score', -1):
            return False
        data[key] = {**summary, 'profile': profile, 'recorded_at': time.strftime('%Y-%m-%d %H:%M:%S')}
        data = dict(list(data.items())[-128:])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)
        return True


class RhythmPanel(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.project = training_project()
        self.chart = None
        self.session = None
        self.player = ThreadedArrangementPlayer()
        self.striker = None
        self.probe = CapabilityProbe()
        self._probe_job = None
        self._frame_job = None
        self.running = self.live_hw = self.live_performance = False
        self.origin = 0.
        self.last_song_time = -LEAD_IN
        self.held = set()
        self.pointer = None
        self.summary = None
        self.track_ids = {}
        self.sources = {'内置 · 星轨练习': None, '当前编曲 · 副本': 'current'}
        self.hall_input = HallInput()
        self.store = ResultStore(ROOT/'rhythm_data'/'best_scores.json')
        self.source = tk.StringVar(value='内置 · 星轨练习')
        self.track = tk.StringVar()
        self.variant = tk.StringVar(value='短试听')
        self.difficulty = tk.StringVar(value='标准')
        self.input_mode = tk.StringVar(value='鼠标 / Z·X')
        self.game_mode = tk.StringVar(value='跟拍练习')
        self.hardware = tk.BooleanVar(value=False)
        self.autoplay = tk.BooleanVar(value=False)
        self.offset = tk.IntVar(value=0)
        self.status = tk.StringVar(value='先选择曲目，再按开始。离线练习无声；连接FPGA后可播放板端音乐。')
        self.chart_text = tk.StringVar()
        self.capability_text = tk.StringVar(value='FPGA尚未探测')
        self._read_library()
        self._build()
        self._set_tracks()
        self.rebuild()
        self._bindings = [(name, controller.bind(name, callback, add='+')) for name, callback in
            (('<KeyPress>', self._key_down), ('<KeyRelease>', self._key_up),
             ('<ButtonRelease-1>', self._mouse_up), ('<FocusOut>', self._focus_out))]
        controller.hall_panel.line_listeners.append(self._hall_line)

    def _read_library(self):
        directory = ROOT/'Music_Demos'
        try:
            data = json.loads((directory/'catalog.json').read_text(encoding='utf-8'))
            for song in data['songs']:
                paths = {}
                for variant in ('full', 'short'):
                    path = (directory/song[variant]).resolve()
                    if path.parent != (directory/'projects').resolve() or not path.name.endswith('.tang.json'):
                        raise ValueError('曲库路径越界')
                    paths[variant] = path
                self.sources['曲库 · '+song['title']] = paths
        except (OSError, ValueError, KeyError, TypeError):
            pass  # standalone host retains its original training chart

    def _combo(self, parent, variable, values, width, callback):
        widget = ttk.Combobox(parent, textvariable=variable, values=tuple(values), state='readonly', width=width)
        widget.pack(side='left', padx=(0, 6))
        widget.bind('<<ComboboxSelected>>', callback)
        return widget

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        heading = ttk.Frame(self, padding=(18, 10, 18, 6))
        heading.grid(row=0, column=0, sticky='ew')
        ttk.Label(heading, text='芯奏界 · 节奏舞台', style='Title.TLabel').pack(side='left')
        ttk.Label(heading, text='APPROACH / HIT / CREATE', style='Muted.TLabel').pack(side='right')
        source_row = ttk.Frame(self, padding=(16, 4))
        source_row.grid(row=1, column=0, sticky='ew')
        self.source_box = self._combo(source_row, self.source, self.sources, 39, self.load_source)
        self._combo(source_row, self.variant, ('短试听', '完整版'), 8, self.load_source)
        ttk.Button(source_row, text='从编曲取谱', command=self.use_arrangement).pack(side='left', padx=3)
        ttk.Button(source_row, text='打开工程', command=self.open_project).pack(side='left', padx=3)
        self.track_box = self._combo(source_row, self.track, (), 24, self.rebuild)
        settings = ttk.Frame(self, padding=(16, 4))
        settings.grid(row=2, column=0, sticky='ew')
        self._combo(settings, self.difficulty, DIFFICULTIES, 6, self.rebuild)
        self._combo(settings, self.input_mode, ('鼠标 / Z·X', '霍尔拨杆'), 12, self.rebuild)
        self._combo(settings, self.game_mode, ('跟拍练习', '命中发声'), 9, self.rebuild)
        ttk.Label(settings, text='输入校准ms').pack(side='left')
        ttk.Spinbox(settings, from_=-250, to=250, increment=5, textvariable=self.offset, width=5).pack(side='left', padx=5)
        ttk.Checkbutton(settings, text='FPGA发声', variable=self.hardware, command=self._settings_changed).pack(side='left', padx=5)
        ttk.Checkbutton(settings, text='演示（不记成绩）', variable=self.autoplay, command=self._settings_changed).pack(side='left', padx=5)
        controls = ttk.Frame(self, padding=(16, 4))
        controls.grid(row=3, column=0, sticky='ew')
        ttk.Button(controls, text='▶ 开始 / 重新挑战', style='Primary.TButton', command=self.start).pack(side='left')
        ttk.Button(controls, text='■ 停止 / Esc', command=self.stop).pack(side='left', padx=6)
        ttk.Button(controls, text='探测FPGA', command=self.probe_fpga).pack(side='left', padx=3)
        ttk.Button(controls, text='配置霍尔', command=lambda: self.controller.show_page('hall')).pack(side='left', padx=3)
        ttk.Label(controls, textvariable=self.capability_text, style='Muted.TLabel').pack(side='left', padx=7)
        self.view = RhythmView(self)
        self.view.grid(row=4, column=0, sticky='nsew', padx=14, pady=(6, 0))
        self.view.bind('<Motion>', self._motion)
        self.view.bind('<Leave>', lambda event: setattr(self, 'pointer', None))
        self.view.bind('<ButtonPress-1>', self._mouse_down)
        self.view.bind('<Configure>', self._idle_resize, add='+')
        footer = ttk.Frame(self, padding=(16, 5))
        footer.grid(row=5, column=0, sticky='ew')
        ttk.Label(footer, textvariable=self.chart_text, style='Muted.TLabel').pack(anchor='w')
        ttk.Label(footer, text='缩圈到边缘时点击；滑条需按住并跟随光球。Z/X也需瞄准；霍尔按弦号、H1扫弦通用命中。',
                  wraplength=1150, style='Muted.TLabel').pack(anchor='w', pady=2)
        ttk.Label(footer, textvariable=self.status, wraplength=1150).pack(anchor='w')

    def _set_tracks(self):
        self.track_ids = {f'{track.name} / {INSTRUMENTS[track.instrument]}': track.id for track in self.project.active_tracks()
                          if any(clip.notes for clip in track.clips)}
        self.track_box['values'] = tuple(self.track_ids)
        if self.track.get() not in self.track_ids:
            self.track.set(next(iter(self.track_ids), ''))

    def use_arrangement(self):
        self.source.set('当前编曲 · 副本')
        self.load_source()

    def load_source(self, event=None):
        self.stop('切换曲目')
        try:
            selection = self.sources[self.source.get()]
            if selection is None:
                self.project = training_project()
            elif selection == 'current':
                self.project = deepcopy(self.controller.arrangement_panel.project)
            else:
                self.project = Project.load(selection['short' if self.variant.get() == '短试听' else 'full'])
            self._set_tracks()
            self.rebuild()
        except (OSError, ValueError, KeyError) as error:
            self.status.set('载入失败：'+str(error))

    def open_project(self):
        self.stop('打开工程')
        path = filedialog.askopenfilename(parent=self, filetypes=[('Tang编曲', '*.tang.json'), ('JSON', '*.json')])
        if not path:
            return
        try:
            self.project = Project.load(path)
            self.source.set('文件 · '+Path(path).name)
            self._set_tracks()
            self.rebuild()
        except (OSError, ValueError) as error:
            self.status.set('工程无效：'+str(error))

    def _settings_changed(self):
        self.stop('设置已改变，请重新开始')

    def _idle_resize(self, event=None):
        if not self.running and self.chart is not None:
            self.view.draw(self.chart, self.session, self.last_song_time if self.session else -1.,
                           time.monotonic(), mode='准备就绪 · 离线练习无声', summary=self.summary)

    def rebuild(self, event=None):
        self.stop('谱面已更新')
        try:
            self.chart = make_chart(self.project, self.track_ids.get(self.track.get()), self.difficulty.get(),
                                    sliders=self.input_mode.get() != '霍尔拨杆')
            self.chart_text.set(f'{self.chart.name} · {self.chart.bpm} BPM · {self.chart.duration:.1f}s · '
                f'{len(self.chart.targets)}个目标 / 原轨{self.chart.source_count}组起音 · '
                f'{sum(target.slider for target in self.chart.targets)}条滑条 · 原编曲副本保持不变')
            self.session = None
            self.summary = None
            self.view.reset()
            self.view.draw(self.chart, None, -1., time.monotonic(), mode='准备就绪 · 离线练习无声')
        except ValueError as error:
            self.chart = None
            self.status.set('无法生成谱面：'+str(error))

    def _blocked(self):
        app = self.controller
        if app.draw_upload_busy or app.riff_playing:
            return '请先停止音色上传或Riff'
        if app.song_panel.player.state != 'stopped' or app.arrangement_panel.player.state != 'stopped':
            return '请先停止乐曲或编曲播放器'
        drum = app.drum_window
        if drum is not None and (drum.playing or drum.uploading):
            return '请先停止鼓步进器或上传'
        if app.port is None or not app.port.is_open:
            return '请先连接顶部FPGA UART；S3拨杆USB是另一个端口'
        return None

    def _serialize(self):
        original = self.controller.port
        if original is not None:
            self.controller.arrangement_panel._serialize_port()
            if self.probe.port is original:
                self.probe.port = self.controller.port

    def probe_fpga(self):
        self.stop('探测前停止音游')
        self._serialize()
        reason = self._blocked()
        if reason:
            self.status.set(reason)
            return
        self.invalidate_probe()
        packet = self.probe.begin(self.controller.port)
        try:
            if self.controller.port.write(packet) != len(packet):
                raise IOError('能力查询发送不完整')
        except Exception as error:
            self.invalidate_probe()
            self.status.set('探测失败：'+str(error))
            return
        self.capability_text.set('等待带序号与校验的v8合奏回复')
        self._probe_job = self.after(25, self._poll_probe)

    def _poll_probe(self):
        self._probe_job = None
        port = self.controller.port
        if port is None or port is not self.probe.port or not port.is_open:
            self.invalidate_probe()
            return
        try:
            if self.probe.feed(port.read(256), port):
                self.capability_text.set('合奏已确认；钢琴库'+('就绪' if self.probe.flags & 4 else '未就绪'))
                return
        except Exception as error:
            self.invalidate_probe()
            self.status.set('探测读取失败：'+str(error))
            return
        if self.probe.clock() >= self.probe.deadline:
            self.invalidate_probe()
            self.capability_text.set('未收到有效合奏回复，保留离线练习')
        else:
            self._probe_job = self.after(25, self._poll_probe)

    def invalidate_probe(self):
        if self._probe_job is not None:
            self.after_cancel(self._probe_job)
            self._probe_job = None
        self.probe.invalidate()
        self.capability_text.set('FPGA尚未探测')

    def start(self):
        self.stop('准备重新挑战')
        if self.chart is None:
            return
        try:
            offset = self.offset.get()
            if not -250 <= offset <= 250:
                raise ValueError('输入校准范围为-250..250ms；正值补偿偏晚的输入')
            hall_mode = self.input_mode.get() == '霍尔拨杆'
            if hall_mode:
                hall = self.controller.hall_panel
                reading = hall.diagnostic_status.get('HALL,STATE')
                if hall.port is None or not hall.port.is_open or not hall.compatible or reading is None or time.monotonic()-reading[0] > 3 or ',ARMED,1,' not in reading[1]:
                    raise ValueError('请先在霍尔页连接S3、校准并启用拨杆，再返回；音游不自动启用传感器')
            performance = self.game_mode.get() == '命中发声'
            if performance and self.chart.instrument not in ('guitar', 'drums'):
                raise ValueError('命中发声首版支持吉他/鼓；钢琴或提琴请选择跟拍练习')
            hardware = self.hardware.get()
            if hardware:
                self._serialize()
                reason = self._blocked()
                if reason:
                    raise ValueError(reason)
                if not self.probe.usable(self.controller.port):
                    raise ValueError('请先在本页探测FPGA合奏能力')
                if any(track.instrument == 'piano' for track in self.project.active_tracks()) and not self.probe.flags & 4:
                    raise ValueError('钢琴参数库尚未就绪，请等待SD加载后重新探测')
            plan = game_plan(self.project, self.chart.instrument, hardware, performance)
            self.session = Session(self.chart, offset, assist=hall_mode, autoplay=self.autoplay.get())
            self.live_hw, self.live_performance = hardware, performance
            self.summary = None
            self.held.clear()
            self.hall_input = HallInput()
            self.view.reset()
            self.running = True
            self.last_song_time = -LEAD_IN
            if hardware:
                self._captured_port = self.controller.port
                sender = PlaybackSender(self._captured_port)
                if performance:
                    self.striker = LiveStriker(PlaybackSender(self._captured_port))
                self.player.play(plan, send=sender)
            else:
                self.origin = time.monotonic()+LEAD_IN
            self.status.set(('板端音乐' if hardware else '离线无声练习')+' · '+self.game_mode.get()+
                ' · '+('演示不记录成绩' if self.autoplay.get() else '正校准值补偿输入偏晚；Esc停止'))
            self.view.focus_set()
            self._schedule()
        except (ValueError, tk.TclError) as error:
            self.stop('未开始：'+str(error))

    def _clock(self, wall):
        if not self.live_hw:
            return wall-self.origin, False
        snapshot = self.player.snapshot()
        if snapshot.state == 'stopped':
            if '播放完成' in snapshot.message:
                return self.chart.duration+1, False
            self.stop(snapshot.message)
            return self.last_song_time, False
        if snapshot.preparing or snapshot.published_at == 0:
            return -LEAD_IN, True
        extra = max(0., wall-snapshot.published_at)
        return min(snapshot.plan.duration, snapshot.position+extra)-LEAD_IN, False

    def _schedule(self):
        if self._frame_job is None and self.running:
            self._frame_job = self.after(16, self._animate)

    def _animate(self):
        self._frame_job = None
        if not self.running:
            return
        wall = time.monotonic()
        if self.live_hw and (self.controller.port is not self._captured_port or not self._captured_port.is_open):
            self.stop('FPGA串口断开，停止音游')
            return
        if self.input_mode.get() == '霍尔拨杆':
            port = self.controller.hall_panel.port
            if port is None or not port.is_open:
                self.stop('S3拨杆串口断开，停止本次挑战')
                return
        if self.striker is not None and self.striker.error:
            self.stop('命中发声异常：'+self.striker.error)
            return
        song_time, preparing = self._clock(wall)
        if not self.running:
            return
        self.last_song_time = song_time
        if not preparing:
            for result in self.session.advance(song_time, self.pointer, bool(self.held)):
                self._feedback(result, wall)
            if self.session.autoplay and self.live_hw and self.live_performance:
                # The demonstration triggers targets only once, including slider heads.
                for target in self.chart.targets:
                    if target.at <= song_time and target.id not in self._demo_sent:
                        self._demo_sent.add(target.id)
                        self.striker.submit(strike_frames(target, self.chart.instrument))
            if song_time >= self.chart.duration+.2:
                self._finish()
        mode = ('FPGA MUSIC' if self.live_hw else 'SILENT PRACTICE')+'  /  '+self.input_mode.get()
        if self.session.autoplay:
            mode += '  /  DEMO'
        self.view.draw(self.chart, self.session, song_time, wall, self.pointer, mode, self.summary, preparing)
        self._schedule()

    def _feedback(self, result, wall):
        if result is not None:
            self.view.burst(result, wall)

    def _tap(self, at=None, string=0):
        if not self.running or self.session is None or self.session.autoplay:
            return
        wall = time.monotonic()
        song_time, preparing = self._clock(wall)
        if preparing or not self.running:
            return
        if at is not None:
            song_time -= max(0., wall-at)
        result = self.session.tap(song_time, self.pointer, string)
        if result:
            self._feedback(result, wall)
            if self.striker is not None and not self.striker.submit(strike_frames(result.target, self.chart.instrument)):
                self.stop('命中发声队列失败，请重新连接后重试')

    def _motion(self, event):
        self.pointer = self.view.world(event.x, event.y)

    def _mouse_down(self, event):
        self._motion(event)
        self.view.focus_set()
        if self.input_mode.get() != '鼠标 / Z·X' or 'mouse' in self.held:
            return
        self.held.add('mouse')
        self._tap()

    def _mouse_up(self, event=None):
        self.held.discard('mouse')

    def _key_down(self, event):
        if self.controller.active_page != 'rhythm':
            return
        key = event.keysym.lower()
        if key == 'escape':
            self.stop()
            return 'break'
        if not self.running or self.input_mode.get() != '鼠标 / Z·X' or key not in ('z', 'x'):
            return
        if event.widget.winfo_class() in ('Entry', 'TEntry', 'TSpinbox', 'TCombobox', 'Text'):
            return
        if key not in self.held:
            self.held.add(key)
            self._tap()
        return 'break'

    def _key_up(self, event):
        self.held.discard(event.keysym.lower())

    def _focus_out(self, event):
        if self.controller.focus_displayof() is None:
            self.held.clear()  # lost application focus cannot hold a slider forever

    def _hall_line(self, line, received):
        if not self.running or self.input_mode.get() != '霍尔拨杆':
            return
        hit = self.hall_input.feed(line, received)
        if hit is not None:
            self._tap(hit.at, hit.string)

    def _finish(self):
        self.session.advance(self.chart.duration+2)
        self.summary = self.session.summary()
        profile = self.input_mode.get()+':'+self.game_mode.get()+(' FPGA' if self.live_hw else ' silent')
        try:
            saved = self.store.record(self.summary, profile)
            message = '本地新纪录已保存' if saved else '挑战完成' if not self.summary['autoplay'] else '演示完成，不记成绩'
        except OSError as error:
            message = '挑战完成，成绩写入失败：'+str(error)
        self.stop(message)

    def stop(self, message='已停止；Esc可随时结束'):
        self.running = False
        if self._frame_job is not None:
            self.after_cancel(self._frame_job)
            self._frame_job = None
        self.held.clear()
        if self.striker is not None:
            self.striker.shutdown()
            self.striker = None
        if self.player.state != 'stopped':
            self.player.stop(message)
            self.player.wait_ready()
        self.status.set(message)
        self._demo_sent = set()

    def on_hide(self):
        self.stop('已离开音游页，音乐与判定停止')
        self.invalidate_probe()

    def on_disconnect(self):
        self.stop('串口断开，音游停止')
        self.invalidate_probe()

    def close(self):
        self.stop('关闭音游')
        self.invalidate_probe()
        self.destroy()

    def destroy(self):
        if self._destroying:
            return
        self.stop('关闭音游')
        self.player.shutdown()
        hall = getattr(self.controller, 'hall_panel', None)
        if hall and self._hall_line in hall.line_listeners:
            hall.line_listeners.remove(self._hall_line)
        for name, token in getattr(self, '_bindings', ()):
            self.controller.unbind(name, token)
        super().destroy()
