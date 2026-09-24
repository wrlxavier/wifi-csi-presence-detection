"""Backward-compatible wrapper for preprocessing module."""

from wifi_csi.core.constants import METADATA_COLS
from wifi_csi.models.splitting import load_feature_table, split_features_metadata

__all__ = ["METADATA_COLS", "load_feature_table", "split_features_metadata"]
