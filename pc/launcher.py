"""Portable complete desktop entry; editable application files remain beside EXE."""
import argparse
import json
from pathlib import Path
import sys
import traceback

import numpy
import numpy.fft
import serial
import serial.tools.list_ports
import tkinter
import tkinter.ttk
import tkinter.font
import tkinter.filedialog
import tkinter.colorchooser
import tkinter.messagebox


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('main', 'arrangement', 'rhythm', 'demo', 'midi', 'led'), default='main')
    parser.add_argument('--smoke-test', action='store_true')
    parser.add_argument('--smoke-report')
    args = parser.parse_args()
    root = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    project = root / 'drum_bass_pitch_20261013'
    sys.path[:0] = [str(project / 'violin_r15'), str(project / 'host'), str(root / 'Music_Demos'), str(root / 'tools')]
    if args.mode == 'led':
        import led_debug_panel
        window = tkinter.Tk()
        panel = led_debug_panel.Panel(window)
        if args.smoke_test:
            window.update()
            assert panel.link is None
            window.destroy()
            Path(args.smoke_report or root / 'led_startup_check.json').write_text(json.dumps(dict(
                passed=True, frozen=bool(getattr(sys, 'frozen', False)), mode='led', hardware_connected=False,
                firmware_written=False, resource_root=str(root)), indent=2), encoding='utf8')
        else:
            window.mainloop()
        return
    import host_controller
    import rhythm_panel
    import demo_library
    import midi_guide
    from arrangement_model import Project
    from arrangement_playback import compile_plan
    assert Path(rhythm_panel.ROOT).resolve() == root
    modules = (host_controller, host_controller.legacy, rhythm_panel, demo_library, midi_guide)
    for module in modules:
        if not Path(module.__file__).resolve().is_relative_to(root):
            raise RuntimeError('Module loaded outside portable tree: ' + module.__name__)
    app = host_controller.ViolinController()
    demo_library.attach_library(app)
    app.title('Tang Mega · FPGA / ESP 完整控制台 2026.11.04')
    pages = ('guitar', 'piano', 'drums', 'pitch', 'effects', 'mix', 'verify', 'violin',
             'hall', 'song', 'arrangement', 'rhythm', 'midi_guide', 'demos')
    if args.smoke_test:
        for page in pages:
            app.show_page(page)
            app.update()
            assert page in app._pages, page
        songs = demo_library.read_catalog()
        compiled = 0
        for song in songs:
            for variant in ('full', 'short'):
                compile_plan(Project.load(demo_library.project_path(song, variant)), hardware=True, ensemble=True)
                compiled += 1
        midi_files = list((root / 'Music_Demos').glob('MIDI_*/*.mid'))
        midi_notes = 0
        for path in midi_files:
            score = midi_guide.read_midi(path)
            midi_notes += len(score.notes)
        assert app.port is None and app.hall_panel.port is None
        app.destroy()
        report = dict(passed=True, pages_checked=list(pages), catalog_songs=len(songs),
                      projects_loaded_and_compiled=compiled, midi_files_loaded=len(midi_files),
                      midi_notes=midi_notes, frozen=bool(getattr(sys, 'frozen', False)),
                      resource_root=str(root), module_paths={m.__name__: m.__file__ for m in modules},
                      hardware_connected=False, firmware_written=False)
        Path(args.smoke_report or root / 'startup_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
        return
    app.show_page(dict(main='guitar', arrangement='arrangement', rhythm='rhythm', demo='demos', midi='midi_guide')[args.mode])
    app.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        detail = traceback.format_exc()
        base = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
        (base / 'startup_error.log').write_text(detail, encoding='utf8')
        if '--smoke-test' not in sys.argv:
            window = tkinter.Tk()
            window.withdraw()
            tkinter.messagebox.showerror('启动失败', detail[-1200:])
            window.destroy()
        sys.exit(1)
