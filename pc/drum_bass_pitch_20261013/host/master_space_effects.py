"""Independent stereo chorus and delay for the complete instrument mix."""
from __future__ import annotations

import tkinter as tk
from ui_pages import EmbeddedPage
from tkinter import ttk

from guitar_effects import control_frame


def space_effect_frames(chorus_mix=0, chorus_rate=40, chorus_depth=40,
                        delay_mix=0, delay_time=42, delay_feedback=35):
    values = (chorus_mix, chorus_rate, chorus_depth,
              delay_mix, delay_time, delay_feedback)
    if any(type(value) is not int or not 0 <= value <= 127 for value in values):
        raise ValueError("效果参数必须为 0..127 的整数")
    if delay_feedback > 96:
        raise ValueError("延迟反馈不能超过 96")
    return [control_frame(0x60, (chorus_mix << 16) | (chorus_rate << 8) | chorus_depth),
            control_frame(0x61, (delay_mix << 16) | (delay_time << 8) | delay_feedback),
            control_frame(0x62, 0)]


class MasterSpaceEffects(EmbeddedPage):
    def __init__(self, controller, parent=None, section=False):
        super().__init__(controller, parent=parent, section=section)
        self.controller = controller
        self.vars = {key: tk.IntVar(value=value) for key, value in {
            "chorus_mix": 0, "chorus_rate": 40, "chorus_depth": 40,
            "delay_mix": 0, "delay_time": 42, "delay_feedback": 35,
        }.items()}
        self.live = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="上电默认关闭；设置对吉他、钢琴、手绘音色和鼓机同时生效。")
        self._live_after = None

        from ui_panels import space_fx
        space_fx(self)
        for variable in self.vars.values():
            variable.trace_add("write", self._schedule_live_send)

    def _schedule_live_send(self, *_args):
        if not self.live.get():
            return
        if self._live_after is not None:
            self.after_cancel(self._live_after)
        self._live_after = self.after(90, self._send_live)

    def _send_live(self):
        self._live_after = None
        if self.winfo_exists() and self.live.get():
            self.send(live=True)

    def hard_rock(self):
        for key, value in dict(chorus_mix=24, chorus_rate=30, chorus_depth=46,
                               delay_mix=38, delay_time=47, delay_feedback=36).items():
            self.vars[key].set(value)

    def off(self):
        self.vars["chorus_mix"].set(0)
        self.vars["delay_mix"].set(0)
        self.send()

    def send(self, live=False):
        values = {key: int(variable.get()) for key, variable in self.vars.items()}
        ok = self.controller.send_master_effects(space_effect_frames(**values))
        self.status.set(("实时设置" if live else "设置") + "已发送（单向串口，无板端 ACK）。" if ok
                        else "未完成发送，请检查连接 / 上传状态。")

    def close(self):
        if self._live_after is not None:
            self.after_cancel(self._live_after)
        self.destroy()
