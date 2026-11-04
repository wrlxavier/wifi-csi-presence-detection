"""Unit tests for backup_data.py compression, restoration, and validation."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts.backup_data import (
    ZENODO_DEFAULT_ARCHIVE_NAME,
    _find_repo_root,
    _get_untracked_files,
    _validate_structure,
    compress,
    main,
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


def test_get_untracked_files_zenodo_filtering(tmp_path: Path) -> None:
    mock_root = tmp_path / "mock_project_zenodo"
    mock_root.mkdir()

    # Data files
    (mock_root / "data/01_raw/c1").mkdir(parents=True)
    (mock_root / "data/01_raw/c1/session_1.csv").write_text("raw_csi")
    (mock_root / "data/03_processed").mkdir(parents=True)
    (mock_root / "data/03_processed/features.parquet").write_text("parquet")
    (mock_root / "data/03_processed/figures").mkdir(parents=True)
    (mock_root / "data/03_processed/figures/class_distribution.png").write_text("png")

    # Models files
    (mock_root / "models/registry/mlp_bundle").mkdir(parents=True)
    (mock_root / "models/mlp.pkl").write_text("pickle")
    (mock_root / "models/registry/mlp_bundle/model_card.json").write_text("{}")

    # Reports files (optimal_features should be kept, other reports ignored)
    (mock_root / "reports/logs").mkdir(parents=True)
    (mock_root / "reports/logs/optimal_features.json").write_text('{"feature": 1}')
    (mock_root / "reports/logs/evaluation_report.json").write_text('{"eval": 1}')
    (mock_root / "reports/figures").mkdir(parents=True)
    (mock_root / "reports/figures/confusion_matrix.png").write_text("png")
    (mock_root / "reports/tables").mkdir(parents=True)
    (mock_root / "reports/tables/results.tex").write_text("tex")

    # Outputs files (all outputs should be ignored)
    (mock_root / "outputs/plots").mkdir(parents=True)
    (mock_root / "outputs/plots/fig1.png").write_text("png")
    (mock_root / "outputs/backups").mkdir(parents=True)
    (mock_root / "outputs/backups/old.zip").write_text("zip")

    # Standard mode (_get_untracked_files with zenodo=False)
    standard_files = _get_untracked_files(mock_root, zenodo=False)
    standard_str = {f.as_posix() for f in standard_files}
    assert "outputs/plots/fig1.png" in standard_str
    assert "reports/logs/evaluation_report.json" in standard_str
    assert "reports/figures/confusion_matrix.png" in standard_str
    assert "reports/tables/results.tex" in standard_str
    assert "reports/logs/optimal_features.json" in standard_str
    assert "data/03_processed/figures/class_distribution.png" in standard_str

    # Zenodo mode (_get_untracked_files with zenodo=True)
    zenodo_files = _get_untracked_files(mock_root, zenodo=True)
    zenodo_str = {f.as_posix() for f in zenodo_files}

    # Must contain data/ and models/ and reports/logs/optimal_features.json
    assert "data/01_raw/c1/session_1.csv" in zenodo_str
    assert "data/03_processed/features.parquet" in zenodo_str
    assert "models/mlp.pkl" in zenodo_str
    assert "models/registry/mlp_bundle/model_card.json" in zenodo_str
    assert "reports/logs/optimal_features.json" in zenodo_str

    # Must NOT contain outputs/, any other reports/ files, or images in data/
    assert not any(f.startswith("outputs/") for f in zenodo_str)
    assert not any(f.endswith(".png") for f in zenodo_str)
    assert not any("figures" in f for f in zenodo_str)
    reports_in_zenodo = [f for f in zenodo_str if f.startswith("reports/")]
    assert reports_in_zenodo == ["reports/logs/optimal_features.json"]


def test_compress_zenodo_default_and_custom_filename(tmp_path: Path) -> None:
    mock_root = tmp_path / "mock_project_zenodo_compress"
    mock_root.mkdir()

    (mock_root / "data/01_raw").mkdir(parents=True)
    (mock_root / "data/01_raw/raw.csv").write_text("raw")
    (mock_root / "models").mkdir(parents=True)
    (mock_root / "models/model.pkl").write_text("model")
    (mock_root / "reports/logs").mkdir(parents=True)
    (mock_root / "reports/logs/optimal_features.json").write_text("{}")
    (mock_root / "reports/logs/other.json").write_text("{}")
    (mock_root / "outputs/plots").mkdir(parents=True)
    (mock_root / "outputs/plots/plot.png").write_text("plot")

    # 1. Default filename with zenodo=True
    archive_default = compress(
        archive_name=None,
        output_dir=mock_root / "outputs/backups",
        repo_root=mock_root,
        zenodo=True,
    )
    assert archive_default.name == ZENODO_DEFAULT_ARCHIVE_NAME
    assert archive_default.name == "wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip"
    assert archive_default.is_file()

    with zipfile.ZipFile(archive_default, "r") as zf:
        namelist = zf.namelist()
        assert "data/01_raw/raw.csv" in namelist
        assert "models/model.pkl" in namelist
        assert "reports/logs/optimal_features.json" in namelist
        assert "reports/logs/other.json" not in namelist
        assert not any(f.startswith("outputs/") for f in namelist)

    # 2. Custom filename with -f / archive_name overrides default
    archive_custom = compress(
        archive_name="custom_dataset.zip",
        output_dir=mock_root / "outputs/backups",
        repo_root=mock_root,
        zenodo=True,
    )
    assert archive_custom.name == "custom_dataset.zip"
    assert archive_custom.is_file()

    with zipfile.ZipFile(archive_custom, "r") as zf:
        namelist = zf.namelist()
        assert "data/01_raw/raw.csv" in namelist
        assert "models/model.pkl" in namelist
        assert "reports/logs/optimal_features.json" in namelist
        assert "reports/logs/other.json" not in namelist
        assert not any(f.startswith("outputs/") for f in namelist)


def test_cli_compress_zenodo(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_compress(archive_name=None, output_dir="outputs/backups", repo_root=None, zenodo=False):
        calls.append({"archive_name": archive_name, "output_dir": output_dir, "zenodo": zenodo})
        return Path(output_dir) / (archive_name or ZENODO_DEFAULT_ARCHIVE_NAME)

    monkeypatch.setattr("scripts.backup_data.compress", fake_compress)

    # Test subcommand: compress --zenodo
    monkeypatch.setattr("sys.argv", ["backup_data.py", "compress", "--zenodo", "-d", "custom_dir"])
    main()
    assert len(calls) == 1
    assert calls[0]["zenodo"] is True
    assert calls[0]["archive_name"] is None
    assert calls[0]["output_dir"] == "custom_dir"

    # Test subcommand with custom -f: compress --zenodo -f custom_export.zip
    calls.clear()
    monkeypatch.setattr("sys.argv", ["backup_data.py", "compress", "--zenodo", "-f", "custom_export.zip"])
    main()
    assert len(calls) == 1
    assert calls[0]["zenodo"] is True
    assert calls[0]["archive_name"] == "custom_export.zip"

    # Test fallback top-level flag: -c --zenodo
    calls.clear()
    monkeypatch.setattr("sys.argv", ["backup_data.py", "-c", "--zenodo"])
    main()
    assert len(calls) == 1
    assert calls[0]["zenodo"] is True
    assert calls[0]["archive_name"] is None


def test_validate_structure_zenodo_scope(tmp_path: Path) -> None:
    mock_root = tmp_path / "mock_zenodo_valid"
    mock_root.mkdir()

    # Raw
    (mock_root / "data/01_raw/c1").mkdir(parents=True)
    (mock_root / "data/01_raw/c1/sess.csv").write_text("raw")

    # Processed
    (mock_root / "data/03_processed/splits").mkdir(parents=True)
    (mock_root / "data/03_processed/features_ht40.parquet").write_text("parquet")
    for s in ("train", "val", "test"):
        (mock_root / "data/03_processed/splits" / f"{s}.parquet").write_text("split")

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

    # Only optimal_features.json in reports, NO outputs/ at all
    (mock_root / "reports/logs").mkdir(parents=True)
    (mock_root / "reports/logs/optimal_features.json").write_text("{}")

    # Standard validation must fail because outputs/ is missing
    is_valid_std, checks_std = _validate_structure(mock_root, zenodo=False)
    assert is_valid_std is False
    assert any("outputs: Missing" in c for c in checks_std)

    # Zenodo validation must succeed because outputs/ is omitted by design
    is_valid_zenodo, checks_zenodo = _validate_structure(mock_root, zenodo=True)
    assert is_valid_zenodo is True
    assert any("outputs: Omitted by design" in c for c in checks_zenodo)
    assert any("optimal_features.json verified (Zenodo academic scope)" in c for c in checks_zenodo)


def test_restore_zenodo_roundtrip(tmp_path: Path) -> None:
    mock_root = tmp_path / "mock_zenodo_roundtrip"
    mock_root.mkdir()

    # Setup directories
    (mock_root / "data/01_raw/pilot").mkdir(parents=True)
    (mock_root / "data/01_raw/pilot/sess_1.csv").write_text("raw_csi")

    (mock_root / "data/03_processed/splits").mkdir(parents=True)
    (mock_root / "data/03_processed/features_ht40.parquet").write_text("parquet")
    for s in ("train", "val", "test"):
        (mock_root / "data/03_processed/splits" / f"{s}.parquet").write_text("split")

    models = [
        "mlp", "random_forest", "gradient_boosting", "svm",
        "mlp_light", "random_forest_light", "gradient_boosting_light", "svm_light",
    ]
    (mock_root / "models/registry").mkdir(parents=True)
    for m in models:
        (mock_root / "models" / f"{m}.pkl").write_text(f"pkl_{m}")
        bundle = mock_root / "models/registry" / f"{m}_bundle"
        bundle.mkdir()
        (bundle / "pipeline.joblib").write_text("joblib")
        (bundle / "model_card.json").write_text("{}")

    (mock_root / "reports/logs").mkdir(parents=True)
    (mock_root / "reports/logs/optimal_features.json").write_text('{"feature": "test"}')

    # Compress into zenodo archive
    archive_path = compress(
        output_dir=mock_root / "outputs/backups",
        repo_root=mock_root,
        zenodo=True,
    )
    assert archive_path.name == ZENODO_DEFAULT_ARCHIVE_NAME

    # Simulate data loss
    (mock_root / "reports/logs/optimal_features.json").unlink()
    (mock_root / "models/mlp.pkl").unlink()

    # Restore archive with zenodo=True
    is_valid, restored_path = restore(archive_name=archive_path, repo_root=mock_root, zenodo=True)
    assert is_valid is True
    assert restored_path == archive_path
    assert (mock_root / "reports/logs/optimal_features.json").is_file()
    assert (mock_root / "models/mlp.pkl").is_file()

    # Restore with auto-detection (zenodo=False but archive has 'zenodo' in filename)
    (mock_root / "models/mlp.pkl").unlink()
    is_valid_auto, _ = restore(archive_name=archive_path, repo_root=mock_root, zenodo=False)
    assert is_valid_auto is True
    assert (mock_root / "models/mlp.pkl").is_file()


def test_cli_restore_zenodo(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_decompress(archive_name=None, output_dir="outputs/backups", repo_root=None, zenodo=False):
        calls.append({"archive_name": archive_name, "output_dir": output_dir, "zenodo": zenodo})
        return True, Path(output_dir) / (archive_name or ZENODO_DEFAULT_ARCHIVE_NAME)

    monkeypatch.setattr("scripts.backup_data.decompress", fake_decompress)

    # Test subcommand: restore --zenodo
    monkeypatch.setattr("sys.argv", ["backup_data.py", "restore", "--zenodo", "-d", "custom_dir"])
    main()
    assert len(calls) == 1
    assert calls[0]["zenodo"] is True
    assert calls[0]["archive_name"] is None
    assert calls[0]["output_dir"] == "custom_dir"

    # Test subcommand with custom -f: restore --zenodo -f custom_export.zip
    calls.clear()
    monkeypatch.setattr("sys.argv", ["backup_data.py", "restore", "--zenodo", "-f", "custom_export.zip"])
    main()
    assert len(calls) == 1
    assert calls[0]["zenodo"] is True
    assert calls[0]["archive_name"] == "custom_export.zip"


