"""Functions for converting raw CSI vectors to amplitudes, filtering, and windowing."""

from pathlib import Path

import pandas as pd

# Metadata (non-feature) columns present in the pipeline-v0 feature table.
# ``label`` is listed here but returned separately by ``split_features_metadata``.
METADATA_COLS = [
    "session_id",
    "source_csv",
    "label_name",
    "label",
    "window_index",
    "window_start_time",
    "window_end_time",
    "n_samples",
    "effective_rate_hz_window",
]


def load_feature_table(path):
    """Load a pipeline-v0 feature table from CSV or Parquet.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the feature file. ``.parquet`` is read with
        :func:`pandas.read_parquet`; anything else with :func:`pandas.read_csv`.

    Returns
    -------
    pandas.DataFrame
        The full table (metadata + feature columns).
    """
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def split_features_metadata(df):
    """Separate feature columns, target, and metadata of a feature table.

    Feature columns are every column not listed in :data:`METADATA_COLS`
    (the ``sc<NNN>_<descriptor>`` statistics). The target is the binary
    ``label`` column (0 = empty, 1 = occupied).

    Parameters
    ----------
    df : pandas.DataFrame
        A feature table as produced by the v0 pipeline.

    Returns
    -------
    X : pandas.DataFrame
        Feature columns only.
    y : pandas.Series
        The ``label`` target.
    meta : pandas.DataFrame
        The remaining metadata columns present in :data:`METADATA_COLS`.
    """
    feature_cols = [c for c in df.columns if c not in METADATA_COLS]
    meta_cols = [c for c in METADATA_COLS if c in df.columns]
    X = df[feature_cols]
    y = df["label"]
    meta = df[meta_cols]
    return X, y, meta
