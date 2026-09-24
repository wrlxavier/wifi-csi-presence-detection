"""Statistical time-domain descriptors: Variance, MAD, Range, IQR."""

import numpy as np

OFFICIAL_FEATURE_NAMES = ["var", "mad", "range", "iqr"]


def mean_absolute_deviation(values: np.ndarray, axis: int = 0) -> np.ndarray:
    """Compute the mean absolute deviation around the mean along specified axis."""
    center = np.nanmean(values, axis=axis, keepdims=True)
    return np.nanmean(np.abs(values - center), axis=axis)


def make_feature_columns(n_valid_subcarriers: int) -> list[str]:
    """Create official feature column names for retained valid-subcarrier indices."""
    width = max(3, len(str(max(n_valid_subcarriers - 1, 0))))
    columns: list[str] = []
    for valid_index in range(n_valid_subcarriers):
        prefix = f"sc{valid_index:0{width}d}"
        columns.extend([f"{prefix}_{feature_name}" for feature_name in OFFICIAL_FEATURE_NAMES])
    return columns


def extract_official_features(window_amplitude: np.ndarray) -> np.ndarray:
    """Extract variance, MAD, range, and IQR for each retained subcarrier.

    Parameters
    ----------
    window_amplitude : np.ndarray
        Array of shape (n_samples, n_subcarriers).

    Returns
    -------
    np.ndarray
        Flattened 1D array of length (n_subcarriers * 4).
    """
    if window_amplitude.ndim != 2:
        raise ValueError("Window amplitude must have shape (n_samples, n_subcarriers).")
    if window_amplitude.shape[0] < 2:
        raise ValueError("At least two samples are required for feature extraction.")

    variance = np.nanvar(window_amplitude, axis=0, ddof=1)
    mad = mean_absolute_deviation(window_amplitude, axis=0)
    ptp_range = np.nanmax(window_amplitude, axis=0) - np.nanmin(window_amplitude, axis=0)
    q75 = np.nanpercentile(window_amplitude, 75, axis=0)
    q25 = np.nanpercentile(window_amplitude, 25, axis=0)
    iqr = q75 - q25

    return np.column_stack([variance, mad, ptp_range, iqr]).reshape(-1)
