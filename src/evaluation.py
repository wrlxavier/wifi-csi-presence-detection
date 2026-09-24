"""Backward-compatible wrapper for evaluation module."""

from wifi_csi.evaluation.metrics import false_alarm_rate, compute_metrics
from wifi_csi.evaluation.plotting import plot_confusion_matrix

__all__ = ["false_alarm_rate", "compute_metrics", "plot_confusion_matrix"]
