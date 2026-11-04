"""MIDI guitar practice lights using the existing S3 USB connection."""
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk, filedialog

from midi_guide import read_midi, fingering, guide_masks, mask_command
from ui_pages import EmbeddedPage
from ui_theme import scroll_body


class MidiGuidePanel(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.score = None
        self.notes = ()
        self.running = False
        self.position = 0.
        self.origin = 0.
        self.last_mask = None
        self.last_send = 0.
        self.capable_port = None
        self.pending_port = None
        self.session_port = None
        self.await_until = 0.
        self.upload_name = tk.StringVar(value='未导入 MIDI')
        self.status = tk.StringVar(value='导入 MIDI → 选择轨道 → 连接 S3 → 开始跟灯。跟灯练习由实体演奏发声。')
        self.track = tk.StringVar()
        self.speed = tk.IntVar(value=100)
        self.transpose = tk.IntVar(value=0)
        self.progress = tk.DoubleVar(value=0)
        self._track_ids = {}
        body = scroll_body(self, padding=16)
        ttk.Label(body, text='MIDI 跟灯练习', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='蓝色：谱面提示；绿色：实际按键。21个品位灯＋6根弦灯；空弦对应第1位。', wraplength=1000).pack(anchor='w', pady=8)
        row = ttk.Frame(body); row.pack(fill='x')
        for index, (title, action) in enumerate([('导入 MIDI', self.load), ('连接 S3', lambda: controller.show_page('hall')),
                              ('开始 / 继续', self.play), ('暂停', self.pause), ('停止', self.stop),
                              ('恢复炫彩展示', self.demo)]):
            ttk.Button(row, text=title, command=action).grid(row=index//3, column=index%3, padx=3, pady=3, sticky='ew')
        ttk.Label(body, textvariable=self.upload_name).pack(anchor='w', pady=8)
        controls = ttk.Frame(body); controls.pack(fill='x')
        ttk.Label(controls, text='引导轨道').pack(side='left')
        self.tracks = ttk.Combobox(controls, textvariable=self.track, state='readonly', width=28)
        self.tracks.pack(side='left', padx=6)
        self.tracks.bind('<<ComboboxSelected>>', lambda e: self.select())
        controls = ttk.Frame(body); controls.pack(fill='x', pady=6)
        for label, var, low, high in [('速度 %', self.speed, 25, 150), ('移调', self.transpose, -36, 36)]:
            ttk.Label(controls, text=label).pack(side='left', padx=6)
            ttk.Spinbox(controls, textvariable=var, from_=low, to=high, width=6,
                        command=self.changed).pack(side='left')
        ttk.Button(controls, text='应用速度 / 移调', command=self.changed).pack(side='left', padx=6)
        self.scale = ttk.Scale(body, variable=self.progress, from_=0, to=1, command=self.seek)
        self.scale.pack(fill='x', pady=16)
        self.canvas = tk.Canvas(body, height=260, background='#10162A', highlightthickness=0)
        self.canvas.pack(fill='x')
        ttk.Label(body, textvariable=self.status, wraplength=1050).pack(anchor='w', pady=12)
        ttk.Label(body, text='默认只引导一个旋律轨，跳过第10通道鼓。超出E2–C6的音符不亮灯，可移调。\n'
                  '同音选择最低可用品位；多音同时显示品位与弦的集合，灯板不能区分每个交叉点。\n'
                  '按真实MIDI速度事件和延音踏板计时；暂停、停止、换曲清灯，断联后1秒内自动清除引导。',
                  wraplength=1050).pack(anchor='w')
        controller.hall_panel.line_listeners.append(self.line)
        self._job = self.after(20, self.tick)
        self.paint([])

    def line(self, line, received):
        if 'LED,GUIDE,CAP,1' in line and self.pending_port is self.controller.hall_panel.port:
            self.capable_port = self.pending_port
        if 'ERROR,LED' in line and (self.running or self.await_until):
            self.pause(); self.status.set('S3拒绝灯光指令：' + line)

    def send(self, data):
        return self.controller.hall_panel.send(data, quiet=True)

    def load(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[('标准 MIDI', '*.mid *.midi')])
        if not path: return
        self.stop()
        try:
            self.score = read_midi(path)
            self._track_ids = {f'{i+1}: {name}': i for i, name in enumerate(self.score.names)
                               if any(n.track == i and n.channel != 9 for n in self.score.notes)}
            if not self._track_ids: raise ValueError('文件只有鼓轨，没有弦品引导音符')
            self.tracks.configure(values=tuple(self._track_ids))
            self.track.set(next(iter(self._track_ids)))
            self.upload_name.set(f'{Path(path).name} · {self.score.duration:.1f} 秒 · {len(self.score.notes)} 音符')
            self.scale.configure(to=max(.01, self.score.duration))
            self.select()
        except (OSError, ValueError) as error:
            self.score = None; self.notes = (); self.status.set('导入失败：' + str(error))

    def select(self):
        self.stop()
        if self.score:
            self.notes = tuple(n for n in self.score.notes if n.track == self._track_ids.get(self.track.get()) and n.channel != 9)
            self.changed()

    def changed(self):
        self.pause()
        try:
            self.rate = int(self.speed.get()) / 100
            self.shift = int(self.transpose.get())
            if not .25 <= self.rate <= 1.5 or not -36 <= self.shift <= 36: raise ValueError('参数超范围')
            missed = sum(fingering(n.pitch+self.shift) is None for n in self.notes)
            self.status.set(f'已选 {len(self.notes)} 音符，{missed} 个超出弦品范围；速度 {self.speed.get()}%。')
        except (ValueError, tk.TclError) as error:
            self.status.set('设置无效：' + str(error))

    def play(self):
        hall = self.controller.hall_panel
        if not self.notes: self.status.set('请先导入MIDI并选择有音符的轨道'); return
        if hall.port is None or not hall.compatible:
            self.status.set('请先在霍尔页连接 S3 原生USB并等待握手'); return
        self.changed()
        try:
            rate = int(self.speed.get())/100; shift = int(self.transpose.get())
            if not .25 <= rate <= 1.5 or not -36 <= shift <= 36: return
        except (ValueError, tk.TclError): return
        self.rate, self.shift = rate, shift
        if self.capable_port is not hall.port:
            self.pending_port = hall.port
            if self.send(b'LED,GUIDE,STATUS\n'):
                self.await_until = time.monotonic()+2
                self.status.set('正在确认S3实时引导能力…')
            return
        self.await_until = 0
        if self.position >= self.score.duration: self.position = 0
        if not self.send(b'LED,CLEAR\nLED,MODE,BOTH\n'): return
        self.session_port = hall.port
        self.running = True; self.origin = time.monotonic()-self.position/self.rate
        self.last_mask = None
        self.status.set('跟灯练习中：请按照亮起的品位和弦演奏')

    def clear(self):
        hall = self.controller.hall_panel
        if self.session_port is not None and self.session_port is hall.port and hall.compatible:
            self.send(mask_command(0, 0))
        self.last_mask = None

    def pause(self):
        self.await_until = 0
        if self.running: self.position = max(0, (time.monotonic()-self.origin)*self.rate)
        self.running = False; self.clear(); self.paint([])

    def stop(self):
        self.pause(); self.position = 0; self.progress.set(0)

    def demo(self):
        self.stop(); self.send(b'LED,CLEAR\nLED,MODE,DEMO\n')

    def seek(self, value):
        self.pause(); self.position = float(value)
        self.status.set(f'定位到 {self.position:.1f} 秒，点击继续')

    def paint(self, active):
        self.canvas.delete('all')
        width = max(300, self.canvas.winfo_width())
        for string in range(1, 7):
            y = 30+(string-1)*35
            self.canvas.create_line(45, y, width-10, y, fill='#4B5370')
            self.canvas.create_text(20, y, text=f'{string}弦', fill='white')
        for fret in range(21):
            x = 60+fret*(width-90)/21
            self.canvas.create_text(x, 245, text=str(fret), fill='#A0AEC0')
        for pitch, fret, string in active:
            x = 60+fret*(width-90)/21; y=30+(string-1)*35
            self.canvas.create_oval(x-10,y-10,x+10,y+10,fill='#00D5FF',outline='')

    def tick(self):
        now = time.monotonic(); hall = self.controller.hall_panel
        if self.await_until:
            if self.capable_port is hall.port and hall.port is not None:
                self.await_until = 0; self.play()
                now = time.monotonic()
            elif now > self.await_until:
                self.await_until = 0; self.status.set('当前S3未报告实时引导能力，需烧入配套MIDI跟灯固件')
        if self.running:
            if hall.port is not self.session_port or not hall.compatible:
                self.pause(); self.status.set('S3连接已断开，练习停止；重新连接后再开始')
            else:
                self.position = (now-self.origin)*self.rate
                if self.position >= self.score.duration:
                    self.stop(); self.status.set('练习完成，引导灯已清除')
                else:
                    p, s, active = guide_masks(self.notes, self.position, self.shift)
                    if (p,s) != self.last_mask or now-self.last_send >= .25:
                        if self.send(mask_command(p,s)):
                            self.last_mask=(p,s); self.last_send=now
                        else:
                            self.pause(); self.status.set('灯光发送失败，已停止')
                    self.progress.set(self.position); self.paint(active)
        self._job = self.after(20, self.tick)

    def on_hide(self):
        self.pause()

    def destroy(self):
        self.pause()
        self.after_cancel(self._job)
        if self.line in self.controller.hall_panel.line_listeners:
            self.controller.hall_panel.line_listeners.remove(self.line)
        super().destroy()
