"""Use the existing V14 envelope RAM protocol for per-voice short tails."""
import math

from guitar_controller import (CMD_ENV_BEGIN, CMD_ENV_COMMIT, CMD_ENV_SELECT,
                               make_envelope_control, make_envelope_data, riff_tail_ms)
from melody_player import command_frame


def short_envelope_words(sustain):
    if type(sustain) is not int or not 0 <= sustain < 127:
        raise ValueError('短延音必须为0..126；127使用原自然包络')
    tail = riff_tail_ms(3, sustain) / 1000
    values = []
    for index in range(4096):
        # Match V14 custom RAM addressing: age * 3994 >> 16 at 48kHz.
        seconds = index * 65536 / (3994 * 48000)
        if seconds >= tail:
            gain = 0
        elif seconds < 0.004:
            gain = seconds / 0.004
        elif seconds < 0.065:
            gain = 1 - 0.28 * (seconds - 0.004) / 0.061
        else:
            amount = (seconds - 0.065) / (tail - 0.065)
            gain = 0.72 * math.cos(amount * math.pi / 2) ** 2
        values.append(round(gain * 32768))
    values[0] = values[-1] = 0
    return tuple(values)


def envelope_preparation(sustain, ensemble=False):
    words = short_envelope_words(sustain)
    # Clear the old voices and wait for the envelope-write guard to become idle.
    result = [(command_frame(3, 1, 0, 0) + command_frame(4, 0, 0, 0) +
               make_envelope_control(CMD_ENV_SELECT, 0) +
               (command_frame(0x0e, 1, 0, 0) if ensemble else b''), 80),
              (make_envelope_control(CMD_ENV_BEGIN), 5)]
    result.extend((make_envelope_data(address, words[address:address + 16]), 5)
                  for address in range(0, 4096, 16))
    result.extend(((make_envelope_control(CMD_ENV_COMMIT), 10),
                   (make_envelope_control(CMD_ENV_SELECT, 1), 10)))
    return tuple(result)
