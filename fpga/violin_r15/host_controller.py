from pathlib import Path
import sys
import time
import tkinter as tk
from tkinter import ttk

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'host'))
import guitar_controller as legacy
from ui_pages import EmbeddedPage
import ui_pages
from hall_panel import HallPanel
from song_panel import SongPanel
from arrangement_panel import ArrangementPanel

TIMBRE_VIOLIN = 3


def frame(opcode, first=0, second=0, third=0):
    values = [0xA5, opcode, first, second, third]
    if any(type(value) is not int or not 0 <= value <= 255 for value in values):
        raise ValueError('Frame bytes must be integers in 0..255')
    checksum = 0
    for value in values:
        checksum ^= value
    return bytes(values + [checksum])


def violin_command(key, velocity, action):
    if type(key) is not int or not 55 <= key <= 100:
        raise ValueError('Violin range is MIDI 55..100')
    if type(velocity) is not int or not 1 <= velocity <= 127 or action not in (0, 1, 3):
        raise ValueError('Invalid violin velocity or action')
    return frame(8, key, velocity, action)


class MonoKeys:
    def __init__(self):
        self.held = {}

    def event(self, key, velocity, on, legato=True):
        violin_command(key, velocity, 1 if on else 0)
        previous = next(reversed(self.held), None)
        if on:
            self.held.pop(key, None)
            self.held[key] = velocity
            return violin_command(key, velocity, 3 if legato and previous is not None else 1)
        self.held.pop(key, None)
        if key != previous:
            return None
        if self.held:
            current = next(reversed(self.held))
            return violin_command(current, self.held[current], 3 if legato else 1)
        return violin_command(key, 1, 0)


