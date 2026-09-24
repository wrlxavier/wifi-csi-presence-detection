"""Unit tests for Scikit-Learn Pipeline building and atomic serialization."""

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from wifi_csi.models.builder import build_presence_pipeline
from wifi_csi.models.serialization import save_model_bundle, load_model_bundle


def test_build_presence_pipeline():
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    pipe = build_presence_pipeline(rf, with_scaler=True)
    assert len(pipe.steps) == 2
    assert pipe.steps[0][0] == "scaler"
    assert pipe.steps[1][0] == "classifier"

    # Test fit and predict
    X = np.random.normal(size=(50, 10))
    y = np.random.choice([0, 1], size=50)
    pipe.fit(X, y)
    preds = pipe.predict(X)
    assert len(preds) == 50
    assert set(preds).issubset({0, 1})


def test_save_and_load_model_bundle(tmp_path):
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    pipe = build_presence_pipeline(rf)
    X = np.random.normal(size=(20, 5))
    y = np.random.choice([0, 1], size=20)
    pipe.fit(X, y)

    bundle_dir = save_model_bundle(
        pipeline=pipe,
        name="test_rf",
        output_dir=tmp_path / "registry",
        metadata={"test_metric": 0.95},
        save_legacy_flat=False,
    )
    assert bundle_dir.exists()
    assert (bundle_dir / "pipeline.joblib").exists()
    assert (bundle_dir / "model_card.json").exists()

    loaded_pipe, card = load_model_bundle(bundle_dir)
    assert card["model_name"] == "test_rf"
    assert card["metadata"]["test_metric"] == 0.95
    loaded_preds = loaded_pipe.predict(X)
    np.testing.assert_array_equal(pipe.predict(X), loaded_preds)
