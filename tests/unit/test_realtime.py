"""Unit tests for real-time inference engine and formatting helpers."""

from pathlib import Path

from scripts.realtime_presence import (
    build_menu_aliases,
    discover_available_models,
    prompt_model_selection,
    render_model_menu,
)
from wifi_csi.acquisition.realtime import (
    RealtimeCSIInference,
    find_serial_port,
    format_duration,
    make_bar,
    make_bipolar_gauge,
)


def test_make_bar():
    empty = make_bar(0.0, width=10, fill_char="#", empty_char="-")
    assert empty == "----------"

    full = make_bar(1.0, width=10, fill_char="#", empty_char="-")
    assert full == "##########"

    half = make_bar(0.5, width=10, fill_char="#", empty_char="-")
    assert half == "#####-----"


def test_make_bipolar_gauge():
    gauge = make_bipolar_gauge(0.0, width=10)
    assert len(gauge) == 10
    assert "◆" in gauge

    gauge_mid = make_bipolar_gauge(0.5, width=10)
    assert len(gauge_mid) == 10


def test_format_duration():
    assert format_duration(0) == "00:00:00"
    assert format_duration(65) == "00:01:05"
    assert format_duration(3665) == "01:01:05"


def test_find_serial_port_explicit():
    assert find_serial_port("/dev/ttyTest") == "/dev/ttyTest"


def test_realtime_csi_inference_init():
    engine = RealtimeCSIInference(port="/dev/ttyUSB0", min_samples=5)
    assert engine.model_name in ["mlp", "random_forest", "svm", "gradient_boosting"]
    assert engine.pipeline is not None
    assert len(engine.raw_indices) > 0
    assert len(engine.feature_names) == len(engine.raw_indices) * 4
    assert engine.window_seconds == 2.0
    assert engine.window_mode == "sliding"

    # Empty buffer should return buffering status
    res = engine.predict_latest()
    assert res["status"] == "buffering"
    assert res["sample_count"] == 0


def test_realtime_csi_inference_tumbling_mode():
    engine = RealtimeCSIInference(port="/dev/ttyUSB0", window_mode="tumbling", window_seconds=2.0)
    assert engine.window_mode == "tumbling"
    assert engine.window_seconds == 2.0
    assert engine.min_samples >= 5

    res = engine.predict_latest()
    assert res["status"] == "buffering"
    assert res["window_mode"] == "tumbling"


def test_discover_available_models():
    repo_root = Path.cwd()
    models, best = discover_available_models(repo_root)

    assert len(models) >= 4
    model_keys = [m["key"] for m in models]
    assert "mlp" in model_keys
    assert "random_forest" in model_keys
    assert "gradient_boosting" in model_keys
    assert "svm" in model_keys

    # Best model should be first in the list
    assert models[0]["is_best"] is True
    assert models[0]["key"] == best


def test_build_menu_aliases():
    mock_models = [
        {"key": "mlp"},
        {"key": "random_forest"},
        {"key": "gradient_boosting"},
        {"key": "svm"},
    ]
    aliases = build_menu_aliases(mock_models, best_model_name="mlp")

    # Default / Enter
    assert aliases[""] == "mlp"
    assert aliases["default"] == "mlp"

    # Numeric selections
    assert aliases["1"] == "mlp"
    assert aliases["2"] == "random_forest"
    assert aliases["3"] == "gradient_boosting"
    assert aliases["4"] == "svm"

    # Exact names and shortcuts
    assert aliases["mlp"] == "mlp"
    assert aliases["rf"] == "random_forest"
    assert aliases["random_forest"] == "random_forest"
    assert aliases["random forest"] == "random_forest"
    assert aliases["gb"] == "gradient_boosting"
    assert aliases["gbdt"] == "gradient_boosting"
    assert aliases["svm"] == "svm"


def test_render_model_menu():
    repo_root = Path.cwd()
    models, _ = discover_available_models(repo_root)

    # ANSI Box render
    rendered_box = render_model_menu(models, inner_w=74, plain=False)
    assert "WI-FI CSI REAL-TIME PRESENCE DETECTION" in rendered_box
    assert "MODEL SELECTION MENU" in rendered_box
    assert "RECOMMENDED / BEST" in rendered_box
    assert "mlp" in rendered_box

    # Plain render
    rendered_plain = render_model_menu(models, plain=True)
    assert "MODEL SELECTION" in rendered_plain
    assert "mlp" in rendered_plain


def test_prompt_model_selection(monkeypatch):
    repo_root = Path.cwd()

    # Simulate pressing enter (default option)
    monkeypatch.setattr("builtins.input", lambda _: "")
    chosen = prompt_model_selection(repo_root, plain_mode=True)
    assert chosen in ["mlp", "gradient_boosting", "random_forest", "svm"]

    # Simulate selecting option 2
    monkeypatch.setattr("builtins.input", lambda _: "2")
    chosen2 = prompt_model_selection(repo_root, plain_mode=True)
    assert chosen2 != ""

    # Simulate typing 'svm'
    monkeypatch.setattr("builtins.input", lambda _: "svm")
    chosen_svm = prompt_model_selection(repo_root, plain_mode=True)
    assert chosen_svm == "svm"
