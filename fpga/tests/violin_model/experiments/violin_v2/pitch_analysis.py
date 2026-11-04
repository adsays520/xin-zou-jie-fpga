import math

import numpy as np


def estimate_pitch(audio, sample_rate):
    centered = np.asarray(audio, dtype=np.float64) - np.mean(audio)
    if len(centered) < 8 or not np.isfinite(centered).all() or np.dot(centered, centered) < 1e-12:
        return dict(frequency=None, correlation=0.0, spectral_support=False)
    fft_size = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_size)
    correlation = np.fft.irfft(np.abs(spectrum) ** 2, fft_size)[:len(centered)]
    prefix_energy = np.concatenate(([0.0], np.cumsum(centered ** 2)))
    lags = np.arange(len(centered))
    denominator = np.sqrt(prefix_energy[len(centered) - lags] * (prefix_energy[-1] - prefix_energy[lags]))
    correlation = np.clip(correlation / np.maximum(denominator, 1e-30), -1, 1)
    minimum_lag = max(1, math.ceil(sample_rate / 16000))
    maximum_lag = min(len(centered) - 2, math.floor(sample_rate / 100))
    peaks = [index for index in range(minimum_lag, maximum_lag + 1)
             if correlation[index] > correlation[index - 1] and correlation[index] >= correlation[index + 1]]
    if not peaks:
        return dict(frequency=None, correlation=0.0, spectral_support=False)
    best = max(float(correlation[index]) for index in peaks)
    selected = next(index for index in peaks if correlation[index] >= 0.95 * best)
    left, center, right = correlation[selected - 1:selected + 2]
    denominator = left - 2 * center + right
    offset = 0.0 if abs(denominator) < 1e-15 else 0.5 * (left - right) / denominator
    coarse = sample_rate / (selected + offset)
    spectral_size = 1 << (8 * len(centered) - 1).bit_length()
    magnitudes = np.abs(np.fft.rfft(centered * np.hanning(len(centered)), spectral_size))
    lower = max(1, math.floor(coarse * 0.97 * spectral_size / sample_rate))
    upper = min(len(magnitudes) - 2, math.ceil(coarse * 1.03 * spectral_size / sample_rate))
    spectral_peaks = [index for index in range(lower, upper + 1)
                      if magnitudes[index] > magnitudes[index - 1] and magnitudes[index] >= magnitudes[index + 1]]
    if not spectral_peaks:
        return dict(frequency=coarse, coarse_frequency=coarse, correlation=float(center), spectral_support=False)
    selected_peak = max(spectral_peaks, key=lambda index: magnitudes[index])
    relative_level = float(magnitudes[selected_peak] / np.max(magnitudes))
    left, center_level, right = np.log(np.maximum(magnitudes[selected_peak - 1:selected_peak + 2], 1e-30))
    denominator = left - 2 * center_level + right
    offset = 0.0 if abs(denominator) < 1e-15 else 0.5 * (left - right) / denominator
    refined = sample_rate * (selected_peak + offset) / spectral_size
    return dict(frequency=refined, coarse_frequency=coarse, correlation=float(center),
                spectral_support=relative_level >= 0.01, fundamental_relative_level=relative_level)


def pitch_record(audio, sample_rate, target_frequency):
    result = estimate_pitch(audio, sample_rate)
    result['cents_error'] = None if result['frequency'] is None else 1200 * math.log2(result['frequency'] / target_frequency)
    result['steady_rms'] = float(np.sqrt(np.mean(np.asarray(audio) ** 2)))
    return result
