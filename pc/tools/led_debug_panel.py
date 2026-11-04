"""LED-only USB control panel. Flashing and audio commands are not supported."""
import argparse
import math
import queue
import re
import threading
import time
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

import serial
from serial.tools import list_ports


PINS = {'GPIO3 · 13颗': 3, 'GPIO7 · 14颗': 7, '两路 · 27颗': 0}
TIMINGS = {'714kHz · 降频试验': 'SLOW714', '800kHz · 350/900ns': 'LEGACY',
           '800kHz · 厂家典型值': 'XL'}
ENCODERS = {'整帧字节 · 新版': 'BYTES', '手工符号 · 旧版对照': 'COPY'}


def output_command(pin, rgb, brightness, blink, frequency, duty):
    if pin not in (0, 3, 7) or len(rgb) != 3:
        raise ValueError('请选择GPIO3、GPIO7或两路')
    if any(not 0 <= x <= 255 or int(x) != x for x in rgb):
        raise ValueError('R、G、B必须是0～255的整数')
    if not math.isfinite(brightness) or not 0 <= brightness <= 100:
        raise ValueError('亮度须为0～100%')
    period = on = 0
    if blink:
        if not math.isfinite(frequency) or not .1 <= frequency <= 10:
            raise ValueError('闪烁频率须为0.1～10Hz')
        if not math.isfinite(duty) or not 10 <= duty <= 90:
            raise ValueError('亮灯占比须为10～90%')
        period = round(1000 / frequency)
        on = round(period * duty / 100)
        on = max(10, min(period - 10, on))
    channels = [round(x * brightness / 100) for x in rgb]
    return f'LED,OUTPUT,{pin},' + ','.join(map(str, [*channels, period, on]))


def payload(line):
    line = re.sub(r'\x1b\[[0-9;]*m', '', line).strip()
    return line.split('HOST_REPLY:', 1)[-1].strip()


class Link(threading.Thread):
    """One worker owns the serial port. Waiting for replies never blocks Tk."""
    def __init__(self, port, events):
        super().__init__(daemon=True)
        self.port_name, self.events = port, events
        self.commands = queue.Queue()
        self.closing = threading.Event()
        self.ready = False
        self.demo_supported = False
        self.port = None
        self.rx_buffer = bytearray()

    def read_reply(self):
        # Serial reads may time out between fragments of a HOST_REPLY line.
        # Keep incomplete bytes until the newline instead of treating each
        # fragment as a whole reply and losing its prefix.
        if b'\n' not in self.rx_buffer:
            self.rx_buffer.extend(self.port.read(min(16384, self.port.in_waiting or 1)))
        if b'\n' not in self.rx_buffer:
            if len(self.rx_buffer) > 65536:
                self.rx_buffer.clear()
            return ''
        raw, _, remaining = self.rx_buffer.partition(b'\n')
        self.rx_buffer = bytearray(remaining)
        raw = raw.decode('utf8', errors='replace')
        text = payload(raw)
        if text.startswith(('LED,', 'OK,LED', 'ERROR,', 'PONG,')):
            self.events.put(('log', '← ' + text))
            if text.startswith('LED,OUTPUT,STATE,'):
                self.events.put(('state', text))
            return text
        return ''

    def transact(self, command):
        self.events.put(('log', '→ ' + command))
        if self.port.write((command + '\n').encode('ascii')) != len(command) + 1:
            raise OSError('串口未完整写入命令')
        wanted = ('PONG,' if command == 'PING' else
                  'LED,OUTPUT,STATE,' if command == 'LED,OUTPUT,STATUS' else
                  'LED,STATE,' if command == 'LED,STATUS' else 'OK,LED')
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            text = self.read_reply()
            if text.startswith('ERROR,'):
                raise RuntimeError(text)
            if text.startswith(wanted):
                return text
        raise TimeoutError('S3未确认命令；请检查连接和固件版本')

    def run(self):
        try:
            self.port = serial.Serial(port=None, baudrate=115200, timeout=.05, write_timeout=1)
            self.port.dtr = False
            self.port.rts = False
            self.port.port = self.port_name
            self.port.open()
            greeting = self.transact('PING')
            match = re.search(r'R15-HALL-v(\d+)\.(\d+)\.(\d+)', greeting)
            if not match or tuple(map(int, match.groups())) < (3, 4, 20):
                raise RuntimeError('此工具需要S3 v3.4.20或更新固件')
            self.demo_supported = tuple(map(int, match.groups())) >= (3, 4, 24)
            self.transact('LED,OUTPUT,STATUS')
            self.ready = True
            self.events.put(('connected', greeting))
            next_status = time.monotonic() + 2
            while not self.closing.is_set():
                try:
                    batch = self.commands.get_nowait()
                except queue.Empty:
                    batch = None
                if batch:
                    try:
                        for command in batch:
                            self.transact(command)
                        self.events.put(('applied', '板端已确认'))
                    except Exception as exc:
                        self.events.put(('error', str(exc)))
                elif time.monotonic() >= next_status:
                    try:
                        self.transact('LED,OUTPUT,STATUS')
                    except TimeoutError:
                        self.events.put(('error', '状态读取暂时超时，连接保留；可重新读取或应用输出'))
                    next_status = time.monotonic() + 2
                else:
                    self.read_reply()
        except Exception as exc:
            self.events.put(('error', str(exc)))
        finally:
            if self.port and self.port.is_open:
                if self.ready:
                    try:
                        self.transact('LED,MODE,DEMO' if self.demo_supported else 'LED,MODE,OFF')
                    except Exception:
                        pass
                self.port.close()
            self.ready = False
            self.events.put(('disconnected', '已断开；已请求恢复展示模式' if self.demo_supported else '已断开；旧版固件已请求关灯'))


