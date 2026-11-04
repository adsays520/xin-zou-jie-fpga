"""Periodic drawn oscillator + per-note amplitude-envelope upload protocol.

The eight tables are band-limited versions of ONE cycle, not PCM recordings.
The FPGA reuses the existing MIDI 21..108 / A4=440 key-frequency commands.
"""
from __future__ import annotations

import math

WAVE_POINTS = 1024
WAVE_BANKS = 8
ENV_POINTS = 4096
BLOCK_WORDS = 16
SAMPLE_RATE = 48000
CMD_WAVE_BEGIN, CMD_WAVE_DATA, CMD_WAVE_COMMIT = 0x20, 0x21, 0x22
CMD_DRAW_SELECT, CMD_DRAW_STEP = 0x23, 0x24
CMD_DRAW_ENV_BEGIN, CMD_DRAW_ENV_DATA, CMD_DRAW_ENV_COMMIT = 0x30, 0x31, 0x32
BANK_HIGH_KEYS = (35, 47, 59, 71, 83, 95, 107, 108)


def crc16(data: bytes | bytearray) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xFFFF
    return crc


def control_frame(command: int, value: int = 0) -> bytes:
    if command not in (CMD_WAVE_BEGIN, CMD_WAVE_COMMIT, CMD_DRAW_SELECT,
                       CMD_DRAW_STEP, CMD_DRAW_ENV_BEGIN, CMD_DRAW_ENV_COMMIT):
        raise ValueError("invalid drawn-synth control command")
    if command == CMD_DRAW_SELECT:
        if value not in (0, 1):
            raise ValueError("drawn mode must be zero or one")
        payload = (value, 0, 0)
    elif command == CMD_DRAW_STEP:
        if not 698 <= value <= 111821:
            raise ValueError("envelope step must represent 50..8000 ms")
        payload = (value >> 16, (value >> 8) & 255, value & 255)
    else:
        if value != 0:
            raise ValueError("BEGIN/COMMIT payload must be zero")
        payload = (0, 0, 0)
    frame = bytearray((0xA5, command, *payload))
    checksum = 0
    for byte in frame:
        checksum ^= byte
    return bytes(frame + bytes((checksum,)))


def data_frame(command: int, address: int, words: list[int]) -> bytes:
    limit = WAVE_POINTS * WAVE_BANKS if command == CMD_WAVE_DATA else ENV_POINTS
    if command not in (CMD_WAVE_DATA, CMD_DRAW_ENV_DATA):
        raise ValueError("invalid drawn-synth data command")
    if address < 0 or address > limit - BLOCK_WORDS or address % BLOCK_WORDS:
        raise ValueError("unaligned/out-of-range drawn-synth address")
    if len(words) != BLOCK_WORDS or any(not 0 <= w <= 65535 for w in words):
        raise ValueError("packet must contain sixteen unsigned 16-bit words")
    frame = bytearray((0xA5, command, address >> 8, address & 255))
    for word in words:
        frame.extend((word >> 8, word & 255))
    checksum = crc16(frame)
    return bytes(frame + checksum.to_bytes(2, "big"))


def envelope_step(duration_ms: float) -> int:
    if not math.isfinite(duration_ms) or not 50 <= duration_ms <= 8000:
        raise ValueError("envelope duration must be 50..8000 ms")
    frames = round(duration_ms * SAMPLE_RATE / 1000)
    return round(((ENV_POINTS - 1) << 16) / frames)


def _validate_curve(values: list[float], count: int) -> None:
    if len(values) != count or any(not math.isfinite(v) for v in values):
        raise ValueError(f"curve must contain {count} finite samples")


