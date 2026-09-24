"""Dataset assembly and feature extraction pipeline orchestrator."""

from typing import Any
import numpy as np
import pandas as pd

from wifi_csi.core.constants import METADATA_COLS
from wifi_csi.features.statistical import (
    extract_official_features,
    make_feature_columns,
)
from wifi_csi.signal.denoise import filter_amplitude_matrix
from wifi_csi.signal.segmentation import (
    select_active_interval,
    segment_non_overlapping_windows,
)


def build_feature_dataset(
    sessions: list[dict[str, Any]],
    shared_mask: np.ndarray,
    window_seconds: float = 2.0,
    filter_type: str = "none",
    butterworth_cutoff_hz: float = 3.0,
    butterworth_order: int = 3,
    wavelet_name: str = "db4",
    wavelet_level: int | None = None,
    min_absolute_samples: int = 5,
    min_rate_fraction: float = 0.5,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, Any]]]:
    """Build official feature dataset from loaded sessions across all campaigns."""
    rows: list[dict[str, Any]] = []
    processing_details: dict[str, dict[str, Any]] = {}

    n_valid = int(shared_mask.sum())
    feature_columns = make_feature_columns(n_valid)
    all_columns = METADATA_COLS + feature_columns

    for session in sessions:
        active_timestamps, active_amplitude, active_details = select_active_interval(session)
        valid_amplitude = active_amplitude[:, shared_mask]
        filtered_amplitude = filter_amplitude_matrix(
            valid_amplitude,
            sample_rate_hz=session["median_rate_hz"],
            filter_type=filter_type,
            butterworth_cutoff_hz=butterworth_cutoff_hz,
            butterworth_order=butterworth_order,
            wavelet_name=wavelet_name,
            wavelet_level=wavelet_level,
        )

        session_info = {
            "session_id": session["session_id"],
            "source_csv": session["csv_path"].name,
            "label_name": session["label_name"],
            "label": session["label"],
        }
        windows, window_details = segment_non_overlapping_windows(
            timestamps=active_timestamps,
            amplitude_matrix=filtered_amplitude,
            window_seconds=window_seconds,
            session_effective_rate_hz=session["effective_rate_hz"],
            session_info=session_info,
            min_absolute_samples=min_absolute_samples,
            min_rate_fraction=min_rate_fraction,
        )

        combined_details = {**active_details, **window_details}
        processing_details[session["session_id"]] = combined_details

        for window in windows:
            feat_values = extract_official_features(window["amplitude"])
            row_dict = {
                "session_id": window["session_id"],
                "source_csv": window["source_csv"],
                "label_name": window["label_name"],
                "label": window["label"],
                "window_index": window["window_index"],
                "window_start_time": window["window_start_time"],
                "window_end_time": window["window_end_time"],
                "n_samples": window["n_samples"],
                "effective_rate_hz_window": window["effective_rate_hz_window"],
            }
            row_dict.update(dict(zip(feature_columns, feat_values)))
            rows.append(row_dict)

    n_valid = int(shared_mask.sum())
    feature_columns = make_feature_columns(n_valid)
    all_columns = METADATA_COLS + feature_columns

    features_df = pd.DataFrame(rows, columns=all_columns)

    valid_subcarrier_indices = np.where(shared_mask)[0]
    mapping_rows = [
        {
            "valid_subcarrier_index": valid_index,
            "raw_complex_subcarrier_index": int(raw_index),
            "prefix": f"sc{valid_index:0{max(3, len(str(max(n_valid - 1, 0))))}d}",
        }
        for valid_index, raw_index in enumerate(valid_subcarrier_indices)
    ]
    mapping_df = pd.DataFrame.from_records(mapping_rows)

    return features_df, mapping_df, processing_details
