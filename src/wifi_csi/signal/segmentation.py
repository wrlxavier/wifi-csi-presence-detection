"""Segmentation of continuous CSI time series into windows."""

from typing import Any
import warnings
import numpy as np
import pandas as pd


def select_active_interval(
    session: dict[str, Any],
    fallback: str = "full",
    fallback_trim_seconds: float = 0.0,
) -> tuple[pd.Series, np.ndarray, dict[str, Any]]:
    """Select active condition interval for a session with metadata or fallback."""
    timestamps = session["timestamps"].reset_index(drop=True)
    amplitude_matrix = session["amplitude_matrix"]
    start = session.get("active_start")
    end = session.get("active_end")

    if start is not None and end is not None:
        mask = timestamps.ge(start) & timestamps.le(end)
        if mask.any():
            details = {
                "active_interval_source": "metadata_t1_t2",
                "active_rows": int(mask.sum()),
                "active_start_used": str(start),
                "active_end_used": str(end),
            }
            return (
                timestamps.loc[mask].reset_index(drop=True),
                amplitude_matrix[mask.to_numpy()],
                details,
            )
        warnings.warn(
            f"Metadata active interval selected no samples for {session['session_id']}. "
            "Using fallback."
        )

    if fallback == "full":
        if fallback_trim_seconds > 0 and len(timestamps) > 1:
            t_min = timestamps.iloc[0] + pd.Timedelta(seconds=fallback_trim_seconds)
            t_max = timestamps.iloc[-1] - pd.Timedelta(seconds=fallback_trim_seconds)
            mask = timestamps.ge(t_min) & timestamps.le(t_max)
            source_name = f"full_trimmed_{fallback_trim_seconds}s"
        else:
            mask = pd.Series(True, index=timestamps.index)
            source_name = "full_untrimmed"

        details = {
            "active_interval_source": source_name,
            "active_rows": int(mask.sum()),
            "active_start_used": str(timestamps.loc[mask].iloc[0]) if mask.any() else None,
            "active_end_used": str(timestamps.loc[mask].iloc[-1]) if mask.any() else None,
        }
        return (
            timestamps.loc[mask].reset_index(drop=True),
            amplitude_matrix[mask.to_numpy()],
            details,
        )

    raise ValueError(f"Unsupported active interval fallback: {fallback}")


def segment_non_overlapping_windows(
    timestamps: pd.Series,
    amplitude_matrix: np.ndarray,
    window_seconds: float = 2.0,
    session_effective_rate_hz: float = 29.0,
    session_info: dict[str, Any] | None = None,
    min_absolute_samples: int = 5,
    min_rate_fraction: float = 0.5,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Segment active samples into non-overlapping time-based windows."""
    if len(timestamps) != amplitude_matrix.shape[0]:
        raise ValueError("Timestamp count must match amplitude rows.")
    if len(timestamps) == 0:
        return [], {"candidate_windows": 0, "dropped_windows": 0, "windows_kept": 0}

    window_delta = pd.Timedelta(seconds=float(window_seconds))
    min_samples = (
        max(
            min_absolute_samples,
            int(min_rate_fraction * session_effective_rate_hz * window_seconds),
        )
        if np.isfinite(session_effective_rate_hz)
        else min_absolute_samples
    )
    recording_start = timestamps.iloc[0]
    recording_end = timestamps.iloc[-1]

    windows: list[dict[str, Any]] = []
    window_start = recording_start
    window_index = 0
    candidate_count = 0
    dropped_count = 0

    while window_start + window_delta <= recording_end:
        candidate_count += 1
        window_end = window_start + window_delta
        mask = timestamps.ge(window_start) & timestamps.lt(window_end)
        sample_indices = np.where(mask.to_numpy())[0]

        if len(sample_indices) < min_samples:
            dropped_count += 1
            window_start = window_end
            continue

        window_timestamps = timestamps.iloc[sample_indices]
        window_duration_s = (window_timestamps.iloc[-1] - window_timestamps.iloc[0]).total_seconds()
        rate_window = (
            float((len(window_timestamps) - 1) / window_duration_s)
            if window_duration_s > 0
            else np.nan
        )

        item = {
            "window_index": window_index,
            "window_start_time": str(window_start),
            "window_end_time": str(window_end),
            "n_samples": int(len(sample_indices)),
            "effective_rate_hz_window": rate_window,
            "amplitude": amplitude_matrix[sample_indices],
        }
        if session_info:
            item.update(session_info)

        windows.append(item)
        window_index += 1
        window_start = window_end

    details = {
        "candidate_windows": candidate_count,
        "dropped_windows": dropped_count,
        "windows_kept": len(windows),
    }
    return windows, details
