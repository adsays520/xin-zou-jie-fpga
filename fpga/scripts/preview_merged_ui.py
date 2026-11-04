"""Render the application itself for layout review, without serial hardware."""
from pathlib import Path
import sys
import time
from unittest.mock import patch
import ctypes
from ctypes import wintypes
from PIL import Image

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'host'))
from guitar_controller import GuitarController, TIMBRE_BASS, TIMBRE_GUITAR, TIMBRE_PIANO
from test_embedded_pages import Port

out = root / 'preview'
out.mkdir(exist_ok=True)
with patch.object(GuitarController, 'refresh_ports'):
    app = GuitarController()
app.port = Port()
app.sms_loader.ready = True
app.piano_bank_progress("钢琴 DDR：参数已就绪", 100)
app.geometry('1440x930+0+0')
errors = []
app.report_callback_exception = lambda *args: errors.append(args)


def capture(name):
    for _ in range(12):
        app.update()
        time.sleep(.02)
    # Render ONLY our own Tk window. Screen grabs can capture an unrelated
    # foreground window when the test runs on a sandbox desktop.
    user, gdi = ctypes.windll.user32, ctypes.windll.gdi32
    user.GetAncestor.restype = wintypes.HWND
    user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user.GetDC.restype = wintypes.HDC
    user.GetDC.argtypes = [wintypes.HWND]
    user.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    gdi.CreateCompatibleDC.restype = wintypes.HDC
    gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi.CreateDIBSection.restype = wintypes.HBITMAP
    gdi.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                                   ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
    gdi.SelectObject.restype = wintypes.HGDIOBJ
    gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi.DeleteDC.argtypes = [wintypes.HDC]
    hwnd = user.GetAncestor(app.winfo_id(), 2)
    width, height = app.winfo_width(), app.winfo_height()
    class Header(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('width', wintypes.LONG),
                    ('height', wintypes.LONG), ('planes', wintypes.WORD),
                    ('bits', wintypes.WORD), ('compression', wintypes.DWORD),
                    ('image_size', wintypes.DWORD), ('xppm', wintypes.LONG),
                    ('yppm', wintypes.LONG), ('used', wintypes.DWORD), ('important', wintypes.DWORD)]
    class Info(ctypes.Structure):
        _fields_ = [('header', Header), ('colors', wintypes.DWORD * 3)]
    info = Info()
    info.header = Header(40, width, -height, 1, 32, 0, 0, 0, 0, 0, 0)
    hdc = user.GetDC(hwnd)
    memory = gdi.CreateCompatibleDC(hdc)
    bits = ctypes.c_void_p()
    bitmap = gdi.CreateDIBSection(hdc, ctypes.byref(info), 0, ctypes.byref(bits), None, 0)
    old = gdi.SelectObject(memory, bitmap)
    try:
        assert user.PrintWindow(hwnd, memory, 3), 'Own-window rendering failed'
        pixels = ctypes.string_at(bits, width * height * 4)
        Image.frombuffer('RGB', (width, height), pixels, 'raw', 'BGRX', 0, 1).save(out / (name + '.png'))
    finally:
        gdi.SelectObject(memory, old)
        gdi.DeleteObject(bitmap)
        gdi.DeleteDC(memory)
        user.ReleaseDC(hwnd, hdc)


try:
    app.send_timbre(3)
    app.show_page('violin')
    capture('violin_1440')
    app.geometry('980x660+0+0')
    capture('violin_980')
    app.geometry('1440x930+0+0')
    app.send_timbre(TIMBRE_PIANO)
    app.show_page('piano')
    capture('piano_sms_1440')
    app.geometry('980x660+0+0')
    capture('piano_sms_980')
    app.geometry('1440x930+0+0')
    app.send_timbre(TIMBRE_BASS)
    capture('bass_1440')
    app.send_timbre(TIMBRE_GUITAR)
    app.select_note(6, 3)
    page = app.show_page('pitch')
    page.target_fret.set(5)
    page.vibrato.set(True)
    page.toggle_vibrato()
    page.slide(1)
    capture('pitch_1440')
    app.geometry('980x660+0+0')
    capture('pitch_980')
    app.show_page('drums')
    capture('drums_980')
    assert not errors, errors
finally:
    app.close()
print('PASS: GUI render at 1440x930 and 980x660, no callback errors.')
