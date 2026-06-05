"""Functions for reading raw CSI session files (CSV + JSON metadata)."""

import json
from pathlib import Path

import pandas as pd


def load_session_metadata(meta_dir):
    """Build a per-session metadata table from ``*_meta.json`` sidecar files.

    Extracts the fields used for robustness analysis: TX-RX line-of-sight
    distance, subject position, and the active-condition start time (for
    time-of-day grouping).

    Parameters
    ----------
    meta_dir : str or pathlib.Path
        Directory containing ``session_<ID>_..._meta.json`` files
        (e.g. ``data/pilot``).

    Returns
    -------
    pandas.DataFrame
        One row per session, indexed by ``session_id`` (the letter parsed
        from the filename, matching the feature table). Columns: ``label``,
        ``tx_rx_los_distance_m``, ``subject_x_from_west_m``,
        ``subject_y_from_north_m``, ``condition_start``.
    """
    meta_dir = Path(meta_dir)
    rows = []
    for meta_path in sorted(meta_dir.glob("*_meta.json")):
        session_id = meta_path.name.split("_")[1]
        meta = json.loads(meta_path.read_text())
        setup = meta.get("setup", {})
        nodes = setup.get("nodes", {})
        subject = setup.get("protocol", {}).get("subject_position", {})
        rows.append(
            {
                "session_id": session_id,
                "label": meta.get("session", {}).get("label"),
                "tx_rx_los_distance_m": nodes.get("tx_rx_los_distance_m"),
                "subject_x_from_west_m": subject.get("x_from_west_m"),
                "subject_y_from_north_m": subject.get("y_from_north_m"),
                "condition_start": meta.get("timing", {}).get("t1_condition_start"),
            }
        )
    return pd.DataFrame(rows).set_index("session_id")
