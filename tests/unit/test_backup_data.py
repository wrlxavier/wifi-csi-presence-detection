"""Unit tests for backup_data.py compression, restoration, and validation."""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from scripts.backup_data import (
    _find_repo_root,
    _get_untracked_files,
    _validate_structure,
    compress,
    restore,
)


def test_find_repo_root() -> None:
    root = _find_repo_root()
    assert (root / "pyproject.toml").exists()
    assert (root / "src").is_dir()


def test_validate_structure_live_repo() -> None:
    root = _find_repo_root()
    valid, checks = _validate_structure(root)
    assert valid is True
    assert any("Standard & Light model families complete" in c for c in checks)
    assert any("optimal_features.json verified" in c for c in checks)


def test_validate_structure_missing_optimal_features(tmp_path: Path) -> None:
    mock_root = tmp_path / "mock_project"
    mock_root.mkdir()

    # Raw
    (mock_root / "data/01_raw/c1").mkdir(parents=True)
    (mock_root / "data/01_raw/c1/session_1.csv").write_text("dummy")

    # Processed
    (mock_root / "data/03_processed/splits").mkdir(parents=True)
    (mock_root / "data/03_processed/features_ht40.parquet").write_text("dummy")
    for s in ("train", "val", "test"):
        (mock_root / "data/03_processed/splits" / f"{s}.parquet").write_text("dummy")

    # Models (standard + light)
    (mock_root / "models/registry").mkdir(parents=True)
    models = [
        "mlp", "random_forest", "gradient_boosting", "svm",
        "mlp_light", "random_forest_light", "gradient_boosting_light", "svm_light",
    ]
    for m in models:
        (mock_root / "models" / f"{m}.pkl").write_text("model")
        bundle = mock_root / "models/registry" / f"{m}_bundle"
        bundle.mkdir()
        (bundle / "pipeline.joblib").write_text("joblib")
        (bundle / "model_card.json").write_text("{}")

    # Outputs
    (mock_root / "outputs/fig").mkdir(parents=True)
    (mock_root / "outputs/fig/plot.png").write_text("png")

    # Reports WITHOUT optimal_features.json
    (mock_root / "reports/tables").mkdir(parents=True)
    (mock_root / "reports/tables/tbl.csv").write_text("tbl")

    valid, checks = _validate_structure(mock_root)
    assert valid is False
    assert any("Missing optimal_features.json" in c for c in checks)


def test_compress_and_restore_roundtrip(tmp_path: Path) -> None:
    mock_root = tmp_path / "mock_repo"
    mock_root.mkdir()

    # Setup directories
    (mock_root / "data/01_raw/pilot").mkdir(parents=True)
    (mock_root / "data/01_raw/pilot/sess_1.csv").write_text("raw_csi_content")

    (mock_root / "data/03_processed/splits").mkdir(parents=True)
    (mock_root / "data/03_processed/features_ht40.parquet").write_text("features_parquet")
    for s in ("train", "val", "test"):
        (mock_root / "data/03_processed/splits" / f"{s}.parquet").write_text(f"split_{s}")

    models = [
        "mlp", "random_forest", "gradient_boosting", "svm",
        "mlp_light", "random_forest_light", "gradient_boosting_light", "svm_light",
    ]
    (mock_root / "models/registry").mkdir(parents=True)
    for m in models:
        (mock_root / "models" / f"{m}.pkl").write_text(f"pkl_{m}")
        bundle = mock_root / "models/registry" / f"{m}_bundle"
        bundle.mkdir()
        (bundle / "pipeline.joblib").write_text(f"joblib_{m}")
        (bundle / "model_card.json").write_text(json.dumps({"model_name": m}))

    (mock_root / "outputs/plots").mkdir(parents=True)
    (mock_root / "outputs/plots/fig1.png").write_text("png_bytes")

    (mock_root / "reports/logs").mkdir(parents=True)
    (mock_root / "reports/logs/optimal_features.json").write_text(
        json.dumps({"best_standard_model": "mlp", "best_light_model": "gradient_boosting_light"})
    )

    # 1. Compress
    archive_path = compress(
        archive_name="test_backup.zip",
        output_dir=mock_root / "outputs/backups",
        repo_root=mock_root,
    )
    assert archive_path.is_file()

    # Inspect zip contents
    with zipfile.ZipFile(archive_path, "r") as zf:
        namelist = zf.namelist()
        assert "reports/logs/optimal_features.json" in namelist
        for m in models:
            assert f"models/{m}.pkl" in namelist
            assert f"models/registry/{m}_bundle/pipeline.joblib" in namelist
            assert f"models/registry/{m}_bundle/model_card.json" in namelist

    # 2. Simulate data loss by removing files
    (mock_root / "reports/logs/optimal_features.json").unlink()
    (mock_root / "models/gradient_boosting_light.pkl").unlink()
    (mock_root / "models/registry/gradient_boosting_light_bundle/pipeline.joblib").unlink()

    # Confirm broken structure before restore
    valid_before, _ = _validate_structure(mock_root)
    assert valid_before is False

    # 3. Restore
    is_valid_after, restored_archive = restore(archive_name=archive_path, repo_root=mock_root)
    assert is_valid_after is True
    assert restored_archive == archive_path

    # Verify restored files
    assert (mock_root / "reports/logs/optimal_features.json").is_file()
    assert (mock_root / "models/gradient_boosting_light.pkl").is_file()
    assert (mock_root / "models/registry/gradient_boosting_light_bundle/pipeline.joblib").is_file()
    assert (mock_root / "models/registry/gradient_boosting_light_bundle/model_card.json").is_file()

    # Verify JSON content intact
    with open(mock_root / "reports/logs/optimal_features.json", encoding="utf-8") as f:
        meta = json.load(f)
        assert meta["best_light_model"] == "gradient_boosting_light"