class ViolinController(legacy.GuitarController):
    def __init__(self):
        self._panel_sync_active = False
        self._panel_state = None
        self.violin_keys = MonoKeys()
        super().__init__()
        self.title('Tang Mega R15 · 四音色演奏控制台')
        self.violin_legato = tk.BooleanVar(value=True)
        self.violin_level = tk.IntVar(value=127)
        navigation = self._nav_buttons['piano'].master
        ui_pages.PAGE_TITLES['violin'] = '独奏小提琴'
        entry = ttk.Button(navigation, text='独奏小提琴 · R15', command=self.open_violin)
        entry.pack(fill='x', pady=4)
        self._nav_buttons['violin'] = entry
        ui_pages.PAGE_TITLES['hall'] = '霍尔 / 拨杆测试'
        self.hall_panel = HallPanel(self)
        self._pages['hall'] = self.hall_panel
        hall_entry = ttk.Button(navigation, text='霍尔 / 拨杆测试', command=lambda: self.show_page('hall'))
        hall_entry.pack(fill='x', pady=4)
        self._nav_buttons['hall'] = hall_entry
        ui_pages.PAGE_TITLES['song'] = '乐曲播放'
        self.song_panel = SongPanel(self)
        self._pages['song'] = self.song_panel
        song_entry = self._nav_buttons.get('song')
        if song_entry is None:
            song_entry = ttk.Button(navigation, text='乐曲播放 · 超级马里奥', command=lambda: self.show_page('song'))
            song_entry.pack(fill='x', pady=4)
        self._nav_buttons['song'] = song_entry
        ui_pages.PAGE_TITLES['arrangement'] = '编曲工作台'
        self.arrangement_panel = ArrangementPanel(self)
        self._pages['arrangement'] = self.arrangement_panel
        arrangement_entry = self._nav_buttons.get('arrangement')
        if arrangement_entry is None:
            arrangement_entry = ttk.Button(navigation, text='编曲工作台 · 时间轴',
                                          command=lambda: self.show_page('arrangement'))
            arrangement_entry.pack(fill='x', pady=4, before=self._nav_buttons['guitar'])
        self._nav_buttons['arrangement'] = arrangement_entry
        page = EmbeddedPage(self)
        page.on_hide = self.violin_panic
        self._pages['violin'] = page
        content = ttk.Frame(page, padding=24)
        content.pack(fill='both', expand=True)
        ttk.Label(content, text='独奏小提琴 · G3–E7', style='Title.TLabel').pack(anchor='w')
        ttk.Label(content, text='96 kHz 弓弦模型 → 声体 → 抗混叠降采样 → 混音与空间效果', style='Muted.TLabel').pack(anchor='w', pady=12)
        controls = ttk.Frame(content)
        controls.pack(fill='x', pady=12)
        ttk.Checkbutton(controls, text='连弓（重叠按键不重新起弓）', variable=self.violin_legato).pack(side='left')
        ttk.Button(controls, text='停止小提琴', command=self.violin_panic).pack(side='right')
        ttk.Label(content, text='演奏力度').pack(anchor='w')
        ttk.Scale(content, from_=1, to=127, variable=self.velocity).pack(fill='x')
        ttk.Label(content, text='小提琴独立音量').pack(anchor='w', pady=(16, 0))
        level = ttk.Scale(content, from_=0, to=127, variable=self.violin_level)
        level.pack(fill='x')
        level.bind('<ButtonRelease-1>', lambda event: self.send_violin_level())
        keyboard = ttk.Frame(content)
        keyboard.pack(fill='x', pady=20)
        for offset, key in enumerate(range(55, 101)):
            button = ttk.Button(keyboard, text=legacy.midi_note_name(key), width=6)
            button.grid(row=offset // 12, column=offset % 12, padx=2, pady=5, sticky='ew')
            button.bind('<ButtonPress-1>', lambda event, note=key: self.send_piano_key_for(note, int(self.velocity.get()), True))
            button.bind('<ButtonRelease-1>', lambda event, note=key: self.send_piano_key_for(note, 1, False))
            button.bind('<Leave>', lambda event, note=key: self.release_violin_key(note))
        self.show_page('guitar')

    def apply_panel_state(self, state):
        page,motion,values=state
        self._panel_state=state
        if time.monotonic()-getattr(self,'_last_panel_host_write',0)<0.25:
            return
        def put(variable,value):
            if variable.get()!=value:variable.set(value)
        self._panel_sync_active=True
        try:
            if values[31]:
                self.timbre_text.set('板端模式：独立多乐器')
            else:
                actual=0 if values[0]<2 else values[0]-1
                self.current_timbre=actual
                self.timbre_text.set('板端音色：'+('木吉他','电吉他','钢琴','Bass','小提琴')[values[0]])
            self.current_mode=values[30]
            put(self.piano_pedal,values[19])
            put(self.violin_level,values[23])
            levels=(values[20],values[21],values[24],values[23],values[22])
            self.bus_levels[:]=levels
            mix=getattr(self,'mixer_window',None)
            if mix is not None and mix.winfo_exists():
                for i,v in enumerate(levels):
                    if mix.pending[i] is None:put(mix.levels[i],v)
            fx=getattr(self,'effects_window',None)
            if fx is not None and fx.winfo_exists() and fx._live_after is None:
                from guitar_effects import AMPS,MODS
                put(fx.amp,AMPS[values[1]]);put(fx.mod,MODS[values[6]])
                for key,i in [('drive',2),('tone',3),('level',4),('mix',5),('rate',7),('depth',8),('threshold',12)]:put(fx.vars[key],values[i])
                for key,i in [('cabinet',9),('gate',10),('compressor',11)]:put(getattr(fx,key),bool(values[i]))
            space=getattr(self,'space_effects_window',None)
            if space is not None and space.winfo_exists() and space._live_after is None:
                for key,i in [('chorus_mix',13),('chorus_rate',14),('chorus_depth',15),('delay_mix',16),('delay_time',17),('delay_feedback',18)]:put(space.vars[key],values[i])
        finally:self._panel_sync_active=False

    def write_violin(self, data):
        if len(data)>1 and data[1] in (4,0x70):self._last_panel_host_write=time.monotonic()
        if self.draw_upload_busy or self.port is None or not self.port.is_open:
            return False
        try:
            if self.port.write(data) != len(data):
                raise IOError('小提琴控制帧未完整发送')
            return True
        except Exception as error:
            self.log(f'小提琴发送失败：{error}')
            self.disconnect()
            return False

    def open_violin(self):
        if self.send_timbre(TIMBRE_VIOLIN):
            self.show_page('violin')
            self.page_title.set('演奏工作台 / 独奏小提琴')

    def send_timbre(self, timbre):
        if timbre != TIMBRE_VIOLIN:
            result = super().send_timbre(timbre)
            if result:
                self.violin_keys.held.clear()
            return result
        if not self.write_violin(frame(4, 3)):
            return False
        self.violin_keys.held.clear()
        self.stop_riff('已切换独奏小提琴')
        self.current_timbre = TIMBRE_VIOLIN
        self.timbre_text.set('音色：独奏小提琴')
        self.mode_text.set('板端模式：小提琴单声部 / 连弓或分弓')
        self.log('切换 R15 独奏小提琴；原音色停止')
        return True

    def send_piano_key_for(self, key, velocity, note_on):
        if self.current_timbre != TIMBRE_VIOLIN:
            return super().send_piano_key_for(key, velocity, note_on)
        if not 55 <= key <= 100:
            self.log('小提琴音域为 MIDI 55..100（G3–E7）')
            return False
        if self.draw_upload_busy or self.port is None or not self.port.is_open:
            return False
        data = self.violin_keys.event(key, velocity, note_on, self.violin_legato.get())
        return True if data is None else self.write_violin(data)

    def release_violin_key(self, key):
        if key in self.violin_keys.held:
            self.send_piano_key_for(key, 1, False)

    def violin_panic(self):
        if self.current_timbre == TIMBRE_VIOLIN:
            self.write_violin(frame(4, 3))
        self.violin_keys.held.clear()

    def send_violin_level(self):
        self.write_violin(frame(0x70, 3, int(self.violin_level.get())))

    def disconnect(self):
        arrangement = getattr(self, 'arrangement_panel', None)
        if arrangement is not None:
            arrangement.on_disconnect()
        song_panel = getattr(self, 'song_panel', None)
        if song_panel is not None:
            song_panel.stop('串口断开，停止曲谱')
        if getattr(self, 'current_timbre', 0) == TIMBRE_VIOLIN and self.port is not None and self.port.is_open:
            try:
                self.port.write(frame(4, 3))
            except Exception:
                pass
        self.violin_keys.held.clear()
        super().disconnect()

    def close(self):
        if not self.arrangement_panel.confirm_discard():
            return
        self.arrangement_panel.close()
        self.song_panel.stop('关闭上位机，停止曲谱')
        self.hall_panel.close()
        super().close()


def main():
    app = ViolinController()
    if '--arrangement' in sys.argv:
        app.show_page('arrangement')
    if len(sys.argv) == 3 and sys.argv[1] == '--auto-connect':
        app.after(250, lambda: app.auto_connect(sys.argv[2]))
    app.mainloop()


if __name__ == '__main__':
    main()