class Panel:
    def __init__(self, root):
        self.root, self.link = root, None
        self.events = queue.Queue()
        self.quitting = False
        root.title('LED颜色与闪烁调试 · ESP32-S3')
        root.geometry('880x760')
        root.minsize(800, 690)
        root.configure(bg='#eef2f7')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#eef2f7')
        style.configure('TLabel', background='#eef2f7', font=('Microsoft YaHei UI', 10))
        style.configure('TButton', font=('Microsoft YaHei UI', 10), padding=6)
        style.configure('TLabelframe', background='#eef2f7')
        style.configure('TLabelframe.Label', font=('Microsoft YaHei UI', 11, 'bold'), background='#eef2f7')
        box = ttk.Frame(root, padding=18)
        box.pack(fill='both', expand=True)
        ttk.Label(box, text='LED颜色与闪烁调试', font=('Microsoft YaHei UI', 19, 'bold')).pack(anchor='w')
        ttk.Label(box, text='S3原生USB · GPIO3 / GPIO7 · 闪烁由板端计时').pack(anchor='w', pady=(3, 12))

        bar = ttk.Frame(box)
        bar.pack(fill='x')
        self.port = tk.StringVar(value='COM30')
        self.ports = ttk.Combobox(bar, textvariable=self.port, width=17)
        self.ports.pack(side='left')
        ttk.Button(bar, text='刷新串口', command=self.refresh_ports).pack(side='left', padx=6)
        self.connect = ttk.Button(bar, text='连接', command=self.toggle_link)
        self.connect.pack(side='left')
        self.connection = tk.StringVar(value='未连接')
        ttk.Label(bar, textvariable=self.connection).pack(side='left', padx=12)

        settings = ttk.LabelFrame(box, text='输出设置', padding=12)
        settings.pack(fill='x', pady=12)
        self.pin = tk.StringVar(value=next(iter(PINS)))
        self.timing = tk.StringVar(value='800kHz · 350/900ns')
        ttk.Label(settings, text='输出通道').grid(row=0, column=0, sticky='w')
        ttk.Combobox(settings, textvariable=self.pin, values=list(PINS), state='readonly', width=19).grid(row=0, column=1, padx=8, sticky='w')
        ttk.Label(settings, text='数据速率').grid(row=0, column=2, sticky='w', padx=(16, 0))
        ttk.Combobox(settings, textvariable=self.timing, values=list(TIMINGS), state='readonly', width=24).grid(row=0, column=3, padx=8, sticky='w')
        self.rgb = [tk.StringVar(value=x) for x in ('255', '0', '0')]
        colors = ttk.Frame(settings)
        colors.grid(row=1, column=0, columnspan=4, sticky='w', pady=10)
        for label, var in zip(('R', 'G', 'B'), self.rgb):
            ttk.Label(colors, text=label).pack(side='left', padx=(0, 5))
            ttk.Spinbox(colors, from_=0, to=255, width=5, textvariable=var).pack(side='left', padx=(0, 14))
            var.trace_add('write', self.preview)
        ttk.Button(colors, text='自选颜色', command=self.pick_color).pack(side='left')
        self.swatch = tk.Label(colors, width=6, bg='#ff0000', relief='solid', borderwidth=1)
        self.swatch.pack(side='left', padx=12)
        self.brightness = tk.StringVar(value='10')
        ttk.Label(settings, text='亮度 (%)').grid(row=2, column=0, sticky='w')
        ttk.Spinbox(settings, from_=0, to=100, increment=1, width=7, textvariable=self.brightness).grid(row=2, column=1, sticky='w', padx=8)
        ttk.Label(settings, text='RGB先乘以亮度，再发送给S3').grid(row=2, column=2, columnspan=2, sticky='w', padx=16)
        self.encoder = tk.StringVar(value=next(iter(ENCODERS)))
        ttk.Label(settings, text='发送编码').grid(row=3, column=0, sticky='w', pady=(10, 0))
        ttk.Combobox(settings, textvariable=self.encoder, values=list(ENCODERS), state='readonly', width=24).grid(row=3, column=1, columnspan=2, sticky='w', padx=8, pady=(10, 0))

        presets = ttk.Frame(box)
        presets.pack(fill='x')
        ttk.Label(presets, text='快捷发送：').pack(side='left')
        for label, rgb in [('红', (255, 0, 0)), ('绿', (0, 255, 0)), ('蓝', (0, 0, 255)),
                           ('白', (255, 255, 255)), ('黄', (255, 255, 0)), ('青', (0, 255, 255)), ('紫', (255, 0, 255))]:
            ttk.Button(presets, text=label, width=5, command=lambda c=rgb: self.preset(c)).pack(side='left', padx=3)

        blink = ttk.LabelFrame(box, text='灯光闪烁（与714/800kHz数据速率分开设置）', padding=12)
        blink.pack(fill='x', pady=12)
        self.blink = tk.BooleanVar(value=False)
        ttk.Checkbutton(blink, text='启用闪烁；不勾选即常亮', variable=self.blink).grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 9))
        self.frequency = tk.StringVar(value='1')
        self.duty = tk.StringVar(value='50')
        ttk.Label(blink, text='闪烁频率 (Hz)').grid(row=1, column=0, sticky='w')
        ttk.Spinbox(blink, from_=.1, to=10, increment=.1, width=8, textvariable=self.frequency).grid(row=1, column=1, padx=(8, 30))
        ttk.Label(blink, text='亮灯占比 (%)').grid(row=1, column=2)
        ttk.Spinbox(blink, from_=10, to=90, increment=5, width=8, textvariable=self.duty).grid(row=1, column=3, padx=8)
        ttk.Label(blink, text='例如1Hz、50%：亮0.5秒，灭0.5秒。参数修改后点击“应用输出”。').grid(row=2, column=0, columnspan=4, sticky='w', pady=(10, 0))

        actions = ttk.Frame(box)
        actions.pack(fill='x')
        ttk.Button(actions, text='应用输出', command=self.apply_settings).pack(side='left')
        ttk.Button(actions, text='停止并关灯', command=lambda: self.send(['LED,MODE,OFF', 'LED,OUTPUT,STATUS'])).pack(side='left', padx=8)
        ttk.Button(actions, text='恢复按键跟灯', command=lambda: self.send(['LED,SCOPE,PIN,0', 'LED,MODE,LIVE', 'LED,OUTPUT,STATUS'])).pack(side='left')
        ttk.Button(actions, text='赛博展示', command=self.show_demo).pack(side='left', padx=8)
        ttk.Button(actions, text='读取状态', command=lambda: self.send(['LED,STATUS', 'LED,OUTPUT,STATUS'])).pack(side='right')
        self.board = tk.StringVar(value='连接不会自动启用输出。快捷颜色按钮在连接后会立即应用当前闪烁设置。')
        ttk.Label(box, textvariable=self.board, wraplength=810).pack(fill='x', pady=(12, 8))
        self.log = tk.Text(box, height=9, bg='#132238', fg='#dbeafe', font=('Consolas', 9), wrap='word', state='disabled')
        self.log.pack(fill='both', expand=True)
        self.refresh_ports()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(80, self.drain)

    def preview(self, *_):
        try:
            rgb = [max(0, min(255, int(v.get()))) for v in self.rgb]
            if hasattr(self, 'swatch'):
                self.swatch.configure(bg='#%02x%02x%02x' % tuple(rgb))
        except ValueError:
            pass

    def refresh_ports(self):
        self.ports['values'] = [p.device for p in list_ports.comports()]

    def preset(self, rgb):
        for v, x in zip(self.rgb, rgb):
            v.set(str(x))
        if self.link and self.link.ready:
            self.apply_settings()

    def pick_color(self):
        selected = colorchooser.askcolor(parent=self.root, initialcolor=self.swatch['bg'])[0]
        if selected:
            self.preset(tuple(round(x) for x in selected))

    def send(self, commands):
        if self.link and self.link.ready and not self.link.closing.is_set():
            self.link.commands.put(commands)
            self.board.set('正在发送，等待板端确认…')
        else:
            messagebox.showinfo('尚未连接', '请先连接S3原生USB串口。', parent=self.root)

    def apply_settings(self):
        try:
            command = output_command(PINS[self.pin.get()], [int(x.get()) for x in self.rgb],
                                     float(self.brightness.get()), self.blink.get(),
                                     float(self.frequency.get()), float(self.duty.get()))
            timing = TIMINGS[self.timing.get()]
            encoder = ENCODERS[self.encoder.get()]
        except (ValueError, KeyError) as exc:
            messagebox.showerror('参数不正确', str(exc), parent=self.root)
            return
        self.send(['LED,TIMING,' + timing, 'LED,ENCODER,' + encoder, command, 'LED,OUTPUT,STATUS'])

    def show_demo(self):
        if self.link and self.link.ready and not self.link.demo_supported:
            messagebox.showinfo('固件版本', '赛博展示需要S3 v3.4.24或更新固件。', parent=self.root)
            return
        self.send(['LED,MODE,DEMO', 'LED,STATUS', 'LED,OUTPUT,STATUS'])

    def toggle_link(self):
        if self.link and self.link.is_alive():
            self.link.closing.set()
            self.connection.set('正在恢复默认灯效并断开…')
            return
        self.link = Link(self.port.get().strip(), self.events)
        self.connection.set('正在握手…')
        self.connect.configure(state='disabled')
        self.link.start()

    def append(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', time.strftime('%H:%M:%S ') + text + '\n')
        if int(self.log.index('end-1c').split('.')[0]) > 600:
            self.log.delete('1.0', '200.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def drain(self):
        while True:
            try:
                kind, text = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'connected':
                self.connect.configure(text='断开', state='normal')
                self.connection.set(self.port.get() + ' · 已连接')
                self.append(text)
            elif kind == 'disconnected':
                self.connect.configure(text='连接', state='normal')
                self.connection.set('未连接')
                self.append(text)
            elif kind == 'state':
                self.board.set(text)
            elif kind == 'error':
                self.append('错误：' + text)
                self.board.set('错误：' + text)
            elif kind == 'log':
                self.append(text)
        if self.quitting and (not self.link or not self.link.is_alive()):
            self.root.destroy()
            return
        self.root.after(80, self.drain)

    def close(self):
        self.quitting = True
        if self.link:
            self.link.closing.set()
        self.connection.set('正在关灯并退出…')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    root = tk.Tk()
    panel = Panel(root)
    if args.smoke_test:
        root.update()
        assert root.winfo_width() >= 800
        panel.rgb[0].set('17')
        panel.brightness.set('50')
        root.after(300, root.destroy)
    root.mainloop()


if __name__ == '__main__':
    main()
