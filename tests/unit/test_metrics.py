"""Unit tests for evaluation metrics (Accuracy, F1-macro, False-Alarm-Rate)."""

import numpy as np
import pytest

from wifi_csi.evaluation.metrics import false_alarm_rate, compute_metrics


def test_false_alarm_rate_perfect():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])
    assert false_alarm_rate(y_true, y_pred) == 0.0


def test_false_alarm_rate_with_false_positives():
    y_true = np.array([0, 0, 0, 0, 1, 1])
    # 2 true negatives (predicted 0), 2 false positives (predicted 1)
    y_pred = np.array([0, 0, 1, 1, 1, 1])
    # FAR = FP / (FP + TN) = 2 / (2 + 2) = 0.5
    assert false_alarm_rate(y_true, y_pred) == 0.5


def test_compute_metrics():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 1])  # 1 FP
    metrics = compute_metrics(y_true, y_pred)

    assert "accuracy" in metrics
    assert "f1_macro" in metrics
    assert "false_alarm_rate" in metrics
    assert metrics["accuracy"] == 0.75
    assert metrics["false_alarm_rate"] == 0.5
