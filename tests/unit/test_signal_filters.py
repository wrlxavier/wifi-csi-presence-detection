"""Unit tests for amplitude calculation, subcarrier filtering, and Butterworth denoising."""

import numpy as np
import pytest

from wifi_csi.signal.amplitudes import compute_amplitudes
from wifi_csi.signal.subcarrier_filter import detect_valid_subcarriers, compute_shared_valid_mask
from wifi_csi.signal.denoise import butterworth_lowpass_filter, filter_amplitude_matrix


def test_compute_amplitudes():
    c_arr = np.array([[3.0 + 4.0j, 0.0 + 0.0j], [1.0 + 1.0j, -5.0 + 0.0j]])
    amp = compute_amplitudes(c_arr)
    assert amp.shape == (2, 2)
    assert np.isclose(amp[0, 0], 5.0)
    assert np.isclose(amp[0, 1], 0.0)
    assert np.isclose(amp[1, 1], 5.0)


def test_detect_valid_subcarriers(synthetic_amplitude_matrix):
    valid_mask = detect_valid_subcarriers(synthetic_amplitude_matrix, threshold=0.5)
    assert len(valid_mask) == 192
    # The first 20 subcarriers were set to 0.05 < 0.5, so they must be False
    assert not np.any(valid_mask[:20])
    # The rest should be True
    assert np.all(valid_mask[20:])


def test_compute_shared_valid_mask():
    mask1 = np.array([True, True, False, True])
    mask2 = np.array([True, False, False, True])
    s1 = {"amplitude_matrix": np.ones((10, 4)), "valid_mask": mask1}
    s2 = {"amplitude_matrix": np.ones((10, 4)), "valid_mask": mask2}

    shared = compute_shared_valid_mask([s1, s2], min_subcarriers=2)
    np.testing.assert_array_equal(shared, [True, False, False, True])


def test_butterworth_lowpass_filter():
    np.random.seed(42)
    t = np.linspace(0, 10, 300)
    # Slow signal (1 Hz) + High frequency noise (10 Hz)
    sig = np.sin(2 * np.pi * 1.0 * t) + 0.5 * np.sin(2 * np.pi * 10.0 * t)
    matrix = sig[:, None]

    filtered = butterworth_lowpass_filter(matrix, sample_rate_hz=30.0, cutoff_hz=3.0, order=3)
    assert filtered.shape == matrix.shape
    # Denoised signal should have lower variance than noisy signal
    assert np.var(filtered) < np.var(matrix)
