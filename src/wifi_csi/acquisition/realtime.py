"""Real-time CSI acquisition and streaming inference engine."""

import json
import threading
import time
import warnings
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import serial
import serial.tools.list_ports

from wifi_csi.core.config import load_yaml_config
from wifi_csi.features.statistical import extract_official_features, make_feature_columns
from wifi_csi.models.serialization import load_model_bundle
from wifi_csi.parsing.csi_decoder import raw_iq_to_complex


def make_bar(ratio: float, width: int = 36, fill_char: str = "█", empty_char: str = "░") -> str:
    """Generate a text-based progress/level bar."""
    ratio = max(0.0, min(1.0, float(ratio)))
    filled_len = round(ratio * width)
    empty_len = max(0, width - filled_len)
    return (fill_char * filled_len) + (empty_char * empty_len)


def make_bipolar_gauge(prob_occupied: float, width: int = 34) -> str:
    """Generate a centered balance gauge between EMPTY (left) and OCCUPIED (right)."""
    p = max(0.0, min(1.0, prob_occupied))
    pos = round(p * (width - 1))
    chars = []
    mid = width // 2
    for i in range(width):
        if i == pos:
            chars.append("◆")
        elif i == mid:
            chars.append("│")
        elif i < pos <= mid or i > pos >= mid:
            chars.append("─")
        elif (pos < mid and pos <= i <= mid) or (pos > mid and mid <= i <= pos):
            chars.append("▓")
        else:
            chars.append("░")
    return "".join(chars)



