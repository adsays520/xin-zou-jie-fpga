import re
import time
import tkinter as tk
from tkinter import messagebox, ttk

from guitar_controller import serial, list_ports
from ui_pages import EmbeddedPage
from ui_theme import scroll_body


def trigger_command(mode):
    if mode not in ('AUTO', 'DIRECT', 'HALL'):
        raise ValueError('Invalid trigger mode')
    return f'FPGA,TRIGGER,{mode}\n'.encode('ascii')


def pick_command(string_number, velocity, fret=None):
    if type(string_number) is not int or not 1 <= string_number <= 6:
        raise ValueError('String must be 1..6')
    if type(velocity) is not int or not 1 <= velocity <= 127:
        raise ValueError('Velocity must be 1..127')
    if fret is None:
        return f'FPGA,PICK,{string_number},{velocity}\n'.encode('ascii')
    if type(fret) is not int or not 0 <= fret <= 20:
        raise ValueError('Fret must be 0..20')
    return f'FPGA,PLUCK,{string_number},{fret},{velocity}\n'.encode('ascii')


def strum_command(velocity):
    if type(velocity) is not int or not 1 <= velocity <= 127:
        raise ValueError('Velocity must be 1..127')
    return f'FPGA,STRUM,{velocity}\n'.encode('ascii')


