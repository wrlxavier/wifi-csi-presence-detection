"""Domain constants for 802.11n HT40 CSI processing."""

HT40_N_SUBCARRIERS = 192
HT40_N_RAW_VALUES = 384  # 192 complex numbers (Real, Imag)
NOMINAL_RATE_HZ = 29.0

# Non-feature metadata columns in processed feature tables
METADATA_COLS = [
    "session_id",
    "source_csv",
    "label_name",
    "label",
    "window_index",
    "window_start_time",
    "window_end_time",
    "n_samples",
    "effective_rate_hz_window",
]

DEFAULT_LABEL_MAP = {
    "empty": 0,
    "occupied_still": 1,
    "occupied_moving": 1,
    "occupied_p1_still": 1,
    "occupied_p2_still": 1,
    "occupied_p3_still": 1,
    "occupied_p4_still": 1,
}
