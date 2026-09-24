#!/usr/bin/env python3
"""Evaluate models on validation/test sets and compute robustness benchmarks."""

import argparse
from pathlib import Path
import json
import matplotlib.pyplot as plt
import pandas as pd

from wifi_csi.core.config import load_yaml_config
from wifi_csi.models.splitting import load_feature_table, split_features_metadata
from wifi_csi.models.serialization import load_model_bundle
from wifi_csi.evaluation.metrics import compute_metrics
from wifi_csi.evaluation.robustness import compute_grouped_metrics
from wifi_csi.evaluation.plotting import plot_confusion_matrix, plot_model_comparison
from wifi_csi.parsing.metadata_parser import load_session_metadata


def main():
    parser = argparse.ArgumentParser(description="Evaluate presence detection models.")
    parser.add_argument("--config", type=str, default="configs/models.yaml", help="Path to models config")
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    print("=" * 65)
    print("  WI-FI CSI PRESENCE DETECTION - MODEL EVALUATION")
    print("=" * 65)

    splits_dir = Path(cfg.paths.splits_dir)
    val_file = splits_dir / "val.parquet"
    test_file = splits_dir / "test.parquet"

    val_df = load_feature_table(val_file)
    test_df = load_feature_table(test_file)

    X_val, y_val, meta_val = split_features_metadata(val_df)
    X_test, y_test, meta_test = split_features_metadata(test_df)

    # Load pipelines from registry
    registry_dir = Path(cfg.paths.registry_dir)
    model_names = list(cfg.models.keys())
    pipelines = {}

    for name in model_names:
        bundle_dir = registry_dir / f"{name}_bundle"
        if bundle_dir.exists():
            pipe, card = load_model_bundle(bundle_dir)
            pipelines[name] = pipe
        else:
            print(f"Warning: bundle not found for {name} in {registry_dir}")

    if not pipelines:
        raise FileNotFoundError(f"No trained model bundles found in {registry_dir}. Run 'make train' first.")

    # Validation evaluation
    val_rows = []
    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    axes_flat = axes.flatten()

    for idx, (name, pipe) in enumerate(pipelines.items()):
        y_val_pred = pipe.predict(X_val)
        metrics = compute_metrics(y_val, y_val_pred)
        val_rows.append({"model": name, **metrics})
        if idx < len(axes_flat):
            plot_confusion_matrix(y_val, y_val_pred, ax=axes_flat[idx], title=f"{name} (val)")

    val_metrics = pd.DataFrame(val_rows).sort_values("f1_macro", ascending=False).reset_index(drop=True)
    print("\nValidation Set Performance:")
    print(val_metrics.to_string(index=False))

    # Save validation confusion matrices
    fig_dir = Path(cfg.paths.reports_dir) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(fig_dir / "confusion_matrices_val.png", dpi=200, bbox_inches="tight")
    plt.close()

    # Save validation comparison bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    plot_model_comparison(val_metrics, ax=ax, title="Validation Set Metrics Across Models")
    plt.savefig(fig_dir / "model_comparison_val.png", dpi=200, bbox_inches="tight")
    plt.close()

    # Select best model based on validation F1-macro
    best_name = val_metrics.iloc[0]["model"]
    best_pipe = pipelines[best_name]
    print(f"\nBest model selected: {best_name}")

    # Evaluate best model on test set
    y_test_pred = best_pipe.predict(X_test)
    test_metrics = compute_metrics(y_test, y_test_pred)

    print("\nHeld-out Test Set Performance:")
    for k, v in test_metrics.items():
        print(f"  {k:20s}: {v:.4f}")

    # Plot test confusion matrix
    fig, ax = plt.subplots(figsize=(4, 3.5))
    plot_confusion_matrix(y_test, y_test_pred, ax=ax, title=f"{best_name} (Held-out Test)")
    plt.tight_layout()
    plt.savefig(fig_dir / "confusion_matrix_test.png", dpi=200, bbox_inches="tight")
    plt.close()

    f1_threshold = cfg.experiment.f1_pass_threshold
    passed = bool(test_metrics["f1_macro"] >= f1_threshold)
    print(f"\nTarget metric passed (F1 >= {f1_threshold}): {passed}")

    # Robustness Analysis
    eval_df = meta_test.copy()
    eval_df["y_true"] = y_test.values
    eval_df["y_pred"] = y_test_pred

    # Load session metadata for environment parameters
    raw_pilot = Path("data/01_raw/pilot")
    raw_main = Path("data/01_raw/main")
    meta_pilot = load_session_metadata(raw_pilot) if raw_pilot.exists() else pd.DataFrame()
    meta_main = load_session_metadata(raw_main) if raw_main.exists() else pd.DataFrame()
    all_session_meta = pd.concat([meta_pilot, meta_main])

    eval_df = eval_df.join(all_session_meta[["tx_rx_los_distance_m", "condition_start"]], on="session_id")
    cond_starts = pd.to_datetime(eval_df["condition_start"], errors="coerce")
    eval_df["time_of_day"] = cond_starts.dt.hour.map(
        lambda h: "afternoon" if 12 <= h < 18 else "night" if h >= 18 or h < 6 else "morning"
    )

    tbl_dir = Path(cfg.paths.reports_dir) / "tables"
    tbl_dir.mkdir(parents=True, exist_ok=True)

    per_session = compute_grouped_metrics(eval_df, "session_id")
    per_session.to_csv(tbl_dir / "robustness_per_session.csv", index=False)

    per_tod = compute_grouped_metrics(eval_df, "time_of_day")
    per_tod.to_csv(tbl_dir / "robustness_per_time_of_day.csv", index=False)

    per_cond = compute_grouped_metrics(eval_df, "label_name")
    per_cond.to_csv(tbl_dir / "robustness_per_condition.csv", index=False)

    print("\nRobustness breakdown by session:")
    print(per_session.to_string(index=False))

    # Save overall evaluation report JSON
    log_dir = Path(cfg.paths.reports_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "validation": val_metrics.to_dict(orient="records"),
        "best_model": best_name,
        "test": test_metrics,
        "f1_threshold": f1_threshold,
        "test_passed": passed,
    }
    with open(log_dir / "evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved evaluation reports and figures to {cfg.paths.reports_dir}")
    print("=" * 65)


if __name__ == "__main__":
    main()

