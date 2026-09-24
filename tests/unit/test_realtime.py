"""Unit tests for real-time inference engine and formatting helpers."""


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

