"""Signal processing, filtering, masking, and windowing module."""

from wifi_csi.signal.amplitudes import (
    compute_amplitudes,
    load_session_arrays,
)
from wifi_csi.signal.subcarrier_filter import (
    detect_valid_subcarriers,
    compute_shared_valid_mask,
)
from wifi_csi.signal.denoise import (
    filter_amplitude_matrix,
    butterworth_lowpass_filter,
    wavelet_denoise,
)
from wifi_csi.signal.segmentation import (
    select_active_interval,
    segment_non_overlapping_windows,
)

__all__ = [
    "compute_amplitudes",
    "load_session_arrays",
    "detect_valid_subcarriers",
    "compute_shared_valid_mask",
    "filter_amplitude_matrix",
    "butterworth_lowpass_filter",
    "wavelet_denoise",
    "select_active_interval",
    "segment_non_overlapping_windows",
]
