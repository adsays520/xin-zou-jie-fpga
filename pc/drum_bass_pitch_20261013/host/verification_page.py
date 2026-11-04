"""Single-window live hardware observability and clearly labelled preview."""
import time
import tkinter as tk
from tkinter import ttk, filedialog
import json
from pathlib import Path
import numpy as np
from ui_pages import EmbeddedPage
from ui_theme import COLORS as C, card, button, scroll_body
from live_verification import CaptureParser, PreviewSynth, configure, frame, spectrum, peaks


class VerificationPage(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.mode = tk.StringVar(value='板端回传')
        self.status = tk.StringVar(value='先读取板端数据；旧位流不会回传，需烧录本次新增 RTL。')
        self.evidence = tk.StringVar(value='尚无实测数据 · ≤5 ms 整机延迟待示波器验收')
        self.summary = tk.StringVar(value='等待音频采样')
        self.fast_key = tk.BooleanVar(value=False)
        self.frequency = [tk.StringVar(value=str(f)) for f in (375, 750, 1125, 1500)]
        self.gain = [tk.IntVar(value=80) for _ in range(4)]
        self.pan = [tk.IntVar(value=p) for p in (24, 104, 64, 64)]
        self.enabled = [tk.BooleanVar(value=i < 3) for i in range(4)]
        self.parser = CaptureParser()
        self.synth = PreviewSynth()
        self.monitoring = False
        self.running = False
        self.last_capture = None
        self.last_rx = 0
        self.request_at = None
        self.sequence = None
        self.dropped = 0
        self.port_seen = None
        self.last_preview = 0
        self.preview_settings = None
        body = scroll_body(self, padding=(22, 18, 22, 18))
        ttk.Label(body, text='现场验证与实时视听', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='外接屏幕上电自动显示 · G15 切换波形 / 频谱 / 李萨如；以下读取仅用于电脑图表',
                  style='Page.TLabel').pack(anchor='w', pady=(5, 14))
        controls = card(body, '测试通路', accent='blue', padding=14)
        controls.pack(fill='x')
        row = ttk.Frame(controls)
        row.pack(fill='x', pady=(0, 12))
        mode = ttk.Combobox(row, textvariable=self.mode, values=('板端回传', '离线预览'), state='readonly', width=12)
        mode.pack(side='left')
        mode.bind('<<ComboboxSelected>>', lambda e: self.change_mode())
        button(row, '读取板端数据 / 开始预览', self.monitor, 'Blue').pack(side='left', padx=6)
        button(row, '停止观测', self.stop_monitor).pack(side='left')
        table = ttk.Frame(controls)
        table.pack(fill='x')
        for j, title in enumerate(('启用', '频率 Hz', '音量 0–127', '声像 0左 / 64中 / 127右')):
            ttk.Label(table, text=title, style='Muted.TLabel').grid(row=0, column=j, padx=8, sticky='w')
        table.columnconfigure(2, weight=1)
        table.columnconfigure(3, weight=1)
        for i in range(4):
            ttk.Checkbutton(table, text='通路 '+str(i+1), variable=self.enabled[i]).grid(row=i+1, column=0, padx=8, sticky='w')
            ttk.Spinbox(table, from_=50, to=5000, increment=25, textvariable=self.frequency[i], width=8).grid(row=i+1, column=1, padx=8, pady=3)
            ttk.Scale(table, from_=0, to=127, variable=self.gain[i]).grid(row=i+1, column=2, sticky='ew', padx=8)
            ttk.Scale(table, from_=0, to=127, variable=self.pan[i]).grid(row=i+1, column=3, sticky='ew', padx=8)
        actions = ttk.Frame(controls)
        actions.pack(fill='x', pady=(12, 6))
        for col in range(4):
            actions.columnconfigure(col, weight=1, uniform='test_action')
        for count in (1, 2, 3, 4):
            button(actions, str(count)+' 路预设', lambda n=count: self.preset(n)).grid(row=0, column=count-1, sticky='ew', padx=3)
        button(actions, '应用 / 启动测试', self.start, 'Primary').grid(row=1, column=0, columnspan=2, sticky='ew', padx=3, pady=(8,0))
        button(actions, '停止测试 / 恢复演奏', self.stop, 'Warm').grid(row=1, column=2, columnspan=2, sticky='ew', padx=3, pady=(8,0))
        ttk.Label(controls, textvariable=self.status, wraplength=740, style='Muted.TLabel').pack(anchor='w', pady=(6, 0))
        info = card(body, '证据与延迟', accent='teal', padding=12)
        info.pack(fill='x', pady=12)
        ttk.Label(info, textvariable=self.evidence, wraplength=740).pack(anchor='w')
        ttk.Label(info, textvariable=self.summary, wraplength=740, style='Muted.TLabel').pack(anchor='w', pady=6)
        button(info, '导出当前采样与验证记录', self.export, 'Teal').pack(anchor='w')
        ttk.Checkbutton(info, text='低延迟板键演奏：F15 短按直接拨弦（原调音 / 长按功能暂停）',
                        variable=self.fast_key, command=self.set_fast_key).pack(anchor='w', pady=(6, 0))
        plots = ttk.Frame(body, style='Page.TFrame')
        plots.pack(fill='x')
        self.wave = self.plot(plots, '波形 · 左蓝 / 右橙', 170)
        self.fft = self.plot(plots, '频谱 · 双声道能量合并 / dBFS', 200)
        self.xy = self.plot(plots, '李萨如 · X=左声道 / Y=右声道', 210)
        ttk.Label(body, text='板端模式显示 FPGA 最终 I²S 送数点的回传采样。FFT 窗口 512 点 / 12 kHz，分辨率 23.44 Hz；'
                  '115200 串口下观测约 4 次/秒，显示刷新不计入演奏延迟。离线预览无音频播放、不能作为硬件证据。',
                  style='Page.TLabel', wraplength=740).pack(anchor='w', pady=12)
        def reflow(event):
            def visit(widget):
                if isinstance(widget, ttk.Label) and int(widget.cget('wraplength') or 0)>0:
                    widget.configure(wraplength=max(240,event.width-100))
                for child in widget.winfo_children():
                    visit(child)
            visit(body)
        body.bind('<Configure>', reflow, add='+')
        self.after(20, self.poll)

    def plot(self, parent, title, height):
        panel = card(parent, title, accent='violet', padding=10)
        panel.pack(fill='x', pady=(0, 10))
        canvas = tk.Canvas(panel, height=height, background='#101F30', highlightthickness=0)
        canvas.pack(fill='x')
        canvas.bind('<Configure>', lambda e: self.render() if self.last_capture is not None else None)
        return canvas

    def settings(self):
        frequencies = [int(v.get()) for v in self.frequency]
        gains = [int(round(float(v.get()))) if e.get() else 0 for v, e in zip(self.gain, self.enabled)]
        pans = [int(round(float(v.get()))) for v in self.pan]
        configure(frequencies, gains, pans)  # validates before changing any board state
        return frequencies, gains, pans

    def preset(self, count):
        for i, freq in enumerate((375, 750, 1125, 1500)):
            self.frequency[i].set(str(freq))
            self.enabled[i].set(i < count)
            self.gain[i].set(80)
            self.pan[i].set((24, 104, 64, 64)[i])
        self.status.set('已选择 %d 路预设，点击“应用 / 启动测试”提交。' % count)

    def write(self, data):
        app = self.controller
        if app.draw_upload_busy:
            self.status.set('双表正在上传，请等待完成。')
            return False
        if app.port is None or not app.port.is_open:
            self.status.set('未连接串口。')
            return False
        try:
            if app.port.write(data) != len(data):
                raise IOError('串口写入不完整')
            return True
        except Exception as exc:
            self.status.set('通信失败：'+str(exc))
            app.disconnect()
            return False

    def change_mode(self):
        self.stop()
        if self.fast_key.get():
            self.fast_key.set(False)
            self.write(frame(0x85, 0))
        self.monitoring = False
        self.last_capture = None
        self.last_rx = 0
        self.request_at = None
        self.preview_settings = None
        self.evidence.set('离线数值预览 · 无音频输出 · 无硬件证据' if self.mode.get() == '离线预览' else '等待新的板端回传')
        self.summary.set('等待音频采样')
        for canvas in (self.wave, self.fft, self.xy):
            canvas.delete('all')

    def monitor(self):
        if self.mode.get() == '离线预览':
            try:
                self.preview_settings = self.settings()
            except ValueError as exc:
                self.status.set(str(exc)); return
            self.monitoring = True
            self.status.set('离线预览已开启；此模式只绘图，不播放声音。')
            return
        if self.write(frame(0x84, 1)):
            self.monitoring = True
            self.parser = CaptureParser()
            self.sequence = None
            self.request_at = None
            self.last_rx = 0
            self.status.set('读取真实送数点；若 1 秒无回传，请检查位流和 UART TX 接线。')

    def stop_monitor(self):
        self.monitoring = False
        self.request_at = None
        if self.mode.get() == '板端回传':
            self.write(frame(0x84, 0))
        self.evidence.set('观测已暂停 · 当前图为冻结历史采样')

    def set_fast_key(self):
        if self.mode.get() != '板端回传' or time.monotonic()-self.last_rx > 1:
            self.fast_key.set(False)
            self.status.set('先读取有效板端回传，再切换 F15 演奏模式。')
            return
        if not self.write(frame(0x85, int(self.fast_key.get()))):
            self.fast_key.set(False)
        else:
            self.status.set('F15 模式已发送；以板端回传状态为准。首次按下立即触发，释放稳定 20 ms 后重新允许触发。')

    def start(self):
        try:
            settings = self.settings()
            data = configure(*settings)
        except ValueError as exc:
            self.status.set(str(exc)); return
        if self.mode.get() == '离线预览':
            self.preview_settings = settings
            self.monitoring = True
            self.running = False
            self.status.set('离线预览已更新 · 无音频输出。')
            return
        if not self.monitoring or time.monotonic()-self.last_rx > 1:
            self.status.set('先读取有效板端回传，再启动测试；不能向未知位流声明测试成功。')
            return
        app = self.controller
        if getattr(app, 'riff_playing', False):
            app.stop_riff('进入现场测试')
        if app.drum_window is not None:
            app.drum_window.stop()
        if self.write(data):
            self.running = True
            self.status.set('配置已发送；以回传运行位和实际谱峰为准。测试替代演奏总输出，停止后恢复。')

    def stop(self):
        if getattr(self, '_stopping', False):
            return
        if self.running or (self.mode.get() == '板端回传' and self.last_capture is not None
                            and self.last_capture.flags & 1 and time.monotonic()-self.last_rx <= 1):
            # Clear the flag before writing; error handling may call disconnect again.
            self.running = False
            self._stopping = True
            try:
                self.write(frame(0x82, 0))
            finally:
                self._stopping = False
        self.status.set('测试已停止；若串口异常，板端状态需复位确认。')

    def on_disconnect(self):
        was_monitoring = self.monitoring
        self.monitoring = False
        self.stop()
        if self.fast_key.get():
            self.fast_key.set(False)
            self.write(frame(0x85, 0))
        if was_monitoring and self.mode.get() == '板端回传':
            self.write(frame(0x84, 0))
        self.monitoring = False
        self.last_rx = 0
        self.port_seen = None
        self.parser = CaptureParser()
        self.evidence.set('连接已断开 · 图为历史采样，不能代表当前硬件状态')

    def poll(self):
        now = time.monotonic()
        app = self.controller
        if self.monitoring and self.mode.get() == '离线预览':
            if now-self.last_preview >= .1:
                self.last_preview = now
                self.accept(self.synth.capture(*self.preview_settings), now, preview=True)
        elif self.monitoring and app.port is not None:
            if self.port_seen is not app.port:
                self.port_seen = app.port
                self.parser = CaptureParser()
                self.request_at = None
                self.sequence = None
            try:
                available = getattr(app.port, 'in_waiting', 0)
                if available:
                    for capture in self.parser.feed(app.port.read(min(available, 8192))):
                        self.accept(capture, now)
                        self.request_at = None
                if self.request_at is None or now-self.request_at > 1:
                    if self.request_at is not None:
                        self.evidence.set('回传超时 · 当前曲线为历史采样 · 检查固件及 FPGA→主机串口通路')
                    if self.write(frame(0x83)):
                        self.request_at = now
                if self.last_rx and now-self.last_rx > 1:
                    self.evidence.set('采样已过期 · 当前曲线为历史采样')
            except Exception as exc:
                self.status.set('接收失败：'+str(exc))
                app.disconnect()
        self.after(20, self.poll)

    def accept(self, capture, now, preview=False):
        if self.sequence is not None and not preview:
            distance = (capture.sequence-self.sequence) & 65535
            if distance == 0 or distance > 32768:
                return
            self.dropped += max(0, distance-1)
        self.sequence = capture.sequence
        self.last_capture = capture
        self.last_rx = now
        if preview:
            self.evidence.set('离线数值预览 · 无音频播放 · 不能验证板端合成或 ≤5 ms')
        else:
            latency = ('DDS 指令校验完成→首个非零合成采样 %.4f ms' % capture.latency_ms
                       if capture.flags & 2 else '尚无 DDS 指令响应计时')
            self.evidence.set('FPGA 实际送数点 · %d 路测试 / %s · %s · 整机 ≤5 ms 待实测\nF15 %s · 采样截止期 %s' %
                              (capture.active_count, '运行' if capture.flags & 1 else '停止', latency,
                               '直接演奏' if capture.flags & 8 else '原操作模式', '违例！' if capture.flags & 4 else '未报告违例'))
        detected = peaks(capture.samples, capture.sample_rate)
        selected = sorted(detected[:8])
        clipping = int(np.count_nonzero(np.abs(capture.samples.astype(np.int32)) >= 32767))
        self.summary.set('序号 %d · CRC 错误 %d · 缺帧 %d · 满量程点 %d\n可见谱峰：%s' %
                         (capture.sequence, self.parser.bad_packets, self.dropped, clipping,
                          ' / '.join('%.1f Hz (%.1f dBFS)' % p for p in selected) or '无明显峰'))
        if app_active(self.controller):
            self.render()

    def grid_axes(self, canvas, subtitle):
        canvas.delete('all')
        w, h = max(100, canvas.winfo_width()), canvas.winfo_height()
        for x in np.linspace(40, w-12, 9):
            canvas.create_line(x, 22, x, h-24, fill='#26384B')
        for y in np.linspace(22, h-24, 5):
            canvas.create_line(40, y, w-12, y, fill='#26384B')
        canvas.create_text(8, 8, anchor='nw', text=subtitle, fill='#C1D4E6', font=('Segoe UI', 9))
        canvas.create_text(w-10, 8, anchor='ne',
                           text='离线预览 · 非硬件证据' if self.mode.get() == '离线预览' else '板端回传 · 非整机延迟实测',
                           fill='#FFB366', font=('Microsoft YaHei UI', 9))
        return w, h

    def render(self):
        if self.last_capture is None:
            return
        capture = self.last_capture
        data = capture.samples.astype(float)/32768
        w, h = self.grid_axes(self.wave, '±1 FS · 0–%.2f ms' % (128/capture.sample_rate*1000))
        xs = np.linspace(40, w-12, 128)
        for ch, color in ((0, '#59B8FA'), (1, '#FFB366')):
            ys = (h-2)/2-data[:128, ch]*(h-46)/2
            self.wave.create_line(*np.column_stack((xs, ys)).ravel().tolist(), fill=color, width=2)
        hz, db = spectrum(capture.samples, capture.sample_rate)
        w, h = self.grid_axes(self.fft, '-100–0 dBFS · 0–6000 Hz · Δf=23.44 Hz')
        xs = 40+hz/6000*(w-52)
        ys = 22+np.clip(-db, 0, 100)/100*(h-46)
        self.fft.create_line(*np.column_stack((xs, ys)).ravel().tolist(), fill='#51D6BA', width=2)
        for frequency, level in peaks(capture.samples, capture.sample_rate)[:8]:
            x = 40+frequency/6000*(w-52)
            y = 22+min(100, -level)/100*(h-46)
            self.fft.create_text(x+4, y-10, anchor='w', text='%.0f' % frequency, fill='#D8F3EA', font=('Segoe UI', 9))
        common_gain = 1.0/max(.05, float(np.max(np.abs(data)))*1.1)
        w, h = self.grid_axes(self.xy, 'X=L / Y=R · 同比例放大 ×%.1f' % common_gain)
        scale = min(w-52, h-46)/2*common_gain
        # Plot true relative level; do not normalise channels independently.
        self.xy.create_line(*np.column_stack(((w+28)/2+data[:, 0]*scale,
                                               (h-2)/2-data[:, 1]*scale)).ravel().tolist(),
                            fill='#C2A4F4', width=1)

    def export(self):
        if self.last_capture is None:
            self.status.set('尚无采样可以导出。'); return
        filename = filedialog.asksaveasfilename(parent=self.controller, title='保存验证记录',
                                               defaultextension='.json', filetypes=[('验证记录', '*.json')])
        if not filename:
            return
        c = self.last_capture
        preview = self.mode.get() == '离线预览'
        record = dict(source='offline_preview' if preview else 'fpga_i2s_word_tap',
                      captured_at=time.strftime('%Y-%m-%d %H:%M:%S'), sequence=c.sequence,
                      stale=not self.monitoring or time.monotonic()-self.last_rx > 1,
                      sample_rate=c.sample_rate, active_count=c.active_count,
                      latency_cycles=None if preview or not c.flags & 2 else c.latency_cycles,
                      latency_scope='DDS validated start command to first nonzero DDS sample; excludes USB, input and DAC',
                      end_to_end_5ms_verified=False, flags=c.flags, crc_errors=self.parser.bad_packets,
                      missing_frames=self.dropped, peaks_hz_dbfs=peaks(c.samples, c.sample_rate),
                      samples_lr=c.samples.tolist())
        try:
            Path(filename).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
            self.status.set('已导出当前实际来源和验证边界：'+filename)
        except OSError as exc:
            self.status.set('导出失败：'+str(exc))

    def close(self):
        self.stop()
        if self.fast_key.get():
            self.fast_key.set(False)
            self.write(frame(0x85, 0))
        if self.monitoring and self.mode.get() == '板端回传':
            self.monitoring = False
            self.write(frame(0x84, 0))
        self.monitoring = False
        self.destroy()


def app_active(app):
    return app.active_page == 'verify'
