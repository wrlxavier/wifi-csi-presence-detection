"""Parsing and validation of metadata sidecars (*_meta.json)."""

from pathlib import Path
from typing import Any
import json
import warnings
import pandas as pd

from wifi_csi.core.constants import DEFAULT_LABEL_MAP
from wifi_csi.parsing.csi_decoder import parse_host_timestamp


def load_metadata(meta_path: str | Path | None) -> dict[str, Any]:
    """Load a metadata JSON file, returning an empty dictionary when unavailable."""
    if meta_path is None:
        return {}
    meta_path = Path(meta_path)
    if not meta_path.exists():
        warnings.warn(f"Metadata file not found: {meta_path}")
        return {}
    with meta_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def infer_label_from_filename(
    csv_path: Path, label_map: dict[str, int] | None = None
) -> str | None:
    """Infer the session label from a CSV filename when metadata does not provide it."""
    mapping = label_map or DEFAULT_LABEL_MAP
    name = csv_path.stem.lower()
    for label_name in sorted(mapping, key=len, reverse=True):
        if label_name in name:
            return label_name
    return None


def infer_label_from_metadata_or_filename(
    meta: dict[str, Any],
    csv_path: Path,
    label_map: dict[str, int] | None = None,
) -> str | None:
    """Infer the label from metadata first and fallback to filename."""
    label_name = meta.get("session", {}).get("label")
    if isinstance(label_name, str) and label_name.strip():
        return label_name.strip()
    return infer_label_from_filename(csv_path, label_map=label_map)


def metadata_validation_details(
    meta: dict[str, Any], required_status: str = "VALID"
) -> tuple[str | None, str | None, bool]:
    """Return metadata validity status, invalidation reason, and validity flag."""
    timing = meta.get("timing", {}) if isinstance(meta, dict) else {}
    status_raw = timing.get("status")
    status = str(status_raw).strip().upper() if status_raw is not None else None
    invalidation_reason = timing.get("invalidation_reason")
    is_valid = status == required_status
    return status, invalidation_reason, is_valid


def get_active_interval_from_metadata(
    meta: dict[str, Any],
) -> tuple[pd.Timestamp | None, pd.Timestamp | None, str]:
    """Extract preferred active condition interval with midnight-rollover handling."""
    timing = meta.get("timing", {}) if isinstance(meta, dict) else {}
    start = parse_host_timestamp(timing.get("t1_condition_start"))
    end = parse_host_timestamp(timing.get("t2_condition_end"))
    if not pd.isna(start) and not pd.isna(end) and end < start:
        end = end + pd.Timedelta(days=1)
    if pd.isna(start) or pd.isna(end) or start >= end:
        return None, None, "missing_or_invalid_metadata_interval"
    return start, end, "metadata_t1_t2"


def discover_sessions(
    data_dirs: list[str | Path] | str | Path,
    required_status: str = "VALID",
    label_map: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Discover CSV sessions and companion metadata files across directories."""
    dirs = [data_dirs] if isinstance(data_dirs, (str, Path)) else data_dirs
    csv_paths: list[Path] = []
    for d in dirs:
        p = Path(d)
        if p.exists():
            csv_paths.extend(sorted(p.glob("*.csv")))

    records: list[dict[str, Any]] = []
    for csv_path in csv_paths:
        meta_path = csv_path.with_name(f"{csv_path.stem}_meta.json")
        meta_exists = meta_path.exists()
        meta = load_metadata(meta_path if meta_exists else None)
        label_name = infer_label_from_metadata_or_filename(meta, csv_path, label_map=label_map)
        status, reason, is_valid = metadata_validation_details(meta, required_status=required_status)
        session_id = meta.get("session", {}).get("id") if isinstance(meta, dict) else None
        dataset_source = csv_path.parent.name

        records.append(
            {
                "dataset_source": dataset_source,
                "csv_path": csv_path,
                "csv_filename": csv_path.name,
                "metadata_path": meta_path if meta_exists else None,
                "metadata_filename": meta_path.name if meta_exists else None,
                "session_id": session_id or csv_path.stem,
                "label_name": label_name,
                "metadata_status": status,
                "is_metadata_valid": is_valid,
                "invalidation_reason": reason,
                "file_size_mb": csv_path.stat().st_size / (1024 * 1024),
            }
        )

    return pd.DataFrame.from_records(records)


def load_session_metadata(meta_dir: str | Path) -> pd.DataFrame:
    """Build a per-session metadata table from *_meta.json sidecar files.

    Maintained for full backward compatibility with original src/parsing.py.
    """
    meta_dir = Path(meta_dir)
    rows = []
    for meta_path in sorted(meta_dir.glob("*_meta.json")):
        session_id = meta_path.name.split("_")[1]
        meta = json.loads(meta_path.read_text())
        setup = meta.get("setup", {})
        nodes = setup.get("nodes", {})
        subject = setup.get("protocol", {}).get("subject_position", {})
        rows.append(
            {
                "session_id": session_id,
                "label": meta.get("session", {}).get("label"),
                "tx_rx_los_distance_m": nodes.get("tx_rx_los_distance_m"),
                "subject_x_from_west_m": subject.get("x_from_west_m"),
                "subject_y_from_north_m": subject.get("y_from_north_m"),
                "condition_start": meta.get("timing", {}).get("t1_condition_start"),
            }
        )
    return pd.DataFrame(rows).set_index("session_id")
