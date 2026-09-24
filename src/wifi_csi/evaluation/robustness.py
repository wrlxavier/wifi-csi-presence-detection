"""Robustness benchmark evaluations across sessions, positions, and conditions."""

from typing import Any
import pandas as pd
from wifi_csi.evaluation.metrics import compute_metrics


def compute_grouped_metrics(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Compute presence metrics for each subgroup of df grouped by the given column.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing columns `y_true`, `y_pred`, and the grouping column `by`.
    by : str
        Column name to group by (e.g. 'session_id', 'time_of_day', 'condition').

    Returns
    -------
    pd.DataFrame
        Table with columns: [by, 'n', 'accuracy', 'f1_macro', 'false_alarm_rate'].
    """
    out = []
    for key, g in df.groupby(by, observed=True):
        if len(g) == 0:
            continue
        out.append({by: key, "n": int(len(g)), **compute_metrics(g["y_true"], g["y_pred"])})
    return pd.DataFrame(out)
