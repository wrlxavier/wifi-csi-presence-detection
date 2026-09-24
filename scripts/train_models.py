#!/usr/bin/env python3
"""Train ML models using GridSearchCV and register bundled pipelines."""

import argparse
from pathlib import Path
import json

from wifi_csi.core.config import load_yaml_config
from wifi_csi.models.splitting import load_feature_table, split_features_metadata
from wifi_csi.models.tuning import run_grid_search
from wifi_csi.models.serialization import save_model_bundle


def main():
    parser = argparse.ArgumentParser(description="Train presence detection ML models.")
    parser.add_argument("--config", type=str, default="configs/models.yaml", help="Path to models config")
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    print("=" * 65)
    print("  WI-FI CSI PRESENCE DETECTION - MODEL TRAINING (10-FOLD CV)")
    print("=" * 65)

    splits_dir = Path(cfg.paths.splits_dir)
    train_file = splits_dir / "train.parquet"
    if not train_file.exists():
        raise FileNotFoundError(f"Training split not found: {train_file}. Run 'make pipeline' first.")

    train_df = load_feature_table(train_file)
    X_train, y_train, meta_train = split_features_metadata(train_df)
    print(f"Loaded training data: {X_train.shape[0]} samples, {X_train.shape[1]} features")

    # Run Grid Search
    fitted_pipelines, cv_results = run_grid_search(
        X_train=X_train,
        y_train=y_train,
        search_spaces=cfg.models,
        cv_folds=cfg.experiment.cv_folds,
        scoring=cfg.experiment.scoring,
        random_seed=cfg.experiment.random_seed,
    )

    print("\nCross-Validation Results (Stratified 10-Fold):")
    print(cv_results.to_string(index=False))

    # Save to registry and legacy paths
    registry_dir = Path(cfg.paths.registry_dir)
    legacy_models_dir = Path(cfg.paths.models_dir)

    for name, pipeline in fitted_pipelines.items():
        row = cv_results.loc[cv_results["model"] == name].iloc[0]
        meta = {
            "cv_f1_macro": float(row["cv_f1_macro"]),
            "best_params": row["best_params"],
            "n_features": int(X_train.shape[1]),
            "feature_columns": list(X_train.columns),
        }
        bundle_path = save_model_bundle(
            pipeline=pipeline,
            name=name,
            output_dir=registry_dir,
            metadata=meta,
            save_legacy_flat=True,
            legacy_dir=legacy_models_dir,
        )
        print(f"Saved {name} bundle to {bundle_path}")

    # Save CV results table
    reports_logs = Path(cfg.paths.reports_dir) / "logs"
    reports_logs.mkdir(parents=True, exist_ok=True)
    cv_csv = reports_logs / "cv_results.csv"
    cv_results.to_csv(cv_csv, index=False)

    print(f"\nSaved CV summary table to {cv_csv}")
    print("=" * 65)


if __name__ == "__main__":
    main()

