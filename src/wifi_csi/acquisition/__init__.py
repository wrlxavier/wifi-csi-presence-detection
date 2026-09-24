"""Hardware data acquisition and serial logging module."""

from wifi_csi.acquisition.serial_reader import CSISerialReader
from wifi_csi.acquisition.metadata_logger import generate_session_metadata
from wifi_csi.acquisition.realtime import (
    RealtimeCSIInference,
    find_serial_port,
    make_bar,
    make_bipolar_gauge,
    format_duration,
)

__all__ = [
    "CSISerialReader",
    "generate_session_metadata",
    "RealtimeCSIInference",
    "find_serial_port",
    "make_bar",
    "make_bipolar_gauge",
    "format_duration",
]


