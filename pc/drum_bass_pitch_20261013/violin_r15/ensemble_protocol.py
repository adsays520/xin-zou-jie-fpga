"""Versioned opt-in multi-instrument commands. Never infer v8 from a COM name."""
import time

from melody_player import command_frame, note_frame


TARGETS = {'guitar': (0, 0x0a), 'bass': (2, 0x0b), 'piano': (1, 0x0c), 'violin': (3, 0x0d)}


def targeted_note(instrument, pitch, velocity, on):
    timbre, opcode = TARGETS[instrument]
    original = note_frame(timbre, pitch, velocity, on)
    return command_frame(opcode, *original[2:5]) if original else b''


class CapabilityProbe:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.sequence = 0
        self.invalidate()

    def invalidate(self):
        self.port = None
        self.pending = False
        self.confirmed = False
        self.flags = 0
        self.buffer = bytearray()
        self.deadline = 0
        self.confirmed_at = 0

    def begin(self, port):
        self.invalidate()
        self.sequence = (self.sequence + 1) & 255
        self.port = port
        self.pending = True
        self.deadline = self.clock() + 1.5
        return command_frame(0x0f, self.sequence, 0, 0)

    def feed(self, data, port):
        if not self.pending or port is not self.port or self.clock() > self.deadline:
            return False
        self.buffer.extend(data)
        while len(self.buffer) >= 6:
            packet = self.buffer[:6]
            checksum = 0
            for value in packet:
                checksum ^= value
            if packet[:2] == b'\xd8E' and packet[2] == self.sequence and packet[3] == 8 and packet[4] & 3 == 3 and checksum == 0:
                self.flags = packet[4]
                self.confirmed = True
                self.confirmed_at = self.clock()
                self.pending = False
                self.buffer.clear()
                return True
            del self.buffer[0]
        return False

    def usable(self, port):
        return self.confirmed and self.clock() - self.confirmed_at <= 30 and self.port is port and bool(getattr(port, 'is_open', False))
