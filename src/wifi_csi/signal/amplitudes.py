"""Functions for converting complex CSI vectors to amplitudes and loading session data."""

from pathlib import Path
from typing import Any
import warnings
import numpy as np
import pandas as pd

from wifi_csi.core.constants import DEFAULT_LABEL_MAP
from wifi_csi.parsing.csi_decoder import (
    parse_csi_array,
    raw_iq_to_complex,
    parse_host_timestamp,
)
from wifi_csi.parsing.metadata_parser import (
    load_metadata,
    infer_label_from_metadata_or_filename,
    metadata_validation_details,
    get_active_interval_from_metadata,
)
from wifi_csi.signal.subcarrier_filter import detect_valid_subcarriers


def compute_amplitudes(complex_matrix: np.ndarray) -> np.ndarray:
    """Compute Euclidean amplitude matrix |h| = sqrt(I^2 + Q^2)."""
    return np.abs(complex_matrix)


def _series_or_empty_numeric(df: pd.DataFrame, column: str) -> np.ndarray | None:
    """Return numeric column as a NumPy array when present."""
    if column not in df.columns:
        return None
    return pd.to_numeric(df[column], errors="coerce").to_numpy(dtype=np.float64)


def _safe_mode_int(values: pd.Series) -> int | None:
    """Return the most common integer value in a series, or None when unavailable."""
    numeric = pd.to_numeric(values, errors="coerce").dropna().astype(int)
    if numeric.empty:
        return None
    return int(numeric.mode().iloc[0])


def _rssi_summary(rssi: np.ndarray | None) -> dict[str, float | None]:
    """Summarize RSSI values when present."""
    if rssi is None or len(rssi) == 0 or np.all(np.isnan(rssi)):
        return {"mean": None, "std": None, "min": None, "max": None}
    return {
        "mean": float(np.nanmean(rssi)),
        "std": float(np.nanstd(rssi)),
        "min": float(np.nanmin(rssi)),
        "max": float(np.nanmax(rssi)),
    }


