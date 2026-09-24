# Hardware and Acquisition Protocol

This document details the sensing environment, hardware setup, RF configuration, serial acquisition pipeline, and ground-truth protocols established in [csi_collector_v2.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb).

---

## 1. Physical Sensing Environment

Data acquisition was conducted in a controlled residential bedroom at UFMG:

- **Dimensions**: 3.40 m (East-West) × 3.45 m (North-South), ceiling height 2.85 m.
- **Boundaries**: Brick walls, concrete ceiling, closed plywood door, closed window with blinds.
- **Furnishings**: MDF wardrobe (West wall), study desk (East wall), centrally placed bed.

---

## 2. Hardware Architecture and RF Configuration

The sensing link uses two Espressif ESP32-S3 microcontrollers:

- **Transmitter (TX Node)**: STA mode, injects periodic frames at 30 Hz nominal rate.
- **Receiver (RX Node)**: AP mode, captures frames, extracts CSI buffers via ESP-IDF callbacks, and streams via USB-UART.

### Physical Layer (PHY) Settings

| Parameter | Configuration | Rationale |
|---|---|---|
| Protocol | ESP-NOW (connectionless 802.11n) | Eliminates Wi-Fi association overhead and beacon jitter |
| Channel | Channel 11 (2.462 GHz) | Minimal 2.4 GHz co-channel interference |
| Bandwidth | HT40 (40 MHz) | 192 OFDM subcarriers for fine frequency resolution |
| Modulation | 802.11n MCS 0 to MCS 7 | High-order OFDM symbol structure |
| Raw Payload | 384 bytes (Interleaved Q/I) | 192 complex numbers: `[imag_0, real_0, imag_1, real_1, ...]` (ESP-IDF format) |

---

## 3. High-Speed Serial Acquisition

- **Baud Rate**: 921,600 baud (`/dev/ttyUSB0` on Linux).
- **Time-stamping**: Sub-millisecond UTC host timestamp (`timestamp_host`) attached on packet arrival.
- **Payload**: 26 CSV columns including `rssi`, `len` (384 bytes), and `data` (bracketed array of 384 signed integers).

---

## 4. Ground Truth & Session Protocol

Each session generates two synchronized files:
1. `session_<ID>_<label>_<YYYYMMDD_HHMM>.csv`: Raw packet stream.
2. `session_<ID>_<label>_<YYYYMMDD_HHMM>_meta.json`: Experimental metadata and timing bounds.

### Timing Lifecycle

To avoid transient operator motion artifacts, sessions follow a 4-stage lifecycle:

1. **`t0_recording_start`**: Recording begins. A 60-second stabilization window (`STABILIZATION_S = 60`) allows the room to settle with door closed.
2. **`t1_condition_start`**: Active sensing window (`ACTIVE_WINDOW_S = 600`, 10 minutes) begins. Subject remains standing motionless in assigned position.
3. **`t2_condition_end`**: Active sensing ends. A 30-second trailing buffer (`BUFFER_END_S = 30`) begins.
4. **`t3_recording_stop`**: Port closes and files flush (total planned duration: 690 seconds).

```
Time:   t0 ----------------> t1 ====================> t2 ----------------> t3
Stage:  [Stabilization 60s ] [ ACTIVE WINDOW 600s ]   [Buffer End 30s]
Action: Discarded            Extracted for Features   Discarded
```

### Midnight Date-Rollover Handling

For sessions crossing UTC midnight ($t_2 < t_1$), [`get_active_interval_from_metadata`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/parsing/metadata_parser.py#L61-L73) in [`wifi_csi.parsing.metadata_parser`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/parsing/metadata_parser.py) automatically advances $t_2$ by +1 day (`end = end + pd.Timedelta(days=1)`).

---

## 5. Metadata Schema Reference

```json
{
  "session_id": "M",
  "label": "occupied_p4_still",
  "setup": {
    "room": {
      "dimensions_m": {"east_west": 3.40, "north_south": 3.45, "ceiling_height": 2.85},
      "door_material": "plywood",
      "window_material": "iron and glass"
    },
    "nodes": {
      "tx": {
        "role": "STA (ICMP transmitter)",
        "device": "ESP32-S3-DevKitC-1",
        "tripod_height_m": 1.2,
        "pos_x_from_west_wall_m": 1.45,
        "pos_y_from_north_wall_m": 3.08,
        "mac": "1a:00:00:00:00:00"
      },
      "rx": {
        "role": "AP (CSI receiver)",
        "device": "ESP32-S3-DevKitC-1",
        "tripod_height_m": 1.2,
        "pos_x_from_west_wall_m": 1.45,
        "pos_y_from_north_wall_m": 1.14,
        "mac": "1c:db:d4:9d:93:dc",
        "serial_port": "/dev/ttyUSB0",
        "baud_rate": 921600
      },
      "tx_rx_los_distance_m": 2.0,
      "tx_rx_axis": "parallel to north-south axis"
    },
    "rf": {
      "channel": 11,
      "bandwidth_mhz": 40,
      "subcarriers": 192,
      "nominal_rate_hz": 30
    }
  },
  "timing": {
    "t0_recording_start": "2026-09-23T00:31:05.000000-03:00",
    "t1_condition_start": "2026-09-23T00:32:05.000000-03:00",
    "t2_condition_end": "2026-09-23T00:42:05.000000-03:00",
    "t3_recording_stop": "2026-09-23T00:42:35.000000-03:00",
    "status": "VALID",
    "invalidation_reason": ""
  }
}
```
