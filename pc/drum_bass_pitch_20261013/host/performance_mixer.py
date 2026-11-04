"""Live three-bus mixer. The FPGA applies levels before shared effects."""
import tkinter as tk
from ui_pages import EmbeddedPage
from tkinter import ttk

BUS_NAMES = ("吉他 / Bass", "钢琴 / 手绘", "鼓机总线")
DUET_LEVELS = (72, 105, 127)


def level_frame(bus: int, value: int) -> bytes:
    if not 0 <= bus <= 2 or not 0 <= value <= 127:
        raise ValueError("bus must be 0..2 and level must be 0..127")
    data = bytes((0xA5, 0x70, bus, value, 0))
    checksum = 0
    for byte in data:
        checksum ^= byte
    return data + bytes((checksum,))


class PerformanceMixer(EmbeddedPage):
    def __init__(self, controller, parent=None, section=False):
        super().__init__(controller, parent=parent, section=section)
        self.controller = controller
        self.pending = [None] * 3
        self.levels = [tk.IntVar(value=v) for v in controller.bus_levels]
        self.status = tk.StringVar(value="拖动时实时发送到 FPGA；串口单向，无板端回读。")
        from ui_panels import mixer
        mixer(self)

    def schedule(self, bus):
        if self.pending[bus] is not None:
            self.after_cancel(self.pending[bus])
        self.pending[bus] = self.after(30, lambda b=bus: self.transmit(b))

    def transmit(self, bus):
        self.pending[bus] = None
        value = self.levels[bus].get()
        if self.controller.send_bus_level(bus, value):
            self.status.set(f"{BUS_NAMES[bus]} {value}/127 已发送（无 ACK）")
        else:
            self.status.set("未发送：请先连接串口，或等待波表上传完成。")

    def set_level(self, bus, value):
        self.levels[bus].set(value)
        self.schedule(bus)

    def preset(self, levels):
        for bus, value in enumerate(levels):
            self.set_level(bus, value)

    def close(self):
        for bus, token in enumerate(self.pending):
            if token is not None:
                self.after_cancel(token)
                self.transmit(bus)
        self.destroy()
