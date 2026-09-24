"""Integration test for end-to-end processing: raw session -> features -> split."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from wifi_csi.signal.amplitudes import load_session_arrays
from wifi_csi.signal.subcarrier_filter import compute_shared_valid_mask
from wifi_csi.features.extractor import build_feature_dataset
from wifi_csi.models.splitting import create_stratified_splits


def test_pipeline_flow(tmp_path):
    # Create 2 synthetic CSV and meta JSON files
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    for idx, label in enumerate(["empty", "occupied_still"]):
        base = raw_dir / f"session_{chr(65+idx)}_{label}"
        csv_file = base.with_suffix(".csv")
        json_file = base.with_name(f"{base.name}_meta.json")

        # Create dummy CSV with 150 rows
        ts_base = pd.Timestamp("2026-09-22 12:00:00")
        rows = []
        for r in range(150):
            ts = (ts_base + pd.Timedelta(milliseconds=r * 34.5)).isoformat()
            # 384 numbers string
            iq = np.random.randint(-50, 50, size=384).tolist()
            rows.append({
                "timestamp_host": ts,
                "type": "CSI_DATA",
                "len": 384,
                "rssi": -30,
                "data": json.dumps(iq),
            })
        pd.DataFrame(rows).to_csv(csv_file, index=False)

        # Create dummy meta JSON
        meta = {
            "session": {"id": chr(65 + idx), "label": label},
            "timing": {
                "status": "VALID",
                "t0_recording_start": ts_base.isoformat(),
                "t1_condition_start": ts_base.isoformat(),
                "t2_condition_end": (ts_base + pd.Timedelta(seconds=5)).isoformat(),
                "t3_recording_stop": (ts_base + pd.Timedelta(seconds=5)).isoformat(),
            },
        }
        json_file.write_text(json.dumps(meta))

    # Load sessions
    loaded = []
    for p in sorted(raw_dir.glob("*.csv")):
        s = load_session_arrays(p, p.with_name(f"{p.stem}_meta.json"), amp_threshold=0.0)
        loaded.append(s)

    assert len(loaded) == 2
    mask = compute_shared_valid_mask(loaded, min_subcarriers=10)
    assert mask.sum() >= 10

    # Build dataset
    features_df, mapping_df, details = build_feature_dataset(
        sessions=loaded,
        shared_mask=mask,
        window_seconds=1.0,
        min_absolute_samples=2,
    )
    assert not features_df.empty
    assert "label" in features_df.columns

    # Test split
    df_train, df_val, df_test = create_stratified_splits(features_df, val_size=0.2, test_size=0.2)
    assert len(df_train) + len(df_val) + len(df_test) == len(features_df)
