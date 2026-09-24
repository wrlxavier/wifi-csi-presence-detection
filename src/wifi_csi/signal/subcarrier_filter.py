"""Detection of valid OFDM subcarriers and shared mask calculation."""

from typing import Any
import numpy as np


def detect_valid_subcarriers(
    amplitude_matrix: np.ndarray,
    threshold: float = 0.5,
) -> np.ndarray:
    """Detect valid subcarriers from mean amplitude using a configurable threshold."""
    if amplitude_matrix.ndim != 2:
        raise ValueError("Amplitude matrix must have shape (samples, subcarriers).")
    mean_amplitude = np.nanmean(amplitude_matrix, axis=0)
    return np.isfinite(mean_amplitude) & (mean_amplitude > threshold)


def compute_shared_valid_mask(
    sessions: list[dict[str, Any]],
    min_subcarriers: int = 40,
) -> np.ndarray:
    """Compute the shared valid-subcarrier mask across all sessions."""
    if not sessions:
        raise ValueError("At least one loaded session is required.")

    raw_counts = [session["amplitude_matrix"].shape[1] for session in sessions]
    if len(set(raw_counts)) != 1:
        raise ValueError(f"Sessions have inconsistent raw complex subcarrier counts: {raw_counts}")

    masks = [session["valid_mask"] for session in sessions]
    shared_mask = np.logical_and.reduce(masks)
    retained_count = int(shared_mask.sum())
    if retained_count < min_subcarriers:
        raise ValueError(
            f"The shared valid-subcarrier mask retained too few subcarriers: {retained_count}. "
            f"Minimum required is {min_subcarriers}."
        )
    return shared_mask
