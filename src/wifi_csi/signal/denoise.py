"""Temporal signal denoising (Butterworth lowpass and Wavelet)."""

import warnings
import numpy as np
from scipy import signal

try:
    import pywt
    HAS_PYWT = True
except ImportError:
    HAS_PYWT = False


def butterworth_lowpass_filter(
    amplitude_matrix: np.ndarray,
    sample_rate_hz: float,
    cutoff_hz: float = 3.0,
    order: int = 3,
) -> np.ndarray:
    """Apply a forward-backward low-pass Butterworth filter across time (axis 0)."""
    if not np.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
        warnings.warn("Invalid sample rate for Butterworth filtering. Returning unfiltered data.")
        return amplitude_matrix.copy()
    if amplitude_matrix.shape[0] < max(12, 3 * order):
        warnings.warn("Signal is too short for stable Butterworth filtering. Returning unfiltered data.")
        return amplitude_matrix.copy()

    nyquist_hz = 0.5 * sample_rate_hz
    safe_cutoff_hz = min(float(cutoff_hz), 0.95 * nyquist_hz)
    if safe_cutoff_hz <= 0:
        warnings.warn("Invalid Butterworth cutoff. Returning unfiltered data.")
        return amplitude_matrix.copy()

    sos = signal.butter(order, safe_cutoff_hz, btype="lowpass", fs=sample_rate_hz, output="sos")
    return signal.sosfiltfilt(sos, amplitude_matrix, axis=0)


def wavelet_denoise(
    amplitude_matrix: np.ndarray,
    wavelet: str = "db4",
    level: int | None = None,
) -> np.ndarray:
    """Apply soft-thresholding Wavelet denoising to each subcarrier time series."""
    if not HAS_PYWT:
        warnings.warn("PyWavelets (pywt) not installed. Returning unfiltered data.")
        return amplitude_matrix.copy()

    filtered = np.empty_like(amplitude_matrix)
    for col_idx in range(amplitude_matrix.shape[1]):
        col = amplitude_matrix[:, col_idx]
        max_lev = pywt.dwt_max_level(len(col), pywt.Wavelet(wavelet).dec_len)
        actual_level = min(level or 2, max_lev)
        if actual_level < 1:
            filtered[:, col_idx] = col
            continue

        coeffs = pywt.wavedec(col, wavelet, mode="symmetric", level=actual_level)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(col)))
        coeffs[1:] = [pywt.threshold(c, threshold, mode="soft") for c in coeffs[1:]]
        denoised = pywt.waverec(coeffs, wavelet, mode="symmetric")
        filtered[:, col_idx] = denoised[: len(col)]
    return filtered


def filter_amplitude_matrix(
    amplitude_matrix: np.ndarray,
    sample_rate_hz: float,
    filter_type: str = "none",
    butterworth_cutoff_hz: float = 3.0,
    butterworth_order: int = 3,
    wavelet_name: str = "db4",
    wavelet_level: int | None = None,
) -> np.ndarray:
    """Apply configured filtering (none, butterworth, or wavelet) to amplitude matrix."""
    ft = str(filter_type).strip().lower()
    if ft == "none":
        return amplitude_matrix.copy()
    elif ft == "butterworth":
        return butterworth_lowpass_filter(
            amplitude_matrix,
            sample_rate_hz=sample_rate_hz,
            cutoff_hz=butterworth_cutoff_hz,
            order=butterworth_order,
        )
    elif ft == "wavelet":
        return wavelet_denoise(
            amplitude_matrix,
            wavelet=wavelet_name,
            level=wavelet_level,
        )
    else:
        warnings.warn(f"Unknown filter_type {filter_type!r}. Returning unfiltered data.")
        return amplitude_matrix.copy()