def format_duration(seconds: float) -> str:
    """Format seconds into HH:MM:SS string."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def find_serial_port(preferred_port: str | None = None) -> str:

    """Auto-detect the active ESP32 / serial port connected to the computer."""
    if preferred_port and preferred_port != "auto":
        return preferred_port

    # Scan available ports
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        # Fallback to standard device paths if comports is empty
        for candidate in ["/dev/ttyUSB0", "/dev/ttyACM0"]:
            if Path(candidate).exists():
                return candidate
        raise ConnectionError("No serial devices detected on system.")

    # 1. Look for known ESP32 / USB-to-UART identifiers
    esp_keywords = ["CP210", "CH340", "USB", "ESP", "UART", "Silicon Labs", "FTDI"]
    for p in ports:
        desc = f"{p.description} {p.manufacturer or ''} {p.hwid}".upper()
        if any(kw.upper() in desc for kw in esp_keywords):
            return p.device

    # 2. Check /dev/ttyUSB* or /dev/ttyACM*
    for p in ports:
        if "ttyUSB" in p.device or "ttyACM" in p.device:
            return p.device

    # 3. Fallback to first available port
    return ports[0].device


class RealtimeCSIInference:
    """Manages serial acquisition, buffered windowing, and live model predictions."""

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = 921600,
        model_name: str | None = None,
        window_seconds: float | None = None,
        window_mode: str = "sliding",
        threshold: float = 0.5,
        repo_root: str | Path | None = None,
        min_samples: int | None = None,
    ):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[3]
        self.port = find_serial_port(port)
        self.baudrate = baudrate
        self.threshold = float(threshold)

        mode_clean = window_mode.lower().strip()
        if mode_clean in ["tumbling", "non-overlapping", "discrete"]:
            self.window_mode = "tumbling"
        elif mode_clean in ["sliding", "rolling", "continuous"]:
            self.window_mode = "sliding"
        else:
            raise ValueError(
                f"Invalid window_mode: {window_mode!r}. Must be 'sliding' or 'tumbling'."
            )

        # Load official project pipeline parameters to guarantee exact training consistency
        pipeline_cfg_path = self.repo_root / "configs/pipeline.yaml"
        default_window_s = 2.0
        default_min_samples = 29
        if pipeline_cfg_path.exists():
            try:
                p_cfg = load_yaml_config(pipeline_cfg_path)
                default_window_s = float(p_cfg.preprocessing.window_seconds)
                nom_rate = float(p_cfg.acquisition.nominal_rate_hz)
                frac = float(p_cfg.preprocessing.min_window_sample_rate_fraction)
                min_abs = int(p_cfg.preprocessing.min_absolute_samples_per_window)
                default_min_samples = max(min_abs, int(frac * nom_rate * default_window_s))
            except (KeyError, AttributeError, ValueError, OSError):
                pass


        self.window_seconds = float(
            window_seconds if window_seconds is not None else default_window_s
        )
        self.min_samples = int(
            min_samples if min_samples is not None else default_min_samples
        )


        # 1. Resolve and load the best model pipeline
        self.model_name, self.pipeline, self.model_card = self._load_model(model_name)

        # 2. Load valid subcarrier indices and feature column names
        self.raw_indices, self.feature_names = self._load_subcarrier_mapping()

        # 3. Serial acquisition state
        self.ser: serial.Serial | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # Buffer stores tuples: (timestamp, amplitude_vector_162, rssi, noise_floor)
        self._buffer: deque[tuple[float, np.ndarray, float | None, float | None]] = deque(maxlen=2000)

        # Telemetry metrics
        self.total_packets_received = 0
        self.total_packets_dropped = 0
        self.latest_rssi: float | None = None
        self.latest_noise_floor: float | None = None
        self.latest_packet_id: int | None = None
        self.current_rate_hz: float = 0.0
        self._recent_timestamps: deque[float] = deque(maxlen=200)

        # Tumbling window tracking state
        self._tumbling_window_start: float | None = None
        self._last_result: dict[str, Any] | None = None

        # Prediction statistics
        self.total_inferences = 0
        self.occupied_count = 0
        self.empty_count = 0


    def _load_model(self, model_name: str | None) -> tuple[str, Any, dict[str, Any]]:
        """Load trained pipeline bundle (auto-resolving best model per modality if unspecified)."""
        resolved_name = model_name

        # 1. Resolve light modality requests to designated best light model
        if resolved_name in ["reduced", "optimal_reduced", "optimal", "optimal_reduced_model", "light"]:
            opt_json = self.repo_root / "reports/logs/optimal_features.json"
            best_light = None
            if opt_json.exists():
                try:
                    with open(opt_json, "r", encoding="utf-8") as f:
                        opt_meta = json.load(f)
                        best_light = opt_meta.get("best_light_model")
                except (json.JSONDecodeError, OSError):
                    pass
            resolved_name = best_light or "gradient_boosting_light"

        # 2. Resolve standard modality requests to designated best standard model
        if not resolved_name or resolved_name in ["default", "standard", "full"]:
            eval_report = self.repo_root / "reports/logs/evaluation_report.json"
            best_standard = None
            if eval_report.exists():
                try:
                    with open(eval_report, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        best_standard = data.get("best_model")
                except (json.JSONDecodeError, OSError):
                    pass
            resolved_name = best_standard or "mlp"

        # 3. Handle model architecture aliases
        alias_map = {
            "rf": "random_forest",
            "rf_light": "random_forest_light",
            "rf_l": "random_forest_light",
            "gb": "gradient_boosting",
            "gb_light": "gradient_boosting_light",
            "gb_l": "gradient_boosting_light",
            "mlp_l": "mlp_light",
            "svm_l": "svm_light",
        }
        if resolved_name in alias_map:
            resolved_name = alias_map[resolved_name]

        bundle_dir = self.repo_root / f"models/registry/{resolved_name}_bundle"
        if not bundle_dir.exists():
            # Check models directory fallback
            flat_candidates = [
                self.repo_root / f"models/{resolved_name}.pkl",
                self.repo_root / f"models/{resolved_name}_model.pkl",
            ]
            flat_file = next((f for f in flat_candidates if f.exists()), None)
            if flat_file:
                import joblib
                pipeline = joblib.load(flat_file)
                card = {"model_name": resolved_name, "metadata": {}}
                opt_json = self.repo_root / "reports/logs/optimal_features.json"
                if opt_json.exists() and ("reduced" in resolved_name or "light" in resolved_name):
                    with open(opt_json, "r", encoding="utf-8") as f:
                        opt_meta = json.load(f)
                        card["metadata"] = {
                            "is_reduced": True,
                            "is_light": True,
                            "raw_subcarrier_indices": opt_meta.get("raw_subcarrier_indices", []),
                            "feature_columns": opt_meta.get("optimal_feature_columns", []),
                            "optimal_subcarriers": opt_meta.get("optimal_subcarriers", []),
                            "n_subcarriers": opt_meta.get("num_subcarriers", 5),
                            "n_features": opt_meta.get("num_features", 20),
                        }
                return resolved_name, pipeline, card

            raise FileNotFoundError(f"Bundle directory does not exist: {bundle_dir}")

        pipeline, card = load_model_bundle(bundle_dir)
        return resolved_name, pipeline, card

    def _load_subcarrier_mapping(self) -> tuple[np.ndarray, list[str]]:
        """Load valid subcarrier indices mapping and feature column headers."""
        metadata = self.model_card.get("metadata", {})
        if metadata.get("is_reduced") or ("raw_subcarrier_indices" in metadata and "feature_columns" in metadata):
            raw_indices = np.array(metadata["raw_subcarrier_indices"], dtype=int)
            feature_names = list(metadata["feature_columns"])
            return raw_indices, feature_names

        candidates = [
            self.repo_root / "data/03_processed/valid_subcarrier_mapping.csv",
            self.repo_root / "outputs/pipeline_v1/valid_subcarrier_mapping_v1.csv",
        ]
        mapping_file = next((f for f in candidates if f.exists()), None)
        if mapping_file:
            df = pd.read_csv(mapping_file)
            col = "raw_complex_subcarrier_index" if "raw_complex_subcarrier_index" in df.columns else "raw_subcarrier_index"
            raw_indices = df[col].to_numpy(dtype=int)
        else:
            # Fallback to feature columns count from model card
            feat_cols = self.model_card.get("metadata", {}).get("feature_columns", [])
            n_subcarriers = len(feat_cols) // 4 if feat_cols else 162
            raw_indices = np.arange(6, 6 + n_subcarriers, dtype=int)

        feature_names = make_feature_columns(len(raw_indices))
        return raw_indices, feature_names

    def start(self) -> None:
        """Open serial port and start background reader thread."""
        if self._running:
            return

        self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
        self.ser.reset_input_buffer()
        self._running = True

        self._thread = threading.Thread(target=self._reader_loop, daemon=True, name="CSI-SerialWorker")
        self._thread.start()

    def stop(self) -> None:
        """Stop background acquisition and close serial connection."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except (serial.SerialException, OSError):
                pass

    def _reader_loop(self) -> None:
        """Continuous background serial acquisition thread."""
        while self._running:
            try:
                if not self.ser or not self.ser.is_open:
                    time.sleep(0.1)
                    continue

                line = self.ser.readline().decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("CSI_DATA,"):
                    continue

                now = time.time()
                b_start = line.find("[")
                b_end = line.rfind("]")
                if b_start == -1 or b_end == -1 or b_end <= b_start:
                    continue

                # Parse metadata prefix: CSI_DATA,id,mac,rssi,...,len,first_word,"[...]
                prefix = line[:b_start].rstrip(', "')
                parts = prefix.split(",")
                rssi = float(parts[3]) if len(parts) > 3 and parts[3].lstrip("-").isdigit() else None
                noise_floor = (
                    float(parts[14]) if len(parts) > 14 and parts[14].lstrip("-").isdigit() else None
                )
                packet_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

                # Fast numpy parse of CSI payload
                raw = np.fromstring(line[b_start + 1 : b_end], sep=",", dtype=np.float64)
                if len(raw) != 384:
                    self.total_packets_dropped += 1
                    continue

                # Convert interleaved I/Q to complex amplitudes
                complex_vec = raw_iq_to_complex(raw)
                amp_vec = np.abs(complex_vec)[self.raw_indices]

                # Update state safely
                with self._lock:
                    self._buffer.append((now, amp_vec, rssi, noise_floor))
                    self._recent_timestamps.append(now)
                    self.total_packets_received += 1
                    self.latest_rssi = rssi
                    self.latest_noise_floor = noise_floor
                    self.latest_packet_id = packet_id

                    # Compute packet arrival rate over last 2 seconds
                    cutoff = now - 2.0
                    while self._recent_timestamps and self._recent_timestamps[0] < cutoff:
                        self._recent_timestamps.popleft()

                    count = len(self._recent_timestamps)
                    span = (
                        (self._recent_timestamps[-1] - self._recent_timestamps[0])
                        if count > 1
                        else 0.0
                    )
                    self.current_rate_hz = (count - 1) / span if span > 0.05 else 0.0

            except serial.SerialException as err:
                self._last_error = f"SerialException: {err}"
                time.sleep(0.5)
            except Exception as err:  # noqa: BLE001
                self._last_error = f"Exception: {type(err).__name__}: {err}"
                time.sleep(0.01)

    def predict_latest(self) -> dict[str, Any]:
        """Perform feature extraction and prediction based on 2.0-second window logic."""
        now = time.time()

        with self._lock:
            # Purge samples older than 3x window
            old_cutoff = now - (self.window_seconds * 3.0)
            while self._buffer and self._buffer[0][0] < old_cutoff:
                self._buffer.popleft()

            buffer_snapshot = list(self._buffer)
            current_hz = self.current_rate_hz
            rssi = self.latest_rssi
            noise = self.latest_noise_floor
            total_rx = self.total_packets_received

        if not buffer_snapshot:
            return {
                "status": "buffering",
                "sample_count": 0,
                "target_samples": self.min_samples,
                "progress_ratio": 0.0,
                "time_span": 0.0,
                "target_span": self.window_seconds,
                "window_mode": self.window_mode,
                "packet_rate_hz": current_hz,
                "rssi": rssi,
                "noise_floor": noise,
                "total_packets": total_rx,
                "timestamp": now,
            }

        if self.window_mode == "tumbling":
            if self._tumbling_window_start is None:
                self._tumbling_window_start = buffer_snapshot[0][0]

            elapsed_in_window = now - self._tumbling_window_start
            window_end = self._tumbling_window_start + self.window_seconds

            # Still accumulating current discrete window
            if elapsed_in_window < self.window_seconds:
                current_window_samples = [
                    item
                    for item in buffer_snapshot
                    if self._tumbling_window_start <= item[0] < window_end
                ]
                return {
                    "status": "buffering",
                    "window_mode": "tumbling",
                    "sample_count": len(current_window_samples),
                    "target_samples": self.min_samples,
                    "progress_ratio": min(1.0, elapsed_in_window / self.window_seconds),
                    "time_span": elapsed_in_window,
                    "target_span": self.window_seconds,
                    "packet_rate_hz": current_hz,
                    "rssi": rssi,
                    "noise_floor": noise,
                    "total_packets": total_rx,
                    "last_result": self._last_result,
                    "timestamp": now,
                }

            # Discrete window completed!
            win_start = self._tumbling_window_start
            win_samples = [
                item for item in buffer_snapshot if win_start <= item[0] < window_end
            ]

            # Advance window start
            self._tumbling_window_start = window_end
            if now - self._tumbling_window_start > self.window_seconds * 2:
                self._tumbling_window_start = now

            if len(win_samples) < self.min_samples:
                return {
                    "status": "dropped",
                    "window_mode": "tumbling",
                    "sample_count": len(win_samples),
                    "target_samples": self.min_samples,
                    "progress_ratio": 1.0,
                    "time_span": self.window_seconds,
                    "target_span": self.window_seconds,
                    "packet_rate_hz": current_hz,
                    "rssi": rssi,
                    "noise_floor": noise,
                    "total_packets": total_rx,
                    "last_result": self._last_result,
                    "timestamp": now,
                }

            res = self._compute_inference_result(
                win_samples, current_hz, rssi, noise, total_rx, now, "tumbling"
            )
            self._last_result = res
            return res

        # Sliding window mode
        cutoff = now - self.window_seconds
        window_samples = [item for item in buffer_snapshot if item[0] >= cutoff]

        sample_count = len(window_samples)
        time_span = (
            (window_samples[-1][0] - window_samples[0][0])
            if sample_count > 1
            else 0.0
        )
        buffer_history = now - buffer_snapshot[0][0]

        # Enforce full 2.0-second temporal coverage (at least 85% of duration and min_samples)
        is_buffered = (
            buffer_history >= (self.window_seconds * 0.9)
            and time_span >= (self.window_seconds * 0.85)
            and sample_count >= self.min_samples
        )

        if not is_buffered:
            progress = min(
                1.0,
                max(
                    buffer_history / self.window_seconds,
                    sample_count / (self.min_samples * 2),
                ),
            )
            return {
                "status": "buffering",
                "window_mode": "sliding",
                "sample_count": sample_count,
                "target_samples": self.min_samples,
                "progress_ratio": progress,
                "time_span": time_span,
                "target_span": self.window_seconds,
                "packet_rate_hz": current_hz,
                "rssi": rssi,
                "noise_floor": noise,
                "total_packets": total_rx,
                "timestamp": now,
            }

        return self._compute_inference_result(
            window_samples, current_hz, rssi, noise, total_rx, now, "sliding"
        )

    def _compute_inference_result(
        self,
        samples: list[tuple[float, np.ndarray, float | None, float | None]],
        current_hz: float,
        rssi: float | None,
        noise: float | None,
        total_rx: int,
        timestamp: float,
        mode: str,
    ) -> dict[str, Any]:
        """Extract statistical features and evaluate model on a validated window."""
        amp_matrix = np.vstack([item[1] for item in samples])
        time_span = (
            float(samples[-1][0] - samples[0][0])
            if len(samples) > 1
            else self.window_seconds
        )

        feats = extract_official_features(amp_matrix).reshape(1, -1)
        feat_df = pd.DataFrame(feats, columns=self.feature_names)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pred = int(self.pipeline.predict(feat_df)[0])
            if hasattr(self.pipeline, "predict_proba"):
                probs = self.pipeline.predict_proba(feat_df)[0]
                prob_empty = float(probs[0])
                prob_occupied = float(probs[1])
            else:
                prob_occupied = 1.0 if pred == 1 else 0.0
                prob_empty = 1.0 - prob_occupied

        final_prediction = 1 if prob_occupied >= self.threshold else 0
        final_label = "occupied" if final_prediction == 1 else "empty"
        confidence = prob_occupied if final_prediction == 1 else prob_empty

        disturbance = float(np.mean(np.var(amp_matrix, axis=0, ddof=1)))

        self.total_inferences += 1
        if final_prediction == 1:
            self.occupied_count += 1
        else:
            self.empty_count += 1

        snr = (rssi - noise) if (rssi is not None and noise is not None) else None

        return {
            "status": "ready",
            "prediction": final_prediction,
            "label": final_label,
            "prob_empty": prob_empty,
            "prob_occupied": prob_occupied,
            "confidence": confidence,
            "disturbance": disturbance,
            "sample_count": len(samples),
            "window_seconds": self.window_seconds,
            "actual_span_s": time_span,
            "window_mode": mode,
            "packet_rate_hz": current_hz,
            "rssi": rssi,
            "noise_floor": noise,
            "snr_db": snr,
            "total_packets": total_rx,
            "timestamp": timestamp,
        }

