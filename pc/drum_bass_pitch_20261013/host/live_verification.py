"""Verification wire format and analysis. No audio playback or file loading."""
import binascii
import struct
from dataclasses import dataclass
import numpy as np

MAGIC = b'\xd3\x91'
HEADER = struct.Struct('<2sBBHHHIBB')
N = 512
FS = 12000
CLOCK_HZ = 50000000
DEFAULT_FREQUENCIES = (375, 750, 1125, 1500)


def frame(command, a=0, b=0, c=0):
    values = bytes((0xA5, command, a, b, c))
    check = 0
    for value in values:
        check ^= value
    return values + bytes((check,))


def configure(frequencies, gains, pans):
    if not (len(frequencies) == len(gains) == len(pans) == 4):
        raise ValueError('必须配置四路，未启用的通路增益设为 0')
    result = [frame(0x82, 0)]
    for i, (freq, gain, pan) in enumerate(zip(frequencies, gains, pans)):
        if not isinstance(freq, int) or not 50 <= freq <= 5000:
            raise ValueError('频率必须是 50–5000 Hz 的整数')
        if not 0 <= gain <= 127 or not 0 <= pan <= 127:
            raise ValueError('音量及声像必须为 0–127')
        result.extend((frame(0x80, i, freq & 255, freq >> 8), frame(0x81, i, gain, pan)))
    result.append(frame(0x82, 1))
    return b''.join(result)


@dataclass
class Capture:
    sequence: int
    flags: int
    sample_rate: int
    latency_cycles: int
    active_count: int
    samples: np.ndarray

    @property
    def latency_ms(self):
        return self.latency_cycles * 1000 / CLOCK_HZ


def encode_capture(capture):
    samples = np.asarray(capture.samples, dtype='<i2')
    if samples.shape != (N, 2):
        raise ValueError('capture must be 512 stereo samples')
    header = HEADER.pack(MAGIC, 1, capture.flags, capture.sequence,
                         capture.sample_rate, N, capture.latency_cycles,
                         capture.active_count, 0)
    data = header + samples.tobytes()
    return data + struct.pack('>H', binascii.crc_hqx(data[2:], 0xFFFF))


class CaptureParser:
    """Bounded stream parser: handles split packets, garbage and CRC failures."""
    def __init__(self):
        self.buffer = bytearray()
        self.bad_packets = 0

    def feed(self, data):
        self.buffer.extend(data)
        result = []
        size = HEADER.size + N * 4 + 2
        while len(self.buffer) >= 2:
            start = self.buffer.find(MAGIC)
            if start < 0:
                self.buffer[:] = self.buffer[-1:] if self.buffer[-1] == MAGIC[0] else b''
                break
            if start:
                del self.buffer[:start]
            if len(self.buffer) < HEADER.size:
                break
            _, version, flags, seq, rate, count, latency, active, reserved = HEADER.unpack_from(self.buffer)
            if version != 1 or count != N or rate != FS or active > 4 or reserved != 0:
                self.bad_packets += 1
                del self.buffer[0]
                continue
            if len(self.buffer) < size:
                break
            packet = bytes(self.buffer[:size])
            if binascii.crc_hqx(packet[2:-2], 0xFFFF) != struct.unpack('>H', packet[-2:])[0]:
                self.bad_packets += 1
                del self.buffer[0]
                continue
            samples = np.frombuffer(packet[HEADER.size:-2], dtype='<i2').reshape(N, 2).copy()
            result.append(Capture(seq, flags, rate, latency, active, samples))
            del self.buffer[:size]
        return result


def spectrum(samples, sample_rate):
    # RMS combination of channel FFT magnitudes avoids opposite-phase cancellation.
    x = np.asarray(samples, dtype=float) / 32768.0
    x = x - x.mean(axis=0)
    window = np.hanning(len(x))
    amplitude = np.abs(np.fft.rfft(x * window[:, None], axis=0)) * 2 / window.sum()
    amplitude[0] *= .5
    if len(x) % 2 == 0:
        amplitude[-1] *= .5
    combined = np.sqrt((amplitude * amplitude).mean(axis=1))
    return np.fft.rfftfreq(len(x), 1.0/sample_rate), 20*np.log10(np.maximum(combined, 1e-6))


def peaks(samples, sample_rate, floor_db=-55):
    hz, db = spectrum(samples, sample_rate)
    idx = np.where((db[1:-1] > db[:-2]) & (db[1:-1] >= db[2:]) & (db[1:-1] > floor_db))[0] + 1
    # Require local prominence so DDS quantisation spurs do not masquerade as voices.
    idx = [i for i in idx if db[i] - max(db[max(0, i-3)], db[min(len(db)-1, i+3)]) > 6]
    return sorted([(float(hz[i]), float(db[i])) for i in idx], key=lambda v: v[1], reverse=True)


class PreviewSynth:
    """Numerical UI preview, never a hardware proof and never played as audio."""
    def __init__(self):
        self.phase = np.zeros(4)
        self.sequence = 0

    def capture(self, frequencies, gains, pans):
        t = np.arange(N) / FS
        left = np.zeros(N)
        right = np.zeros(N)
        for i, (f, gain, pan) in enumerate(zip(frequencies, gains, pans)):
            signal = np.sin(2*np.pi*(self.phase[i] + f*t)) * gain/128 / 4
            left += signal*(127-pan)/128
            right += signal*pan/128
            self.phase[i] = (self.phase[i] + f*N/FS) % 1
        self.sequence = (self.sequence + 1) & 65535
        samples = np.clip(np.column_stack((left, right))*32767, -32768, 32767).astype('<i2')
        return Capture(self.sequence, 1, FS, 0, sum(g > 0 for g in gains), samples)
