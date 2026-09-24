"""Evaluation metrics, robustness checks, and publication plotting."""

from wifi_csi.evaluation.metrics import (
    false_alarm_rate,
    compute_metrics,
)
from wifi_csi.evaluation.robustness import compute_grouped_metrics
from wifi_csi.evaluation.plotting import (
    plot_confusion_matrix,
    plot_model_comparison,
    plot_feature_importance,
)

__all__ = [
    "false_alarm_rate",
    "compute_metrics",
    "compute_grouped_metrics",
    "plot_confusion_matrix",
    "plot_model_comparison",
    "plot_feature_importance",
]
