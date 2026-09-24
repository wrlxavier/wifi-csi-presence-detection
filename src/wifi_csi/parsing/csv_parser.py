"""CSV reading and validation for CSI raw session captures."""

from pathlib import Path
import pandas as pd


def read_raw_csi_csv(csv_path: str | Path) -> pd.DataFrame:
    """Read a raw CSI CSV file and filter for type == 'CSI_DATA' rows."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if "type" in df.columns:
        df = df.loc[df["type"].astype(str).eq("CSI_DATA")].copy()

    if "timestamp_host" not in df.columns:
        raise ValueError(f"{csv_path.name} is missing required column: timestamp_host")
    if "data" not in df.columns:
        raise ValueError(f"{csv_path.name} is missing required column: data")

    return df
