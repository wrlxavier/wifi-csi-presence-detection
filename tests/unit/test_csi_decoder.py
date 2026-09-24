"""Unit tests for CSI string parsing, timestamp conversion, and complex I/Q decoding."""

import numpy as np
import pandas as pd
import pytest

from wifi_csi.parsing.csi_decoder import (
    parse_csi_array,
    raw_iq_to_complex,
    parse_host_timestamp,
)


def test_parse_host_timestamp_valid():
    ts_str = "2026-09-22T17:03:43-03:00"
    ts = parse_host_timestamp(ts_str)
    assert isinstance(ts, pd.Timestamp)
    assert ts.year == 2026
    assert ts.month == 9
    assert ts.day == 22


def test_parse_host_timestamp_invalid():
    assert pd.isna(parse_host_timestamp(None))
    assert pd.isna(parse_host_timestamp("not-a-date"))


def test_parse_csi_array_from_json_string():
    raw_str = "[0, 1, -5, 12, 33, -4]"
    arr = parse_csi_array(raw_str)
    assert isinstance(arr, np.ndarray)
    assert len(arr) == 6
    np.testing.assert_array_equal(arr, [0, 1, -5, 12, 33, -4])


def test_parse_csi_array_empty_or_invalid():
    assert parse_csi_array("") is None
    assert parse_csi_array("invalid text") is None
    assert parse_csi_array(12345) is None


def test_raw_iq_to_complex(synthetic_raw_iq):
    complex_arr = raw_iq_to_complex(synthetic_raw_iq)
    assert len(complex_arr) == 192
    assert np.iscomplexobj(complex_arr)
    # Check first pair: imag = raw[0], real = raw[1]
    expected_first = synthetic_raw_iq[1] + 1j * synthetic_raw_iq[0]
    assert complex_arr[0] == expected_first


def test_raw_iq_to_complex_odd_length():
    with pytest.raises(ValueError):
        raw_iq_to_complex(np.array([1, 2, 3]))
