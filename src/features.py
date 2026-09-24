"""Backward-compatible wrapper for features module."""

from wifi_csi.features.statistical import (
    extract_official_features,
    make_feature_columns,
    OFFICIAL_FEATURE_NAMES,
)

__all__ = ["extract_official_features", "make_feature_columns", "OFFICIAL_FEATURE_NAMES"]