def prepare_wave(values: list[float]) -> list[int]:
    """DC removal, cyclic join, octave anti-aliasing, common 0.5-FS ceiling."""
    import numpy as np
    _validate_curve(values, WAVE_POINTS)
    wave = np.clip(np.array(values, dtype=float), -1.0, 1.0)
    seam = (wave[0] + wave[-1]) / 2
    for index in range(8):
        blend = index / 8
        wave[index] = seam + (wave[index] - seam) * blend
        wave[-1 - index] = seam + (wave[-1 - index] - seam) * blend
    wave -= wave.mean()
    spectrum = np.fft.rfft(wave)
    spectrum[0] = 0
    banks = []
    for highest_key in BANK_HIGH_KEYS:
        highest_hz = 440 * 2 ** ((highest_key - 69) / 12)
        max_harmonic = min(WAVE_POINTS // 2 - 1, int(0.45 * SAMPLE_RATE / highest_hz))
        bins = spectrum.copy()
        bins[max_harmonic + 1:] = 0
        banks.append(np.fft.irfft(bins, n=WAVE_POINTS))
    # A single scale across all banks preserves relative loudness; never boost
    # a high-key bank that has lost most of its harmonics into a full-scale buzz.
    maximum = max(float(np.max(np.abs(bank))) for bank in banks)
    scale = 16384 / max(1.0, maximum)
    return [int(word) & 65535 for bank in banks
            for word in np.rint(bank * scale).astype(np.int16)]


def prepare_envelope(values: list[float]) -> list[int]:
    _validate_curve(values, ENV_POINTS)
    words = [round(max(0.0, min(1.0, value)) * 32768) for value in values]
    words[0] = words[-1] = 0
    return words


def make_upload_frames(wave: list[float], envelope: list[float], duration_ms: float) -> list[bytes]:
    wave_words = prepare_wave(wave)
    env_words = prepare_envelope(envelope)
    frames = [control_frame(CMD_WAVE_BEGIN)]
    for address in range(0, len(wave_words), BLOCK_WORDS):
        frames.append(data_frame(CMD_WAVE_DATA, address, wave_words[address:address + BLOCK_WORDS]))
    frames.extend((control_frame(CMD_WAVE_COMMIT), control_frame(CMD_DRAW_ENV_BEGIN)))
    for address in range(0, ENV_POINTS, BLOCK_WORDS):
        frames.append(data_frame(CMD_DRAW_ENV_DATA, address, env_words[address:address + BLOCK_WORDS]))
    frames.extend((control_frame(CMD_DRAW_ENV_COMMIT),
                   control_frame(CMD_DRAW_STEP, envelope_step(duration_ms)),
                   control_frame(CMD_DRAW_SELECT, 1)))
    return frames


def piano_envelope() -> list[float]:
    # Time/amplitude nodes for a 1.4-second AD contour. No sustaining plateau.
    nodes = ((0, 0), (3, 1), (20, .92), (80, .72), (250, .40),
             (600, .15), (1200, .02), (1400, 0))
    values = []
    segment = 0
    for index in range(ENV_POINTS):
        t = 1400 * index / (ENV_POINTS - 1)
        while segment < len(nodes) - 2 and t > nodes[segment + 1][0]:
            segment += 1
        t0, g0 = nodes[segment]
        t1, g1 = nodes[segment + 1]
        amount = (t - t0) / (t1 - t0)
        gain = g0 * (g1 / g0) ** amount if g0 > 0 and g1 > 0 else g0 + (g1 - g0) * amount
        values.append(gain)
    values[0] = values[-1] = 0
    return values


def time_to_position(milliseconds: float, duration: float) -> float:
    """Expand the onset: first 30 ms use 30% of the envelope canvas."""
    first, second = min(30, duration * .2), min(250, duration * .6)
    t = max(0.0, min(duration, milliseconds))
    if t <= first:
        return .3 * t / first
    if t <= second:
        return .3 + .35 * (t - first) / (second - first)
    return .65 + .35 * (t - second) / (duration - second)


def position_to_time(position: float, duration: float) -> float:
    first, second = min(30, duration * .2), min(250, duration * .6)
    x = max(0.0, min(1.0, position))
    if x <= .3:
        return first * x / .3
    if x <= .65:
        return first + (second - first) * (x - .3) / .35
    return second + (duration - second) * (x - .65) / .35
