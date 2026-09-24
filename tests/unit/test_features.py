"""Unit tests for statistical feature extraction (Variance, MAD, Range, IQR)."""

import numpy as np
import pytest

from wifi_csi.features.statistical import (
    mean_absolute_deviation,
    extract_official_features,
    make_feature_columns,
)


def test_mean_absolute_deviation():
    vec = np.array([[10.0], [20.0], [30.0]])  # mean is 20, deviations: 10, 0, 10 -> MAD = 20/3
    mad = mean_absolute_deviation(vec, axis=0)
    assert np.isclose(mad[0], 20.0 / 3.0)


def test_make_feature_columns():
    cols = make_feature_columns(n_valid_subcarriers=2)
    expected = [
        "sc000_var", "sc000_mad", "sc000_range", "sc000_iqr",
        "sc001_var", "sc001_mad", "sc001_range", "sc001_iqr",
    ]
    assert cols == expected


def test_extract_official_features(synthetic_window):
    features = extract_official_features(synthetic_window)
    # Shape of synthetic_window is (58, 162)
    # 162 subcarriers * 4 descriptors = 648 features
    assert len(features) == 648
    assert np.all(np.isfinite(features))
    assert np.all(features >= 0.0)  # Variance, MAD, range, and IQR are strictly non-negative
