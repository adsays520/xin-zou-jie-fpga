#!/usr/bin/env python3
"""Generate the 0..20 fret FPGA parameter ROM and 24-bit/48 kHz dry samples.

The six supplied open-string frequencies are authoritative.  Every fretted
target is derived only as f_open * 2**(fret/12); no concert-pitch correction,
stretch tuning, or perceptual detuning is applied.

The WAV renderer is an offline extended physical model, not a claim that an
FPGA bitstream is a microphone recording.  It combines a stiff-string modal
bank, a short pick/finger contact transient, very weak fret/winding noises and
a parallel acoustic-body modal response.  There is no delay-line reverb,
algorithmic reverb, room convolution, limiting, or per-note normalization.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import signal


SAMPLE_RATE = 48_000
MAX_FRET = 20
Q15 = 1 << 15
Q23 = 1 << 23
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass(frozen=True)
class OpenString:
    number: int
    midi: int
    name: str
    frequency_hz: float
    loop_gain_q15: int
    pick_offset: int
    scrape_q15: int
    damping_q23: int
    allpass_q23: int
    init_phase_step: int
    noise_mix_q15: int
    excitation_smooth: int
    wound: bool
    decay_seconds: float
    inharmonicity: float


# String order matches the RTL: 0 is high E, 5 is low E. Frequencies, delay,
# damping and allpass values remain the supplied values. Loop gains are the
# amplitude-only sustain calibration; E2 is anchored to the measured
# -3.19 dB/s body slope in 48000_32_stereo_2.wav and the other strings retain
# the original physical ordering (plain strings decay faster than wound).
OPEN_STRINGS = (
    OpenString(1, 64, "E4", 329.63, 32687, 22, 1500, 838861, 2665197, 29620464, 22282, 0, False, 1.45, 0.00017),
    OpenString(2, 59, "B3", 246.94, 32674, 30, 1400, 1006633, 4935162, 22139007, 21627, 0, False, 1.65, 0.00013),
    OpenString(3, 55, "G3", 196.00, 32665, 49, 1000, 1090519, 1101030, 17602325, 19005, 1, False, 1.90, 0.00010),
    OpenString(4, 50, "D3", 146.83, 32657, 68, 1000, 1593836, 1373164, 13174746, 18350, 2, True, 2.35, 0.000075),
    OpenString(5, 45, "A2", 110.00, 32641, 96, 900, 1929380, 6410848, 9850842, 16384, 3, True, 2.75, 0.000055),
    OpenString(6, 40, "E2", 82.41, 32622, 128, 850, 2516582, 6154926, 7379669, 15073, 3, True, 3.20, 0.000040),
)


def note_name(midi: int) -> str:
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def target_frequency(string: OpenString, fret: int) -> float:
    if fret == 0:
        return string.frequency_hz
    return string.frequency_hz * (2.0 ** (fret / 12.0))


def filter_phase_delay(frequency_hz: float, damping: float, fraction: float) -> float:
    omega = 2.0 * math.pi * frequency_hz / SAMPLE_RATE
    z1 = complex(math.cos(omega), -math.sin(omega))
    damping_h = (1.0 - damping) + damping * z1
    fractional_h = (1.0 - fraction) + fraction * z1
    combined = damping_h * fractional_h
    return -math.atan2(combined.imag, combined.real) / omega


def solve_delay_and_fraction(frequency_hz: float, damping_q23: int) -> tuple[int, int]:
    """Tune the non-recursive two-point fractional delay at the target."""
    period = SAMPLE_RATE / frequency_hz
    damping = damping_q23 / Q23
    damping_only = filter_phase_delay(frequency_hz, damping, 1.0)
    delay_len = math.floor(period)
    if period - delay_len < damping_only:
        delay_len -= 1
    target_filter_delay = period - delay_len

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) * 0.5
        if filter_phase_delay(frequency_hz, damping, mid) > target_filter_delay:
            hi = mid
        else:
            lo = mid
    fraction_q23 = int(round(((lo + hi) * 0.5) * Q23))
    return int(delay_len), max(0, min(Q23 - 1, fraction_q23))


def fpga_parameters(string: OpenString, fret: int) -> dict[str, int | float | str | bool]:
    frequency_hz = target_frequency(string, fret)
    if fret == 0:
        damping_q23 = string.damping_q23
        # Keep the supplied open-string frequency authoritative. The legacy
        # RTL port remains named allpass_q23, but now carries the non-recursive
        # linear interpolation fraction.
        delay_len, allpass_q23 = solve_delay_and_fraction(frequency_hz, damping_q23)
        loop_gain_q15 = string.loop_gain_q15
        pick_offset = string.pick_offset
        scrape_q15 = string.scrape_q15
        init_phase_step = string.init_phase_step
        noise_mix_q15 = string.noise_mix_q15
    else:
        # A shorter fretted string is slightly stiffer and loses upper partial
        # energy faster. The allpass is solved again after this timbre change,
        # so the target fundamental remains unchanged.
        growth = 1.0 + (0.010 if not string.wound else 0.014) * fret
        damping_q23 = int(round(min(0.48, string.damping_q23 / Q23 * growth) * Q23))
        delay_len, allpass_q23 = solve_delay_and_fraction(frequency_hz, damping_q23)

        base_gain = string.loop_gain_q15 / Q15
        base_tau = -1.0 / (string.frequency_hz * math.log(base_gain))
        fret_tau = base_tau * max(0.76, 1.0 - 0.0105 * fret)
        loop_gain_q15 = min(Q15 - 1, int(round(math.exp(-1.0 / (frequency_hz * fret_tau)) * Q15)))

        # Fixed physical pick distance from the bridge, clamped only if the
        # shortened period would otherwise make the comb invalid.
        pick_offset = max(1, min(string.pick_offset, delay_len - 2, 160))
        scrape_q15 = min(4095, int(round(string.scrape_q15 * (1.0 + 0.010 * fret))))
        init_phase_step = int(round(frequency_hz * (1 << 32) / SAMPLE_RATE))
        noise_mix_q15 = min(Q15 - 1, string.noise_mix_q15 + int(round(38 * fret)))

    actual_period = delay_len + filter_phase_delay(
        frequency_hz, damping_q23 / Q23, allpass_q23 / Q23
    )
    actual_hz = SAMPLE_RATE / actual_period
    cents_error = 1200.0 * math.log2(actual_hz / frequency_hz)
    return {
        "string": string.number,
        "fret": fret,
        "note": note_name(string.midi + fret),
        "frequency_hz": frequency_hz,
        "delay_len": delay_len,
        "loop_gain_q15": loop_gain_q15,
        "pick_offset": pick_offset,
        "scrape_q15": scrape_q15,
        "damping_q23": damping_q23,
        "allpass_q23": allpass_q23,
        "init_phase_step": init_phase_step,
        "noise_mix_q15": noise_mix_q15,
        "excitation_smooth": string.excitation_smooth,
        "wound": string.wound,
        "fpga_actual_hz": actual_hz,
        "fpga_cents_error": cents_error,
    }


def render_parameter_rom(output_path: Path) -> list[dict[str, int | float | str | bool]]:
    rows = [fpga_parameters(string, fret) for string in OPEN_STRINGS for fret in range(MAX_FRET + 1)]
    lines = [
        "// Generated by scripts/generate_fret_assets.py. Do not hand-edit.",
        "// Six supplied open frequencies are preserved; frets use f0*2^(n/12).",
        "module guitar_note_params #(parameter PRECLAMPED=0) (",
        "    input wire [2:0] string_sel,",
        "    input wire [4:0] fret_sel,",
        "    output reg [9:0] delay_len,",
        "    output reg [15:0] loop_gain_q15,",
        "    output reg [9:0] pick_offset,",
        "    output reg [15:0] scrape_q15,",
        "    output reg [23:0] damping_q23,",
        "    output reg [23:0] allpass_q23,",
        "    output reg [31:0] init_phase_step,",
        "    output reg [15:0] noise_mix_q15,",
        "    output reg [1:0] excitation_smooth",
        ");",
        "    wire [4:0] safe_fret = PRECLAMPED ? fret_sel : ((fret_sel > 5'd20) ? 5'd20 : fret_sel);",
        "    always @* begin",
        "        case ({string_sel, safe_fret})",
    ]
    for row in rows:
        key = ((int(row["string"]) - 1) << 5) | int(row["fret"])
        lines.extend(
            [
                f"            8'd{key}: begin // S{row['string']} F{row['fret']} {row['note']} {row['frequency_hz']:.9f} Hz",
                f"                delay_len = 10'd{row['delay_len']}; loop_gain_q15 = 16'd{row['loop_gain_q15']};",
                f"                pick_offset = 10'd{row['pick_offset']}; scrape_q15 = 16'd{row['scrape_q15']};",
                f"                damping_q23 = 24'd{row['damping_q23']}; allpass_q23 = 24'd{row['allpass_q23']};",
                f"                init_phase_step = 32'd{row['init_phase_step']};",
                f"                noise_mix_q15 = 16'd{row['noise_mix_q15']}; excitation_smooth = 2'd{row['excitation_smooth']};",
                "            end",
            ]
        )
    # Safe default is the original low-E open string.
    default_row = fpga_parameters(OPEN_STRINGS[5], 0)
    lines.extend(
        [
            "            default: begin // S6 F0 E2",
            f"                delay_len = 10'd{default_row['delay_len']}; loop_gain_q15 = 16'd{default_row['loop_gain_q15']};",
            f"                pick_offset = 10'd{default_row['pick_offset']}; scrape_q15 = 16'd{default_row['scrape_q15']};",
            f"                damping_q23 = 24'd{default_row['damping_q23']}; allpass_q23 = 24'd{default_row['allpass_q23']};",
            f"                init_phase_step = 32'd{default_row['init_phase_step']};",
            f"                noise_mix_q15 = 16'd{default_row['noise_mix_q15']}; excitation_smooth = 2'd{default_row['excitation_smooth']};",
            "            end",
            "        endcase",
            "    end",
            "endmodule",
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return rows


def _colored_noise(rng: np.random.Generator, count: int, low: float, high: float) -> np.ndarray:
    sos = signal.butter(2, (low, high), btype="bandpass", fs=SAMPLE_RATE, output="sos")
    return signal.sosfilt(sos, rng.standard_normal(count))


def _body_response(dry: np.ndarray) -> np.ndarray:
    # Match the supplied fundamental-only project's FPGA body response.
    modes = (
        (105.0, 7.0, 0.220),
        (205.0, 9.0, 0.260),
        (315.0, 10.0, 0.180),
        (690.0, 8.0, 0.055),
        (1280.0, 7.0, 0.025),
    )
    body = 0.88 * dry
    for frequency, quality, mix in modes:
        b, a = signal.iirpeak(frequency, quality, fs=SAMPLE_RATE)
        body += mix * signal.lfilter(b, a, dry)
    # Gentle radiation shaping of an un-miked body, not mastering EQ.
    sos = signal.butter(2, 11_800, btype="lowpass", fs=SAMPLE_RATE, output="sos")
    return signal.sosfilt(sos, body)


def synthesize_note(string: OpenString, fret: int, articulation: str = "pick") -> np.ndarray:
    frequency = target_frequency(string, fret)
    duration = (5.8 if string.wound else 4.8) * (1.0 - 0.006 * fret)
    sample_count = int(round(duration * SAMPLE_RATE))
    t = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE
    rng = np.random.default_rng(0x475452 + string.number * 1009 + fret * 9176)

    length_ratio = 2.0 ** (-fret / 12.0)
    stiffness_b = string.inharmonicity / max(length_ratio * length_ratio, 0.09)
    max_harmonic = min(64 if string.wound else 52, int((SAMPLE_RATE * 0.46) / frequency))
    pick_fraction_open = string.pick_offset / (SAMPLE_RATE / string.frequency_hz)
    pick_fraction = min(0.42, pick_fraction_open / length_ratio)
    base_tau = string.decay_seconds * max(0.74, 1.0 - 0.011 * fret)

    result = np.zeros(sample_count, dtype=np.float64)
    for harmonic in range(1, max_harmonic + 1):
        partial_frequency = frequency * harmonic * math.sqrt(
            (1.0 + stiffness_b * harmonic * harmonic) / (1.0 + stiffness_b)
        )
        if partial_frequency >= SAMPLE_RATE * 0.475:
            break
        pluck_shape = math.sin(math.pi * harmonic * pick_fraction)
        spectral_power = 1.24 if not string.wound else 1.34
        amplitude = pluck_shape / (harmonic ** spectral_power)
        # Wound strings transfer proportionally more energy to the first few
        # partials; fretted notes naturally tighten through the shorter tau.
        if string.wound:
            amplitude *= 1.0 + 0.17 * math.exp(-harmonic / 5.0)
        harmonic_tau = base_tau / (1.0 + (0.018 if string.wound else 0.012) * harmonic ** 1.22)
        phase = rng.normal(0.0, 0.012 if harmonic > 1 else 0.0)
        result += amplitude * np.sin(2.0 * math.pi * partial_frequency * t + phase) * np.exp(-t / harmonic_tau)

        # Very weak close-coupled wrap mode: deterministic, aperiodic enough to
        # avoid chorus, and absent from the three plain strings.
        if string.wound and harmonic <= 18:
            detune = 1.0 + (0.00022 + 0.000015 * fret) * math.sqrt(harmonic)
            result += (
                0.030
                * amplitude
                * np.sin(2.0 * math.pi * partial_frequency * detune * t + 0.31 * harmonic)
                * np.exp(-t / (harmonic_tau * 0.62))
            )

    attack_seconds = 0.0011 if articulation == "pick" else 0.0028
    result *= 1.0 - np.exp(-t / attack_seconds)

    # Pick/finger contact and fret handling are short source events, not room
    # ambience.  Open strings intentionally contain no fret-contact noise.
    contact = _colored_noise(rng, sample_count, 850.0, 10_500.0)
    contact_tau = 0.010 if articulation == "pick" else 0.018
    contact_gain = 0.021 if articulation == "pick" else 0.010
    result += contact_gain * contact * np.exp(-t / contact_tau)

    if fret > 0:
        fret_noise = _colored_noise(rng, sample_count, 420.0, 6_800.0)
        result += (0.0022 + 0.000025 * fret) * fret_noise * np.exp(-t / 0.060)
        # A tiny pressure-dependent buzz follows the fundamental for only the
        # first part of the note and stays far below the pitched string.
        buzz_gate = np.maximum(0.0, np.sin(2.0 * math.pi * frequency * t + 0.2))
        buzz_noise = _colored_noise(rng, sample_count, 1200.0, 9000.0)
        result += 0.00075 * buzz_gate * buzz_noise * np.exp(-t / 0.16)

    if string.wound:
        winding_noise = _colored_noise(rng, sample_count, 1100.0, 7600.0)
        result += 0.0016 * winding_noise * np.exp(-t / (0.24 + 0.015 * string.number))

    result = _body_response(result)
    # One fixed library gain preserves natural level differences.  Only the
    # final 250 ms is faded to eliminate file-boundary clicks.
    result *= 0.29
    fade_count = min(int(0.25 * SAMPLE_RATE), sample_count)
    result[-fade_count:] *= np.linspace(1.0, 0.0, fade_count, endpoint=True) ** 2
    return np.clip(result, -0.999999, 0.999999)


def write_wav24(path: Path, samples: np.ndarray) -> None:
    scaled = np.rint(np.clip(samples, -1.0, 1.0 - 1.0 / Q23) * Q23).astype(np.int32)
    unsigned = scaled.astype(np.uint32)
    packed = np.empty((scaled.size, 3), dtype=np.uint8)
    packed[:, 0] = unsigned & 0xFF
    packed[:, 1] = (unsigned >> 8) & 0xFF
    packed[:, 2] = (unsigned >> 16) & 0xFF
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(3)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(packed.tobytes())


def generate_samples(output_dir: Path, rows: list[dict[str, int | float | str | bool]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, object]] = []
    for string in OPEN_STRINGS:
        for fret in range(MAX_FRET + 1):
            row = rows[(string.number - 1) * (MAX_FRET + 1) + fret]
            filename = f"S{string.number}_F{fret:02d}_{row['note'].replace('#', 's')}_{row['frequency_hz']:.6f}Hz.wav"
            samples = synthesize_note(string, fret)
            write_wav24(output_dir / filename, samples)
            peak = float(np.max(np.abs(samples)))
            tail = samples[-min(len(samples), SAMPLE_RATE // 5) :]
            manifest_rows.append(
                {
                    **row,
                    "file": filename,
                    "sample_rate": SAMPLE_RATE,
                    "bit_depth": 24,
                    "channels": 1,
                    "duration_seconds": len(samples) / SAMPLE_RATE,
                    "peak_dbfs": 20.0 * math.log10(max(peak, 1e-12)),
                    "tail_rms_dbfs": 20.0 * math.log10(max(float(np.sqrt(np.mean(tail * tail))), 1e-12)),
                    "articulation": "pick",
                    "processing": "dry instrument body modes; no room/reverb; fixed library gain",
                }
            )

    fields = list(manifest_rows[0].keys())
    with (output_dir / "manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest_rows)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def validate(rows: list[dict[str, int | float | str | bool]]) -> None:
    assert len(rows) == len(OPEN_STRINGS) * (MAX_FRET + 1)
    for string in OPEN_STRINGS:
        open_row = rows[(string.number - 1) * (MAX_FRET + 1)]
        assert open_row["frequency_hz"] == string.frequency_hz
        for fret in range(MAX_FRET + 1):
            row = rows[(string.number - 1) * (MAX_FRET + 1) + fret]
            expected = string.frequency_hz * 2.0 ** (fret / 12.0)
            assert abs(float(row["frequency_hz"]) - expected) < 1e-10
            assert abs(float(row["fpga_cents_error"])) < 0.001
            assert 16 <= int(row["delay_len"]) <= 600
            assert 0 <= int(row["allpass_q23"]) < Q23


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, default=project_root / "src" / "guitar_note_params.v")
    parser.add_argument("--samples", action="store_true", help="also render all 126 WAV files")
    parser.add_argument("--output", type=Path, default=project_root / "samples" / "phosphor_bronze_0_20")
    args = parser.parse_args()

    rows = render_parameter_rom(args.rom)
    validate(rows)
    print(f"Generated {len(rows)} FPGA note entries at {args.rom}")
    max_error = max(abs(float(row["fpga_cents_error"])) for row in rows)
    print(f"Maximum FPGA tuning error: {max_error:.9f} cents")
    if args.samples:
        generate_samples(args.output, rows)
        print(f"Generated {len(rows)} independent 24-bit/48 kHz WAV files at {args.output}")


if __name__ == "__main__":
    main()
