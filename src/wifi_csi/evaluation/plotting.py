"""Publication-ready plotting utilities for model evaluation and reporting."""

from typing import Any
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import pandas as pd


def plot_confusion_matrix(
    y_true: Any,
    y_pred: Any,
    ax: plt.Axes | None = None,
    title: str = "Confusion matrix",
) -> plt.Axes:
    """Plot a 2x2 confusion-matrix heatmap (empty/occupied).

    Parameters
    ----------
    y_true, y_pred : array-like
        True and predicted binary labels.
    ax : matplotlib.axes.Axes, optional
        Axis to draw on. A new figure/axis is created if omitted.
    title : str
        Plot title.

    Returns
    -------
    matplotlib.axes.Axes
        The axis the heatmap was drawn on.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(4, 3.5))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    labels = ["empty", "occupied"]
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    return ax


def plot_model_comparison(
    metrics_df: pd.DataFrame,
    metric_cols: list[str] | None = None,
    ax: plt.Axes | None = None,
    title: str = "Model Comparison",
) -> plt.Axes:
    """Bar chart comparing validation metrics across models."""
    if metric_cols is None:
        metric_cols = ["accuracy", "f1_macro", "false_alarm_rate"]
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))
    plot_df = metrics_df.set_index("model")[metric_cols]
    plot_df.plot(kind="bar", ax=ax, rot=0, ylim=(0, 1.05))
    ax.set_title(title)
    ax.set_ylabel("Score")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    return ax


def plot_feature_importance(
    importances: pd.Series,
    top_n: int = 20,
    ax: plt.Axes | None = None,
    title: str = "Top Feature Importances",
) -> plt.Axes:
    """Horizontal bar chart of top N feature importances."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))
    top = importances.sort_values(ascending=True).tail(top_n)
    top.plot(kind="barh", ax=ax, color="steelblue")
    ax.set_title(title)
    ax.set_xlabel("Importance")
    ax.grid(axis="x", linestyle="--", alpha=0.6)
    return ax
