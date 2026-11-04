import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def contract():
    configuration = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
    shortest_frame = (64 * (1 << 32)) // 263882791
    cursor = 0
    reservations = []
    for stage in configuration['frame_schedule_reservations_not_verified_rtl']:
        clocks = stage['clocks']
        assert isinstance(clocks, int) and clocks > 0
        reservations.append(dict(stage=stage['stage'], first_clock=cursor,
                                 last_clock=cursor + clocks - 1, clocks=clocks))
        cursor += clocks
    assert shortest_frame == 1041
    assert cursor == 832 and cursor < 900 < shortest_frame
    voices = configuration['planned_hardware_voices']
    assert voices == 4
    assert 64 * voices + 8 + 12 * 6 == 336
    return dict(status='design_reservation_not_cycle_verified_rtl', shortest_frame_clocks=shortest_frame,
                reserved_clocks=cursor, reserve_clocks=shortest_frame - cursor,
                software_voices_implemented=1, planned_hardware_voices=voices,
                reservations=reservations,
                delay_payload_bytes_48k=voices * 2 * 512 * 24 // 8,
                delay_payload_bytes_96k=voices * 2 * 1024 * 24 // 8,
                physical_bsram_measured=False, timing_measured=False,
                formats={
                    'waveguide_velocity': dict(signed=True, width=24, fraction_bits=20),
                    'relative_velocity': dict(signed=True, width=26, fraction_bits=20),
                    'fractional_delay': dict(signed=False, width=26, fraction_bits=16),
                    'bow_reflection': dict(signed=False, width=18, fraction_bits=18),
                    'body_state': dict(signed=True, width=32, fraction_bits=26),
                    'body_coefficient': dict(signed=True, width=24, fraction_bits=22),
                    'body_product': dict(signed=True, width=56, fraction_bits=48),
                    'body_accumulator': dict(signed=True, width=58, fraction_bits=48),
                    'audio_output': dict(signed=True, width=24, fraction_bits=23)
                })


if __name__ == '__main__':
    print(json.dumps(contract(), indent=2))
