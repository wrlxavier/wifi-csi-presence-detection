#!/usr/bin/env python3
"""Standalone CLI for real-time ESP32 CSI acquisition and metadata logging."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import time
import signal
import sys

from wifi_csi.acquisition.serial_reader import CSISerialReader
from wifi_csi.acquisition.metadata_logger import generate_session_metadata, write_session_metadata
from wifi_csi.core.config import load_yaml_config


def main():
    parser = argparse.ArgumentParser(description="Collect CSI data from ESP32-S3 over serial.")
    parser.add_argument("--port", type=str, default="/dev/ttyACM0", help="Serial port device")
    parser.add_argument("--baud", type=int, default=921600, help="Baudrate")
    parser.add_argument("--duration", type=int, default=690, help="Recording duration in seconds")
    parser.add_argument("--label", type=str, required=True, help="Session label (e.g., empty, occupied_p1_still)")
    parser.add_argument("--session-id", type=str, required=True, help="Session ID letter/name (e.g., N)")
    parser.add_argument("--campaign", type=str, default="main", help="Campaign directory name")
    parser.add_argument("--config", type=str, default="configs/acquisition.yaml", help="Path to acquisition config")

    args = parser.parse_args()

    # Create timestamp string: YYYYMMDD_HHMM
    now = datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M")
    base_name = f"session_{args.session_id}_{args.label}_{time_str}"

    raw_dir = Path("data/01_raw") / args.campaign
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_file = raw_dir / f"{base_name}.csv"
    json_file = raw_dir / f"{base_name}_meta.json"

    print("=" * 60)
    print("ESP32-S3 CSI Data Acquisition Daemon")
    print("=" * 60)
    print(f"Session ID : {args.session_id}")
    print(f"Label      : {args.label}")
    print(f"Duration   : {args.duration} s")
    print(f"Port       : {args.port} @ {args.baud} bps")
    print(f"Output CSV : {csv_file}")
    print(f"Output JSON: {json_file}")
    print("=" * 60)

    reader = CSISerialReader(port=args.port, baudrate=args.baud)

    # Signal handler for graceful termination
    interrupted = False

    def handle_sigint(sig, frame):
        nonlocal interrupted
        print("\n[!] Ctrl+C detected. Finalizing and saving captured samples...")
        interrupted = True

    signal.signal(signal.SIGINT, handle_sigint)

    def progress(count, elapsed):
        rate = count / elapsed if elapsed > 0 else 0
        sys.stdout.write(f"\rCaptured: {count:6d} packets | Elapsed: {elapsed:5.1f} s | Rate: {rate:5.1f} Hz")
        sys.stdout.flush()

    try:
        reader.connect()
        t0 = datetime.now(timezone.utc).isoformat()
        t1 = (now + datetime.timedelta(seconds=60)).isoformat() if hasattr(datetime, "timedelta") else t0
        res = reader.capture_session(output_csv=csv_file, duration_s=args.duration, callback=progress)
        t3 = datetime.now(timezone.utc).isoformat()
        t2 = t3
    finally:
        reader.disconnect()

    print("\n\nAcquisition finished!")
    print(f"Total packets logged: {res['samples_captured']}")
    print(f"Elapsed time        : {res['duration_s']:.2f} s")

    # Generate metadata JSON
    meta = generate_session_metadata(
        session_id=args.session_id,
        label=args.label,
        csv_filename=csv_file.name,
        json_filename=json_file.name,
        t0_iso=t0,
        t1_iso=t0,
        t2_iso=t3,
        t3_iso=t3,
        total_samples=res["samples_captured"],
        planned_duration_s=args.duration,
        status="VALID",
    )
    write_session_metadata(meta, json_file)
    print(f"Metadata saved to   : {json_file}")


if __name__ == "__main__":
    main()
