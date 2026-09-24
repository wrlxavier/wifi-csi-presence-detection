"""Serial port reader with signal handling and buffered writing."""

from pathlib import Path
from datetime import datetime, timezone
import time
import serial


class CSISerialReader:
    """Manages serial connection to ESP32-S3 RX node for CSI logging."""

    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 921600, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: serial.Serial | None = None

    def connect(self) -> None:
        """Open serial port connection."""
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.ser.reset_input_buffer()

    def disconnect(self) -> None:
        """Close serial port connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def capture_session(
        self,
        output_csv: str | Path,
        duration_s: float,
        callback: Any = None,
    ) -> dict[str, Any]:
        """Capture CSI lines from serial and save to CSV file.

        Parameters
        ----------
        output_csv : str or Path
            Target CSV file.
        duration_s : float
            Recording duration in seconds.
        callback : callable, optional
            Function called periodically with (samples_captured, elapsed_s).

        Returns
        -------
        dict
            Capture summary metrics (sample count, duration, t0, t3).
        """
        output_csv = Path(output_csv)
        output_csv.parent.mkdir(parents=True, exist_ok=True)

        if not self.ser or not self.ser.is_open:
            self.connect()

        t0 = datetime.now(timezone.utc)
        start_time = time.time()
        sample_count = 0

        with open(output_csv, "w", encoding="utf-8") as f:
            header_written = False
            while (time.time() - start_time) < duration_s:
                line = self.ser.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                if line.startswith("type,") or "CSI_DATA" in line:
                    if not header_written and "timestamp_host" in line:
                        f.write(line + "\n")
                        header_written = True
                        continue
                    f.write(line + "\n")
                    sample_count += 1
                    if callback and sample_count % 100 == 0:
                        callback(sample_count, time.time() - start_time)

        t3 = datetime.now(timezone.utc)
        return {
            "samples_captured": sample_count,
            "duration_s": time.time() - start_time,
            "t0_utc": t0.isoformat(),
            "t3_utc": t3.isoformat(),
        }