def load_session_arrays(
    csv_path: str | Path,
    meta_path: str | Path | None = None,
    required_status: str = "VALID",
    label_map: dict[str, int] | None = None,
    amp_threshold: float = 0.5,
) -> dict[str, Any]:
    """Load, validate, and convert one CSI CSV session into arrays and metrics."""
    csv_path = Path(csv_path)
    meta = load_metadata(meta_path)
    metadata_status, invalidation_reason, is_metadata_valid = metadata_validation_details(
        meta, required_status=required_status
    )
    if not is_metadata_valid:
        raise ValueError(
            f"{csv_path.name} has metadata timing.status={metadata_status!r}; "
            f"only {required_status!r} sessions are allowed. "
            f"Invalidation reason: {invalidation_reason or 'not provided'}"
        )

    mapping = label_map or DEFAULT_LABEL_MAP
    label_name = infer_label_from_metadata_or_filename(meta, csv_path, label_map=mapping)
    if label_name not in mapping:
        warnings.warn(
            f"Label {label_name!r} for {csv_path.name} is not in label_map. "
            "Add an explicit mapping before using this session."
        )
        label_value = None
    else:
        label_value = mapping[label_name]

    df_raw = pd.read_csv(csv_path)
    raw_rows = int(len(df_raw))
    df = df_raw.copy()

    if "type" in df.columns:
        df = df.loc[df["type"].astype(str).eq("CSI_DATA")].copy()
    csi_rows = int(len(df))

    if "timestamp_host" not in df.columns:
        raise ValueError(f"{csv_path.name} is missing required column: timestamp_host")
    if "data" not in df.columns:
        raise ValueError(f"{csv_path.name} is missing required column: data")

    df["timestamp_host_parsed"] = df["timestamp_host"].map(parse_host_timestamp)
    invalid_timestamp_mask = df["timestamp_host_parsed"].isna()
    invalid_timestamp_rows = int(invalid_timestamp_mask.sum())
    df = df.loc[~invalid_timestamp_mask].copy()

    parsed_arrays = df["data"].map(parse_csi_array)
    parse_error_mask = parsed_arrays.isna()
    parse_error_rows = int(parse_error_mask.sum())
    df = df.loc[~parse_error_mask].copy()
    parsed_arrays = parsed_arrays.loc[~parse_error_mask]
    df["parsed_csi"] = parsed_arrays

    if df.empty:
        raise ValueError(f"{csv_path.name} has no valid CSI rows after timestamp and data parsing.")

    raw_lengths = df["parsed_csi"].map(len)
    expected_len_from_column = _safe_mode_int(df["len"]) if "len" in df.columns else None
    expected_raw_length = expected_len_from_column or int(raw_lengths.mode().iloc[0])
    if expected_raw_length % 2 != 0:
        raise ValueError(
            f"{csv_path.name} has odd expected raw CSI vector length {expected_raw_length}."
        )

    length_mismatch_mask = raw_lengths.ne(expected_raw_length)
    if "len" in df.columns:
        len_column = pd.to_numeric(df["len"], errors="coerce")
        length_mismatch_mask = length_mismatch_mask | len_column.ne(expected_raw_length)
    length_mismatch_rows = int(length_mismatch_mask.sum())

    df = df.loc[~length_mismatch_mask].copy()
    if df.empty:
        raise ValueError(f"{csv_path.name} has no valid CSI rows after length validation.")

    df = df.sort_values("timestamp_host_parsed").reset_index(drop=True)

    raw_matrix = np.vstack(df["parsed_csi"].to_numpy())
    complex_matrix = np.vstack([raw_iq_to_complex(row) for row in raw_matrix])
    amplitude_matrix = compute_amplitudes(complex_matrix)

    timestamps = pd.to_datetime(df["timestamp_host_parsed"]).reset_index(drop=True)
    time_diffs_s = timestamps.diff().dt.total_seconds().dropna()
    positive_diffs_s = time_diffs_s[time_diffs_s > 0]

    duration_s = (
        float((timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds())
        if len(timestamps) > 1
        else 0.0
    )
    effective_rate_hz = float((len(timestamps) - 1) / duration_s) if duration_s > 0 else np.nan
    median_rate_hz = float(1.0 / positive_diffs_s.median()) if not positive_diffs_s.empty else np.nan
    jitter_s = float(positive_diffs_s.std()) if len(positive_diffs_s) > 1 else np.nan

    rssi = _series_or_empty_numeric(df, "rssi")
    valid_mask = detect_valid_subcarriers(amplitude_matrix, threshold=amp_threshold)
    active_start, active_end, active_interval_source = get_active_interval_from_metadata(meta)

    session_id = meta.get("session", {}).get("id") if isinstance(meta, dict) else None
    if not session_id:
        session_id = csv_path.stem

    metrics = {
        "session_id": session_id,
        "dataset_source": csv_path.parent.name,
        "source_csv": csv_path.name,
        "metadata_json": Path(meta_path).name if meta_path else None,
        "metadata_status": metadata_status,
        "invalidation_reason": invalidation_reason,
        "label_name": label_name,
        "label": label_value,
        "raw_rows": raw_rows,
        "csi_rows": csi_rows,
        "valid_rows": int(len(df)),
        "dropped_rows_total": int(raw_rows - len(df)),
        "invalid_timestamp_rows": invalid_timestamp_rows,
        "parse_error_rows": parse_error_rows,
        "length_mismatch_rows": length_mismatch_rows,
        "duration_s": duration_s,
        "effective_rate_hz": effective_rate_hz,
        "median_rate_hz": median_rate_hz,
        "jitter_s": jitter_s,
        "rssi": _rssi_summary(rssi),
        "n_raw_values": int(expected_raw_length),
        "n_complex_subcarriers": int(expected_raw_length // 2),
        "n_valid_subcarriers_session": int(valid_mask.sum()),
        "active_interval_source": active_interval_source,
        "active_start": str(active_start) if active_start is not None else None,
        "active_end": str(active_end) if active_end is not None else None,
    }

    return {
        "session_id": session_id,
        "dataset_source": csv_path.parent.name,
        "csv_path": csv_path,
        "meta_path": Path(meta_path) if meta_path else None,
        "metadata": meta,
        "metadata_status": metadata_status,
        "invalidation_reason": invalidation_reason,
        "label_name": label_name,
        "label": label_value,
        "timestamps": timestamps,
        "raw_matrix": raw_matrix,
        "complex_matrix": complex_matrix,
        "amplitude_matrix": amplitude_matrix,
        "rssi": rssi,
        "time_diffs_s": positive_diffs_s.to_numpy(dtype=np.float64),
        "effective_rate_hz": effective_rate_hz,
        "median_rate_hz": median_rate_hz,
        "jitter_s": jitter_s,
        "valid_mask": valid_mask,
        "active_start": active_start,
        "active_end": active_end,
        "active_interval_source": active_interval_source,
        "metrics": metrics,
    }
