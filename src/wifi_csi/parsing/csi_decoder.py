"""Decoders for raw CSI arrays, timestamps, and I/Q complex conversion."""

from typing import Any
import ast
import json
import numpy as np
import pandas as pd


def parse_host_timestamp(value: Any) -> pd.Timestamp:
    """Parse a host timestamp and return a timezone-naive local pandas Timestamp."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return pd.NaT
    try:
        timestamp = pd.to_datetime(value, errors="coerce")
    except Exception:
        return pd.NaT
    if pd.isna(timestamp):
        return pd.NaT
    if getattr(timestamp, "tzinfo", None) is not None:
        timestamp = timestamp.tz_localize(None)
    return pd.Timestamp(timestamp)


def parse_csi_array(data_str: Any) -> np.ndarray | None:
    """Parse a CSI data field into a one-dimensional numeric NumPy array."""
    if isinstance(data_str, np.ndarray):
        raw = data_str
    elif isinstance(data_str, (list, tuple)):
        raw = np.asarray(data_str)
    elif isinstance(data_str, str):
        text = data_str.strip()
        if not text:
            return None
        try:
            raw = np.asarray(json.loads(text))
        except (json.JSONDecodeError, ValueError):
            try:
                raw = np.asarray(ast.literal_eval(text))
            except (ValueError, SyntaxError):
                return None
    else:
        return None

    if raw.ndim != 1:
        return None
    try:
        raw = raw.astype(np.float64)
    except (TypeError, ValueError):
        return None
    if not np.all(np.isfinite(raw)):
        return None
    return raw


def raw_iq_to_complex(raw: np.ndarray) -> np.ndarray:
    """Convert ESP32 interleaved [imag_0, real_0, ...] CSI into real + 1j * imag."""
    if raw.ndim != 1:
        raise ValueError("Raw CSI vector must be one-dimensional.")
    if len(raw) % 2 != 0:
        raise ValueError(f"Raw CSI vector length must be even, got {len(raw)}.")
    imag = raw[0::2]
    real = raw[1::2]
    return real.astype(np.float64) + 1j * imag.astype(np.float64)
