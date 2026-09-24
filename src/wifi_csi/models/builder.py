"""Factory for constructing atomic Scikit-Learn pipelines."""

from typing import Any
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC


def build_presence_pipeline(classifier: Any, with_scaler: bool = True) -> Pipeline:
    """Build an atomic Scikit-Learn pipeline bundling StandardScaler and classifier."""
    steps = []
    if with_scaler:
        steps.append(("scaler", StandardScaler()))
    steps.append(("classifier", classifier))
    return Pipeline(steps)


def get_base_estimators(random_seed: int = 42) -> dict[str, Any]:
    """Return default dictionary of candidate presence classifiers."""
    return {
        "random_forest": RandomForestClassifier(random_state=random_seed),
        "svm": SVC(random_state=random_seed),
        "gradient_boosting": GradientBoostingClassifier(random_state=random_seed),
        "mlp": MLPClassifier(random_state=random_seed, max_iter=500),
    }
