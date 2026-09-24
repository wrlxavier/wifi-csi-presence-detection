"""Model bundle serialization, loading, and model card generation."""

from pathlib import Path
from typing import Any
from datetime import datetime, timezone
import json
import joblib
from sklearn.pipeline import Pipeline


def save_model_bundle(
    pipeline: Pipeline,
    name: str,
    output_dir: str | Path,
    metadata: dict[str, Any] | None = None,
    save_legacy_flat: bool = True,
    legacy_dir: str | Path | None = None,
) -> Path:
    """Save an atomic pipeline and accompanying model card.

    Parameters
    ----------
    pipeline : Pipeline
        Fitted Scikit-Learn Pipeline containing scaler and classifier.
    name : str
        Model identifier (e.g. 'gradient_boosting').
    output_dir : str or Path
        Target directory for versioned registry.
    metadata : dict, optional
        Metrics, hyperparams, subcarrier mask count, git hash, etc.
    save_legacy_flat : bool
        If True, also saves flat model into legacy_dir as models/<name>.pkl.
    legacy_dir : str or Path, optional
        Directory for flat pickle files (defaults to models/).

    Returns
    -------
    Path
        Path to saved pipeline bundle directory.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = out_dir / f"{name}_bundle"
    bundle_path.mkdir(parents=True, exist_ok=True)

    # Save atomic pipeline
    pipeline_file = bundle_path / "pipeline.joblib"
    joblib.dump(pipeline, pipeline_file)

    # Save model card
    card = {
        "model_name": name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_steps": [step[0] for step in pipeline.steps],
        "classifier_class": pipeline.named_steps["classifier"].__class__.__name__,
        "classifier_params": pipeline.named_steps["classifier"].get_params(),
        "metadata": metadata or {},
    }
    with open(bundle_path / "model_card.json", "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2)

    # Save legacy flat pickles if requested
    if save_legacy_flat and legacy_dir:
        leg_dir = Path(legacy_dir)
        leg_dir.mkdir(parents=True, exist_ok=True)

        classifier = pipeline.named_steps.get("classifier")
        scaler = pipeline.named_steps.get("scaler")

        if classifier is not None:
            joblib.dump(classifier, leg_dir / f"{name}.pkl")
        if scaler is not None:
            joblib.dump(scaler, leg_dir / "scaler.pkl")

    return bundle_path


def load_model_bundle(bundle_dir: str | Path) -> tuple[Pipeline, dict[str, Any]]:
    """Load a pipeline bundle and its model card."""
    b_dir = Path(bundle_dir)
    pipeline_file = b_dir / "pipeline.joblib"
    card_file = b_dir / "model_card.json"

    if not pipeline_file.exists():
        raise FileNotFoundError(f"Pipeline file not found: {pipeline_file}")

    pipeline = joblib.load(pipeline_file)
    card = {}
    if card_file.exists():
        with open(card_file, "r", encoding="utf-8") as f:
            card = json.load(f)

    return pipeline, card
