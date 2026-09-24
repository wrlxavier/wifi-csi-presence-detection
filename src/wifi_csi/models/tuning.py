"""Hyperparameter tuning and cross-validation search."""

from typing import Any
import warnings
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from wifi_csi.models.builder import get_base_estimators


def run_grid_search(
    X_train: pd.DataFrame | Any,
    y_train: pd.Series | Any,
    search_spaces: dict[str, dict[str, list[Any]]],
    cv_folds: int = 10,
    scoring: str = "f1_macro",
    random_seed: int = 42,
    n_jobs: int = -1,
) -> tuple[dict[str, Pipeline], pd.DataFrame]:
    """Train candidate estimators using GridSearchCV and return bundled Pipelines.

    Parameters
    ----------
    X_train : pd.DataFrame
        Unscaled raw training features.
    y_train : pd.Series
        Training targets.
    search_spaces : dict
        Mapping from model name to parameter grid dict.
    cv_folds : int
        Number of stratified CV folds.
    scoring : str
        Scoring metric name.
    random_seed : int
        Random seed for CV shuffle.
    n_jobs : int
        Parallel worker count.

    Returns
    -------
    fitted_pipelines : dict[str, Pipeline]
        Mapping from model name to best fitted Pipeline(scaler, classifier).
    cv_results_df : pd.DataFrame
        Table summarizing CV scores and best parameters.
    """
    base_estimators = get_base_estimators(random_seed=random_seed)
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_seed)

    fitted_pipelines: dict[str, Pipeline] = {}
    rows = []

    for name, grid in search_spaces.items():
        if name not in base_estimators:
            continue
        estimator = base_estimators[name]

        # Build pipeline: StandardScaler + Classifier
        pipe = Pipeline([("scaler", StandardScaler()), ("classifier", estimator)])

        # Prefix hyperparameter names with 'classifier__'
        prefixed_grid = {
            f"classifier__{k}" if not k.startswith("classifier__") else k: v
            for k, v in grid.items()
        }

        search = GridSearchCV(
            pipe,
            prefixed_grid,
            cv=cv,
            scoring=scoring,
            n_jobs=n_jobs,
            refit=True,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            search.fit(X_train, y_train)

        best_pipe = search.best_estimator_
        fitted_pipelines[name] = best_pipe

        # Strip prefix for readable reporting
        cleaned_params = {
            k.replace("classifier__", ""): v for k, v in search.best_params_.items()
        }
        rows.append(
            {
                "model": name,
                "cv_f1_macro": float(search.best_score_),
                "best_params": cleaned_params,
            }
        )

    cv_results_df = pd.DataFrame(rows).sort_values("cv_f1_macro", ascending=False).reset_index(drop=True)
    return fitted_pipelines, cv_results_df