class HallPanel(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.port = None
        self.buffer = bytearray()
        self.compatible = False
        self.strum_capable = False
        self.fpga_capable = None
        self.snapshot_capable = None
        self.fpga_online = None
        self.last_fpga_status = None
        self.next_ping = 0.0
        self.ping_attempts = 0
        self.effective_mode = None
        self.next_query = 0.0
        self.ports = {}
        self.diagnostic_status = {}
        self.status = tk.StringVar(value='未连接 S3；原音色控制串口保持独立')
        self.mode = tk.StringVar(value='板端模式：未知')
        self.sensor_state = tk.StringVar(value='ADC：未知；上电不自动发音符')
        self.snapshot_state = tk.StringVar(value='事件快照能力：未知；模式切换能力与事件绑定能力不同')
        self.mapping = tk.StringVar(value='拨杆映射未知，等待S3版本握手；只勾选实际已接通道')
        self.velocity = tk.IntVar(value=100)
        self.fret = tk.IntVar(value=0)
        self.channels = [tk.BooleanVar(value=index < 6) for index in range(7)]
        content = scroll_body(self, padding=20)
        ttk.Label(content, text='霍尔 / 拨杆测试', style='Title.TLabel').pack(anchor='w')
        ttk.Label(content, text='接 S3 原生 USB（原 COM30）；无需焊模式开关。旧 FPGA 不支持软件切换。', wraplength=900).pack(anchor='w', pady=8)
        connection = ttk.Frame(content)
        connection.pack(fill='x')
        self.port_combo = ttk.Combobox(connection, state='readonly', width=54)
        self.port_combo.pack(side='left')
        ttk.Button(connection, text='刷新', command=self.refresh_ports).pack(side='left', padx=6)
        ttk.Button(connection, text='连接 / 断开 S3', command=self.toggle_connection).pack(side='left')
        ttk.Label(content, textvariable=self.status).pack(anchor='w', pady=6)
        modes = ttk.Frame(content)
        modes.pack(fill='x', pady=6)
        for title, mode in [('跟随实体开关', 'AUTO'), ('触摸直接发声', 'DIRECT'), ('霍尔拨弦', 'HALL')]:
            ttk.Button(modes, text=title, command=lambda selected=mode: self.set_mode(selected)).pack(side='left', padx=(0, 8))
        ttk.Button(modes, text='读取状态', command=self.query).pack(side='left')
        ttk.Button(modes, text='复制诊断', command=self.copy_diagnostics).pack(side='left', padx=8)
        ttk.Button(modes, text='选择木吉他', command=lambda: self.send(b'FPGA,TIMBRE,0\n')).pack(side='left')
        ttk.Label(content, textvariable=self.mode).pack(anchor='w')
        ttk.Label(content, textvariable=self.snapshot_state, wraplength=900).pack(anchor='w')
        inputs = ttk.LabelFrame(content, text='实际接线：只勾选已接通道，修改后需重新启用', padding=8)
        inputs.pack(fill='x', pady=8)
        for channel in range(7):
            gpio = channel + 1 if channel < 2 else channel + 12
            ttk.Checkbutton(inputs, text=f'H{channel + 1} / GPIO{gpio}', variable=self.channels[channel]).pack(side='left')
        actions = ttk.Frame(content)
        actions.pack(fill='x', pady=6)
        for title, callback in [('应用通道', self.apply_mask), ('重新校准', lambda: self.send(b'HALL,CAL\n')),
                                ('启用实物拨杆', self.arm), ('停止实物触发', self.disarm)]:
            ttk.Button(actions, text=title, command=callback).pack(side='left', padx=(0, 8))
        ttk.Label(content, textvariable=self.sensor_state, wraplength=900).pack(anchor='w')
        self.readings = ttk.Treeview(content, columns=('gpio', 'raw', 'base', 'delta', 'threshold', 'valid', 'events', 'rejected', 'errors', 'quality', 'detector', 'peak'), show='headings', height=7)
        for column, title in zip(self.readings['columns'], ['通道 / 引脚', '原始值', '中点', '偏移绝对值', '触发阈值', '校准有效', '触发次数', '队列拒绝', 'ADC错误', '校准结果', '检测状态', '滤波偏移峰值']):
            self.readings.heading(column, text=title)
            self.readings.column(column, width=90, anchor='center')
        for channel in range(7):
            gpio = channel + 1 if channel < 2 else channel + 12
            self.readings.insert('', 'end', iid=str(channel + 1), values=(f'H{channel + 1}/GPIO{gpio}', *(['-'] * 11)))
        self.readings.pack(fill='x', pady=8)
        test = ttk.LabelFrame(content, text='软件测试：虚拟拨杆走 Hall 选品链路；直接试音绕过传感器', padding=8)
        test.pack(fill='x')
        ttk.Label(test, text='力度').grid(row=0, column=0)
        ttk.Spinbox(test, from_=1, to=127, textvariable=self.velocity, width=5).grid(row=0, column=1)
        ttk.Label(test, text='直接试音品位').grid(row=0, column=2)
        ttk.Spinbox(test, from_=0, to=20, textvariable=self.fret, width=5).grid(row=0, column=3)
        for column, string_number in enumerate(range(6, 0, -1)):
            ttk.Button(test, text=f'虚拟拨 {string_number} 弦', command=lambda selected=string_number: self.pick(selected)).grid(row=1, column=column, padx=4, pady=5)
            ttk.Button(test, text=f'直接试音 {string_number} 弦', command=lambda selected=string_number: self.pick(selected, direct=True)).grid(row=2, column=column, padx=4)
        ttk.Button(test, text='H1 虚拟向下扫弦', command=self.strum).grid(row=3, column=0, columnspan=2, padx=4, pady=5, sticky='ew')
        ttk.Label(content, textvariable=self.mapping, wraplength=1000).pack(anchor='w', pady=6)
        ttk.Label(content, text='阈值比较偏移，不是原始值。v3.4.4滤波后连续确认；峰值自校准后累计。噪声过大需静置重校，等待回中不会连发。', wraplength=1000).pack(anchor='w')
        self.messages = tk.Text(content, height=7, state='disabled', wrap='word')
        self.messages.pack(fill='both', expand=True)
        self.refresh_ports()
        self.after(50, self.poll)

    def log(self, message):
        self.messages.configure(state='normal')
        self.messages.insert('end', message + '\n')
        if int(self.messages.index('end-1c').split('.')[0]) > 200:
            self.messages.delete('1.0', '50.0')
        self.messages.see('end')
        self.messages.configure(state='disabled')

    def reset_diagnostics(self):
        self.diagnostic_status.clear()
        self.sensor_state.set('ADC：未知；等待本次连接的状态回复')
        for channel in self.readings.get_children():
            gpio = self.readings.item(channel, 'values')[0]
            self.readings.item(channel, values=(gpio, *(['-'] * 11)))

    def diagnostic_text(self):
        now = time.monotonic()
        lines = ['Hall诊断快照（只读，不启用触发、不发送音符）',
                 self.status.get(), self.mode.get(), self.snapshot_state.get(), self.mapping.get(),
                 '以下为各项最近接收值，并非同时采样；超过3秒标记过期。']
        for key in ('HALL,STATE', 'FPGA', *(f'HALL,{channel}' for channel in range(1, 8)),
                    *(f'HALLDIAG,{channel}' for channel in range(1, 8))):
            reading = self.diagnostic_status.get(key)
            if reading is None:
                lines.append(f'{key}: 未收到')
                continue
            received, payload = reading
            age = max(0.0, now - received)
            lines.append(f'[{age:.1f}秒前{"，已过期" if age > 3.0 else ""}] {payload}')
        lines.extend(['阈值比较 |RAW-BASE|；1Hz快照不代表瞬态峰值，VALID仅表示校准有效。',
                      'v3.4.4 RAW_PEAK/FILTERED_PEAK为校准后的累计偏移峰值；NOISE为校准稳健跨度；旧固件无HALLDIAG。',
                      'EVENTS为S3实物触发计数；ACK仅确认传输，不证明已经发声。',
                      '最近日志（可能包含之前连接；当前状态以带接收时间的快照为准）：',
                      self.messages.get('1.0', 'end').strip()])
        return '\n'.join(lines)

    def copy_diagnostics(self):
        try:
            report = self.diagnostic_text()
            self.clipboard_clear()
            self.clipboard_append(report)
        except tk.TclError as error:
            self.log(f'复制失败：{error}')
            return
        self.log('已复制诊断：包含各路采样/阈值/计数、状态接收时间和最近日志；未发送控制命令')

    def refresh_ports(self):
        available = [] if list_ports is None else list(list_ports.comports())
        self.ports = {f'{port.device} — {port.description}': port.device for port in available}
        self.port_combo['values'] = tuple(self.ports)
        if self.port_combo.get() not in self.ports:
            native = next((port.device for port in available if port.vid == 0x303a and port.pid == 0x1001), None)
            self.port_combo.set(next((label for label, device in self.ports.items() if device == native), ''))

    def toggle_connection(self):
        if self.port is not None:
            self.close()
            return
        try:
            device = self.ports.get(self.port_combo.get())
            if device is None:
                self.log('请在霍尔页选择S3原生USB串口；不是FPGA的COM11/COM13或蓝牙串口')
                return
            self.port = serial.Serial(port=None, baudrate=115200, timeout=0, write_timeout=0.2)
            self.port.dtr = False
            self.port.rts = False
            self.port.port = device
            self.port.open()
            self.compatible = False
            self.strum_capable = False
            self.mapping.set('拨杆映射未知，等待S3版本握手；只勾选实际已接通道')
            self.fpga_capable = None
            self.snapshot_capable = None
            self.fpga_online = None
            self.last_fpga_status = None
            self.effective_mode = None
            self.ping_attempts = 0
            self.next_ping = 0.0
            self.buffer.clear()
            self.reset_diagnostics()
            self.status.set(f'已连接 {device}，等待 v3.4 握手；无回复时检查是否仍是旧固件')
            self.request_handshake()
        except Exception as error:
            self.log(f'连接失败：{error}；请先关闭占用串口的监视器')
            self.close()

    def send(self, data, handshake=False, quiet=False):
        if self.port is None or not self.port.is_open:
            self.log('请先在“霍尔 / 拨杆测试”页连接S3原生USB；主界面的FPGA连接与此独立')
            return False
        if not handshake and not self.compatible:
            self.log('S3尚未握手，FPGA能力未知，不能据此判断位流版本；仅重试PING，不发演奏控制')
            self.request_handshake()
            return False
        try:
            if self.port.write(data) != len(data):
                raise IOError('控制帧发送不完整')
            if not quiet:
                self.log('发送：' + data.decode('ascii').strip())
            return True
        except Exception as error:
            self.log(f'发送失败：{error}')
            self.close()
            return False

    def request_handshake(self, now=None):
        now = time.monotonic() if now is None else now
        if self.port is None or self.compatible or now < self.next_ping:
            return
        if self.send(b'PING\n', handshake=True, quiet=self.ping_attempts != 0):
            self.ping_attempts += 1
            self.next_ping = now + (1.0 if self.ping_attempts < 5 else 5.0)
            if self.ping_attempts >= 5:
                self.status.set('USB已打开但没有版本回复；检查S3串口/固件USB控制，FPGA能力仍未知')

    def query(self, quiet=False):
        if not self.compatible:
            self.request_handshake()
            return
        self.send(b'HALL,STATUS\nFPGA,STATUS\n', quiet=quiet)

    def require_fpga(self):
        if self.port is None or not self.port.is_open or not self.compatible:
            self.send(b'FPGA,STATUS\n')
            return False
        if self.last_fpga_status is None or time.monotonic() - self.last_fpga_status > 3.0:
            self.fpga_capable = None
            self.snapshot_capable = None
            self.fpga_online = None
            self.effective_mode = None
            self.log('S3已握手，但尚未取得新鲜的FPGA状态；正在查询，不判定为旧位流')
            self.query()
            return False
        if not self.fpga_online:
            self.log('S3已握手，但SPI没有有效FPGA确认；先检查FPGA配置、SPI接线和运行状态')
            return False
        return True

    def set_mode(self, selected):
        if not self.require_fpga():
            return
        if self.fpga_capable is None:
            self.log('FPGA状态缺少TRIGGER_CAP字段，能力未知；检查S3固件版本和完整状态回复')
            return
        if self.fpga_capable is False:
            self.log('已收到FPGA在线回复，但TRIGGER_CAP=0；当前运行位流未声明软件覆盖能力，请核对实际.fs文件')
            return
        if not self.disarm():
            return
        if self.send(trigger_command(selected)):
            self.after(150, self.query)

    def apply_mask(self):
        mask = sum(1 << index for index, selected in enumerate(self.channels) if selected.get())
        if self.send(f'HALL,MASK,0x{mask:02X}\n'.encode('ascii')):
            self.after(500, self.query)

    def arm(self):
        if not self.require_fpga():
            return
        if self.effective_mode != 'PICK':
            self.log('请先切换霍尔拨弦并确认 MODE,PICK；旧位流可用SW1或临时跳线')
            return
        if not messagebox.askyesno('启用实物拨杆', '确认只勾选实际接线通道，所有ADC端电压安全、与S3共地？\n启用后重新采集128个静止样本，请勿碰拨杆。', parent=self):
            return
        self.apply_mask()
        if self.send(b'HALL,ARM,ON\n'):
            self.after(500, self.query)

    def disarm(self):
        return self.send(b'HALL,ARM,OFF\n')

    def pick(self, string_number, direct=False):
        if not direct:
            if not self.require_fpga():
                return
            if self.effective_mode != 'PICK':
                self.log('虚拟拨杆需要板端处于 PICK 模式；直接试音不受此限制')
                return
        try:
            command = pick_command(string_number, int(self.velocity.get()), int(self.fret.get()) if direct else None)
        except (ValueError, tk.TclError) as error:
            self.log(f'参数错误：{error}')
            return
        self.send(command)

    def handle_line(self, line):
        if line.startswith('PANEL,'):
            from panel_sync import decode_panel_line
            state=decode_panel_line(line)
            callback=getattr(self.controller,'apply_panel_state',None)
            if state is not None and callback is not None:callback(state)
            return
        line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        handshake = re.search(r'PONG,(R15-HALL-v3\.4(?:\.\d+)?)(?=\s|,|$)', line)
        if handshake:
            self.compatible = True
            self.panel_capable=tuple(map(int,handshake[1].split('v')[-1].split('.')))>=(3,4,6)
            self.strum_capable = tuple(map(int, handshake[1].split('v')[-1].split('.'))) >= (3, 4, 5)
            self.mapping.set('H1：6→1弦向下扫弦，沿用触发时各弦选品；H2～H7：分别拨6～1弦。H7需接线并勾选。' if self.strum_capable else
                             '旧固件：H1～H6分别拨6～1弦，H7仅测量；新扫弦映射需S3 v3.4.5。')
            self.status.set(f'{handshake[1]} 已握手；连接不自动切模式或启用实物触发')
            self.next_query = time.monotonic() + 1.0
            self.query()
        hall_state = re.search(r'HALL,STATE,ENABLED,([01]),ARMED,([01]),MASK,0x[0-9A-Fa-f]+', line)
        if hall_state:
            self.diagnostic_status['HALL,STATE'] = (time.monotonic(), hall_state[0])
            hint = '采样未启用' if hall_state[1] == '0' else (
                '实物触发已启用；仍需各路校准有效' if hall_state[2] == '1' else '仅采样，实物触发未启用')
            self.sensor_state.set(f'{hint} | {hall_state[0]}')
        reading = re.search(r'HALL,(\d),RAW,(\d+),BASE,(\d+),THRESHOLD,(\d+),VALID,(\d+),EVENTS,(\d+),REJECTED,(\d+),ERRORS,(\d+)', line)
        if reading and self.readings.exists(reading[1]):
            old = self.readings.item(reading[1], 'values')
            displacement = abs(int(reading[2]) - int(reading[3]))
            self.readings.item(reading[1], values=(old[0], reading[2], reading[3], displacement, *reading.groups()[3:], *old[9:]))
            self.diagnostic_status[f'HALL,{reading[1]}'] = (time.monotonic(), reading[0])
            return
        diagnostic = re.search(r'HALLDIAG,([1-7]),CAL,([A-Z_]+),STATE,([A-Z_]+),CAL_MIN,(\d+),CAL_MAX,(\d+),NOISE,(\d+),RAW_PEAK,(\d+),FILTERED_PEAK,(\d+)', line)
        if diagnostic and self.readings.exists(diagnostic[1]):
            quality = {'OK': '正常', 'OFF': '未选通', 'CALIBRATING': '校准中', 'RAIL': '接近电源轨',
                       'NOISY': '噪声过大', 'UNREACHABLE': '阈值不可达'}.get(diagnostic[2], diagnostic[2])
            state = {'READY': '就绪', 'CONFIRM': '确认中', 'PEAK': '测力度', 'WAIT_CENTER': '等待回中',
                     'INVALID': '禁止触发', 'CALIBRATING': '校准中', 'OFF': '未选通'}.get(diagnostic[3], diagnostic[3])
            old = self.readings.item(diagnostic[1], 'values')
            self.readings.item(diagnostic[1], values=(*old[:9], quality, state, diagnostic[8]))
            self.diagnostic_status[f'HALLDIAG,{diagnostic[1]}'] = (time.monotonic(), diagnostic[0])
            return
        fpga = re.search(r'FPGA,(ONLINE|OFFLINE),ACK,\d+,', line)
        if fpga and self.compatible:
            self.diagnostic_status['FPGA'] = (time.monotonic(), line[fpga.start():].split('\r')[0])
            self.fpga_online = fpga[1] == 'ONLINE'
            self.last_fpga_status = time.monotonic()
            capability = re.search(r',TRIGGER_CAP,([01])(?=,|\s|$)', line)
            self.fpga_capable = capability[1] == '1' if capability and self.fpga_online else None
            snapshot = re.search(r',SNAPSHOT_CAP,([01])(?=,|\s|$)', line)
            self.snapshot_capable = snapshot[1] == '1' if snapshot and self.fpga_online else None
            if self.snapshot_capable is True:
                self.snapshot_state.set('事件快照绑定可用；能力回复不代替音频与正式时序验证')
            elif self.snapshot_capable is False:
                self.snapshot_state.set('当前FPGA未报告事件快照绑定；旧Hall模式仍可测试，但并发修复需配套新位流')
            else:
                self.snapshot_state.set('事件快照能力未知：缺少新鲜字段，不认定为旧位流')
            effective = re.search(r',MODE,(PICK|DIRECT),', line)
            self.effective_mode = effective[1] if effective and self.fpga_online else None
            if not self.fpga_online:
                self.mode.set('S3已握手，FPGA的SPI链路未上线；能力未知')
            elif effective:
                self.mode.set('板端实际状态：' + line[effective.start() + 1:].split('\r')[0])
            else:
                self.mode.set('FPGA已在线，但状态缺少MODE字段；暂不允许拨杆触发')
        if any(tag in line for tag in ('HALL', 'HOST_REPLY', 'HOST_USB', 'USB control', 'FPGA,', 'ACK pick', 'NOTE_ACK', 'NOTE_KEY: DOWN')):
            self.log(line)

    def poll(self):
        if self.port is not None:
            try:
                self.buffer.extend(self.port.read(8192))
                while b'\n' in self.buffer:
                    line, _, self.buffer = self.buffer.partition(b'\n')
                    self.handle_line(line.decode('utf-8', errors='replace').strip())
                if len(self.buffer) > 8192:
                    self.buffer.clear()
                now = time.monotonic()
                if not self.compatible:
                    self.request_handshake(now)
                if self.last_fpga_status is not None and now - self.last_fpga_status > 3.0:
                    self.fpga_capable = None
                    self.snapshot_capable = None
                    self.snapshot_state.set('事件快照能力未知：FPGA状态已超时')
                    self.fpga_online = None
                    self.effective_mode = None
                    self.mode.set('FPGA状态已超时，能力未知；等待新回复')
                hall_state = self.diagnostic_status.get('HALL,STATE')
                if hall_state is not None and now - hall_state[0] > 3.0:
                    self.sensor_state.set('Hall状态已超时，是否启用未知；旧采样值不能代表当前状态')
                if self.compatible and now >= self.next_query:
                    self.next_query=now+1.0
                    if self.controller.active_page=='hall':self.query(quiet=True)
                    else:self.send(b'FPGA,STATUS\n',quiet=True)
                if self.compatible and self.fpga_online and getattr(self,'panel_capable',False) and now>=getattr(self,'next_panel_query',0):
                    self.next_panel_query=now+0.15
                    self.send(b'FPGA,PANEL\n',quiet=True)
            except Exception as error:
                self.log(f'接收失败：{error}')
                self.close()
        self.after(50, self.poll)

    def strum(self):
        if not self.require_fpga():
            return
        if not self.strum_capable:
            self.log('H1扫弦需要S3 v3.4.5；当前固件保留旧拨杆映射')
            return
        if self.effective_mode != 'PICK':
            self.log('向下扫弦需要板端处于 PICK 模式')
            return
        if self.snapshot_capable is not True:
            self.log('扫弦需要FPGA报告 SNAPSHOT_CAP,1，以锁定各弦触发时的选品')
            return
        try:
            command = strum_command(int(self.velocity.get()))
        except (ValueError, tk.TclError) as error:
            self.log(f'参数错误：{error}')
            return
        self.send(command)

    def close(self):
        if self.port is not None:
            try:
                if self.compatible:
                    self.port.write(b'HALL,ARM,OFF\n')
            except Exception:
                pass
            finally:
                try:
                    self.port.close()
                except Exception:
                    pass
        self.port = None
        self.compatible = False
        self.strum_capable = False
        self.mapping.set('拨杆映射未知，等待S3版本握手；只勾选实际已接通道')
        self.fpga_capable = None
        self.snapshot_capable = None
        self.snapshot_state.set('事件快照能力：未知；等待本次连接的状态回复')
        self.fpga_online = None
        self.last_fpga_status = None
        self.effective_mode = None
        self.reset_diagnostics()
        self.mode.set('板端模式：未知')
        self.status.set('S3 已断开；意外断线不保证板端已停用，请重新查询')
