import argparse
import json
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'drum_bass_pitch_20261013'
sys.path[:0] = [str(BASE / 'violin_r15'), str(BASE / 'host'), str(BASE / 'tools/python_deps')]
from arrangement_model import Project
from arrangement_playback import compile_plan
from host_controller import ViolinController
import ui_pages
from ui_pages import EmbeddedPage


def read_catalog():
    catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    if catalog.get('format') != 'tang-demo-library-v1':
        raise ValueError('不支持的曲库格式')
    songs = catalog['songs']
    if not songs or len({song['id'] for song in songs}) != len(songs):
        raise ValueError('曲库为空或曲目ID重复')
    for song in songs:
        for variant in ('full', 'short'):
            project_path(song, variant)
    return songs


def project_path(song, variant):
    if variant not in ('full', 'short'):
        raise ValueError('版本只能是完整版或短试听')
    path = (ROOT / song[variant]).resolve()
    if path.parent != (ROOT / 'projects').resolve() or not path.name.endswith('.tang.json'):
        raise ValueError('Demo路径必须在曲库projects目录内')
    if not path.is_file():
        raise ValueError('Demo文件不存在：' + str(path))
    return path


def load_song(app, identifier, variant='full'):
    song = next((item for item in read_catalog() if item['id'] == identifier), None)
    if song is None:
        raise ValueError('未知Demo：' + identifier)
    project = Project.load(project_path(song, variant))
    compile_plan(project, hardware=True, ensemble=True)
    panel = app.arrangement_panel
    if not panel.confirm_discard():
        return False
    panel._replace(project)
    panel.ensemble.set(True)
    panel.hardware.set(False)
    panel.loop.set(False)
    app.show_page('arrangement')
    panel.status.set(song.get('mix_note', '已载入低音量Demo副本（总线及音量自动化为原来的50%）；未自动连接或播放。') +
                     ' 实机发声请连接FPGA UART、探测能力后勾选发送到FPGA。')
    return True


class DemoLibrary(EmbeddedPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.songs = {song['id']: song for song in read_catalog()}
        content = ttk.Frame(self, padding=22)
        content.pack(fill='both', expand=True)
        ttk.Label(content, text='音乐Demo曲库 · 原创与用户谱改编', style='Title.TLabel').pack(anchor='w')
        ttk.Label(content, text=f'{len(self.songs)}个Demo；新增《Time Machine》：透亮钢琴与干净木吉他双奏。也可从音游页选曲生成节奏谱面；旧曲目保留。',
                  style='Muted.TLabel', wraplength=1000).pack(anchor='w', pady=(8, 14))
        table = ttk.Frame(content)
        table.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(table, columns=('genre', 'bpm', 'duration'), selectmode='browse', height=10)
        self.tree.heading('#0', text='曲目')
        self.tree.column('#0', width=200, minwidth=140)
        for column, title, width in (('genre', '编曲风格', 280), ('bpm', 'BPM', 70), ('duration', '完整 / 短版', 130)):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, minwidth=60)
        scroll = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        for identifier, song in self.songs.items():
            self.tree.insert('', 'end', iid=identifier, text=song['title'],
                values=(song['genre'], song['bpm'], f'{song["duration_seconds"]:.1f}s / {song["short_seconds"]:.1f}s'))
        self.description = tk.StringVar()
        ttk.Label(content, textvariable=self.description, wraplength=920, justify='left').pack(fill='x', pady=14)
        controls = ttk.Frame(content)
        controls.pack(fill='x')
        ttk.Button(controls, text='打开完整版', command=lambda: self.open_selected('full')).pack(side='left')
        ttk.Button(controls, text='打开8小节短试听', command=lambda: self.open_selected('short')).pack(side='left', padx=10)
        ttk.Label(content, text='打开的是可编辑副本；保存时另存，不覆盖曲库。双击曲目打开完整版。',
                  style='Muted.TLabel').pack(anchor='w', pady=(14, 6))
        ttk.Label(content, text='音频由FPGA输出；静音走带不会在电脑合成音频。打开曲目不会自动连接、发声或烧录。',
                  style='Muted.TLabel', wraplength=1000).pack(anchor='w')
        self.status = tk.StringVar(value='实机需配套已通过时序的v10位流；“探测v8能力”是协议名称，不是让你换回旧位流。')
        ttk.Label(content, textvariable=self.status, wraplength=1000).pack(anchor='w', pady=10)
        self.tree.bind('<<TreeviewSelect>>', lambda event: self.describe())
        self.tree.bind('<Double-1>', lambda event: self.open_selected('full'))
        self.tree.selection_set(next(iter(self.songs)))
        self.describe()

    def describe(self):
        selection = self.tree.selection()
        if selection:
            song = self.songs[selection[0]]
            self.description.set(f'{song["title"]}  |  {song["key"]}  |  {song["bars"]}小节\n{song["description"]}')

    def open_selected(self, variant):
        selection = self.tree.selection()
        if not selection:
            return
        try:
            load_song(self.controller, selection[0], variant)
        except (ValueError, OSError, KeyError) as error:
            self.status.set('打开失败：' + str(error))


def attach_library(app):
    ui_pages.PAGE_TITLES['demos'] = '音乐Demo曲库'
    app.demo_library = DemoLibrary(app)
    app._pages['demos'] = app.demo_library
    navigation = app._nav_buttons['arrangement'].master
    entry = app._nav_buttons.get('demos')
    if entry is None:
        entry = ttk.Button(navigation)
        entry.pack(fill='x', pady=4, before=app._nav_buttons['arrangement'])
    entry.configure(text='音乐Demo曲库', command=lambda: app.show_page('demos'))
    app._nav_buttons['demos'] = entry
    app.show_page('demos')
    return app.demo_library


def main():
    parser = argparse.ArgumentParser(description='Tang Mega音乐Demo曲库；不会自动连接或播放')
    parser.add_argument('--song', choices=[song['id'] for song in read_catalog()])
    parser.add_argument('--short', action='store_true')
    arguments = parser.parse_args()
    app = ViolinController()
    app.title('Tang Mega · 音乐Demo曲库 / 吉他与鼓组')
    attach_library(app)
    if arguments.song:
        load_song(app, arguments.song, 'short' if arguments.short else 'full')
    app.mainloop()


if __name__ == '__main__':
    main()
