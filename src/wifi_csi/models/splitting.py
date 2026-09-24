"""Dataset partitioning and feature table splitting."""

from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

from wifi_csi.core.constants import METADATA_COLS


def load_feature_table(path: str | Path) -> pd.DataFrame:
    """Load a feature table from CSV or Parquet."""
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def split_features_metadata(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Separate feature columns, binary label target, and metadata.

    Parameters
    ----------
    df : pd.DataFrame
        Full feature table.

    Returns
    -------
    X : pd.DataFrame
        Feature columns only.
    y : pd.Series
        Binary label target (0 = empty, 1 = occupied).
    meta : pd.DataFrame
        Metadata columns.
    """
    feature_cols = [c for c in df.columns if c not in METADATA_COLS]
    meta_cols = [c for c in METADATA_COLS if c in df.columns]
    X = df[feature_cols]
    y = df["label"]
    meta = df[meta_cols]
    return X, y, meta


def create_stratified_splits(
    df: pd.DataFrame,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split feature dataframe into train, val, and test subsets with stratification."""
    temp_size = val_size + test_size
    df_train, df_temp = train_test_split(
        df,
        test_size=temp_size,
        random_state=random_seed,
        stratify=df["label"],
    )
    val_ratio_in_temp = val_size / temp_size
    df_val, df_test = train_test_split(
        df_temp,
        test_size=(1.0 - val_ratio_in_temp),
        random_state=random_seed,
        stratify=df_temp["label"],
    )
    return (
        df_train.reset_index(drop=True),
        df_val.reset_index(drop=True),
        df_test.reset_index(drop=True),
    )
