"""Metadata sidecar (*_meta.json) generation with relative file paths."""

from pathlib import Path
from typing import Any
import json


def generate_session_metadata(
    session_id: str,
    label: str,
    csv_filename: str,
    json_filename: str,
    t0_iso: str,
    t1_iso: str,
    t2_iso: str,
    t3_iso: str,
    total_samples: int,
    avg_rssi: float | None = None,
    planned_duration_s: int = 690,
    status: str = "VALID",
    room_meta: dict[str, Any] | None = None,
    nodes_meta: dict[str, Any] | None = None,
    protocol_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate standardized session metadata dictionary with relative file paths."""
    meta = {
        "schema_version": "2.1",
        "session": {
            "id": session_id,
            "label": label,
            "files": {
                "csv": csv_filename,
                "json": json_filename,
            },
            "planned_duration_s": planned_duration_s,
        },
        "timing": {
            "t0_recording_start": t0_iso,
            "t1_condition_start": t1_iso,
            "t2_condition_end": t2_iso,
            "t3_recording_stop": t3_iso,
            "total_samples": total_samples,
            "status": status,
            "invalidation_reason": "" if status == "VALID" else "Manual invalidation",
        },
        "environment": {
            "temperature_C": None,
            "avg_rssi_dbm": avg_rssi,
            "door_state": "closed",
            "window_state": "closed",
        },
        "setup": {
            "room": room_meta or {
                "description": "Residential bedroom, brick walls, concrete slab ceiling",
                "dimensions_m": {"east_west": 3.4, "north_south": 3.45, "ceiling_height": 2.85},
            },
            "nodes": nodes_meta or {
                "tx": {"device": "ESP32-S3-DevKitC-1", "tripod_height_m": 1.2},
                "rx": {"device": "ESP32-S3-DevKitC-1", "tripod_height_m": 1.2},
            },
            "protocol": protocol_meta or {},
        },
    }
    return meta


def write_session_metadata(meta: dict[str, Any], output_path: str | Path) -> None:
    """Write metadata dictionary to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
