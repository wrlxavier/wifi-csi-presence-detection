#!/usr/bin/env python3
"""Run end-to-end CSI data processing pipeline: raw data -> features -> splits."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from wifi_csi.core.config import load_yaml_config
from wifi_csi.parsing.metadata_parser import discover_sessions
from wifi_csi.signal.amplitudes import load_session_arrays
from wifi_csi.signal.subcarrier_filter import compute_shared_valid_mask
from wifi_csi.features.extractor import build_feature_dataset
from wifi_csi.models.splitting import create_stratified_splits


def main():
    parser = argparse.ArgumentParser(description="Run the CSI processing pipeline.")
    parser.add_argument("--config", type=str, default="configs/pipeline.yaml", help="Path to pipeline configuration")
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    print("=" * 65)
    print("  WI-FI CSI PRESENCE DETECTION - DATA PIPELINE")
    print("=" * 65)

    raw_dir = Path(cfg.paths.raw_dir)
    data_dirs = [raw_dir / "pilot", raw_dir / "main"]
    print(f"Scanning directories: {[str(d) for d in data_dirs]}")

    sessions_df = discover_sessions(
        data_dirs=data_dirs,
        required_status=cfg.preprocessing.required_metadata_status,
        label_map=cfg.label_map,
    )
    if sessions_df.empty:
        raise FileNotFoundError(f"No CSV sessions found in {data_dirs}")

    valid_sessions_df = sessions_df.loc[sessions_df["is_metadata_valid"]].copy()
    print(f"Discovered: {len(sessions_df)} total sessions ({len(valid_sessions_df)} eligible VALID sessions)")

    # Load session arrays
    loaded_sessions = []
    for _, row in valid_sessions_df.iterrows():
        print(f"Loading session {row['session_id']} ({row['label_name']})...")
        s = load_session_arrays(
            csv_path=row["csv_path"],
            meta_path=row["metadata_path"],
            required_status=cfg.preprocessing.required_metadata_status,
            label_map=cfg.label_map,
            amp_threshold=cfg.preprocessing.subcarrier_mean_amp_threshold,
        )
        loaded_sessions.append(s)

    # Compute shared valid mask
    shared_mask = compute_shared_valid_mask(
        loaded_sessions,
        min_subcarriers=cfg.preprocessing.min_shared_valid_subcarriers,
    )
    n_valid_subcarriers = int(shared_mask.sum())
    print(f"\nShared valid HT40 subcarriers across all sessions: {n_valid_subcarriers}")

    # Build feature dataset
    print(f"Extracting features (window={cfg.preprocessing.window_seconds}s, filter={cfg.preprocessing.filter_type})...")
    features_df, mapping_df, details = build_feature_dataset(
        sessions=loaded_sessions,
        shared_mask=shared_mask,
        window_seconds=cfg.preprocessing.window_seconds,
        filter_type=cfg.preprocessing.filter_type,
        butterworth_cutoff_hz=cfg.preprocessing.butterworth_cutoff_hz,
        butterworth_order=cfg.preprocessing.butterworth_order,
        min_absolute_samples=cfg.preprocessing.min_absolute_samples_per_window,
        min_rate_fraction=cfg.preprocessing.min_window_sample_rate_fraction,
    )

    print(f"Extracted feature dataset shape: {features_df.shape}")
    label_counts = features_df["label"].value_counts().to_dict()
    print(f"Class distribution: {label_counts} (0=empty, 1=occupied)")

    # Save processed features
    proc_dir = Path(cfg.paths.processed_dir)
    proc_dir.mkdir(parents=True, exist_ok=True)

    feat_parquet = proc_dir / "features_ht40.parquet"
    feat_csv = proc_dir / "features_ht40.csv"
    mapping_csv = proc_dir / "valid_subcarrier_mapping.csv"

    features_df.to_parquet(feat_parquet, index=False)
    features_df.to_csv(feat_csv, index=False)
    mapping_df.to_csv(mapping_csv, index=False)
    print(f"\nSaved processed feature files to {proc_dir}")

    # Generate splits
    splits_dir = proc_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    df_train, df_val, df_test = create_stratified_splits(
        features_df,
        val_size=cfg.splits.val_size,
        test_size=cfg.splits.test_size,
        random_seed=cfg.splits.random_seed,
    )
    df_train.to_parquet(splits_dir / "train.parquet", index=False)
    df_val.to_parquet(splits_dir / "val.parquet", index=False)
    df_test.to_parquet(splits_dir / "test.parquet", index=False)

    print(f"Splits generated: train={len(df_train)}, val={len(df_val)}, test={len(df_test)}")
    print(f"Saved splits to {splits_dir}")

    # Save pipeline report
    reports_log_dir = Path(cfg.paths.reports_dir) / "logs"
    reports_log_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "n_sessions": len(loaded_sessions),
        "valid_subcarriers": n_valid_subcarriers,
        "total_windows": len(features_df),
        "class_distribution": {int(k): int(v) for k, v in label_counts.items()},
        "splits": {
            "train_windows": len(df_train),
            "val_windows": len(df_val),
            "test_windows": len(df_test),
        },
    }
    report_file = reports_log_dir / "pipeline_run_latest.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved pipeline execution report to {report_file}")
    print("=" * 65)


if __name__ == "__main__":
    main()
