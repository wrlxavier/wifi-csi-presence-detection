# Hardware and Acquisition Protocol

This document details the physical sensing environment, hardware setup, firmware architecture, serial acquisition pipeline, and ground-truth logging protocols established in [csi_collector_v2.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb).

---

## 1. Physical Sensing Environment

Data acquisition was conducted in a controlled residential bedroom at UFMG (2026/2):

- **Room Dimensions**: 3.40 m (East-West) x 3.45 m (North-South) with a ceiling height of 2.85 m.
- **Structural Materials**: Brick perimeter walls, smooth plaster interior finish, and concrete slab ceiling.
- **Apertures**: Single plywood interior door (closed during active sessions) and iron-frame glass window (closed, blinds drawn to prevent external multipath variations).
- **Notable Furnishings**:
  - MDF wardrobe along the West wall.
  - Wall-mounted mirror.
  - Bed positioned centrally.
  - Study desk and workstation along the East wall.
  - Two wall-mounted book niches.

This environment presents rich multipath propagation typical of residential smart home and healthcare monitoring deployments.

---

## 2. Hardware Architecture and RF Configuration

The sensing system utilizes two Espressif ESP32-S3 microcontrollers:

- **Transmitter (TX Node)**:
  - Role: Station (STA) mode.
  - Function: Injects periodic frames addressed to the receiver node.
  - Transmission Rate: 30 Hz nominal packet frequency (33.33 ms packet interval).
- **Receiver (RX Node)**:
  - Role: Access Point (AP) mode.
  - Function: Captures physical layer packets, extracts Channel State Information (CSI) hardware buffers via ESP-IDF CSI callbacks, and transmits them over USB-UART to the host workstation.

### Physical Layer (PHY) Settings

| Parameter | Configuration | Technical Rationale |
|---|---|---|
| Protocol | ESP-NOW (connectionless 802.11n) | Eliminates Wi-Fi association overhead and beacon jitter |
| Channel | Channel 11 (2.462 GHz) | Selected for minimal 2.4 GHz co-channel interference |
| Bandwidth | HT40 (40 MHz) | Yields 192 OFDM subcarriers for fine frequency resolution |
| Modulation | 802.11n MCS 0 to MCS 7 | High-order OFDM symbol structure |
| Raw Payload | 384 bytes (Interleaved I/Q) | 192 complex numbers: `[real_0, imag_0, real_1, ...]` |

---

## 3. High-Speed Serial Acquisition

The receiver node communicates with the host machine via high-speed UART:

- **Baud Rate**: 921,600 baud.
- **Port Identification**: `/dev/ttyUSB0` (Linux workstation).
- **Host Time-stamping**: Each packet is tagged on arrival with sub-millisecond host timestamps (`timestamp_host`) using `datetime.now(timezone.utc).isoformat()`.

### Raw Serial Frame Header

The incoming CSV serial stream follows this standardized 26-column header:

```
timestamp_host,type,id,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_state,len,first_word,data
```

Key columns monitored during acquisition:
- `timestamp_host`: Ground truth reference timestamp on host computer.
- `rssi`: Received Signal Strength Indicator (dBm).
- `len`: Length of raw CSI byte stream (expected: 384 bytes for HT40).
- `data`: Bracket-delimited JSON-like array of 384 signed integer values.

---

## 4. Dual-File Ground Truth Protocol

Every recording session generates exactly two synchronized artifacts:
1. `session_<ID>_<label>_<YYYYMMDD_HHMM>.csv`: The complete raw packet log.
2. `session_<ID>_<label>_<YYYYMMDD_HHMM>_meta.json`: Experimental metadata and timing bounds.

### Four-Stage Timing Lifecycle

To avoid capturing operator transition artifacts (e.g. walking into the room or closing the door), each recording adheres to a strict 4-stage timeline:

1. **`t0_recording_start`**: Serial port opens; background recording starts. A countdown of 15 seconds allows the experimenter to leave or enter the room.
2. **`t1_condition_start`**: Physical condition stabilizes (door closed, subject seated and still). Active sensing interval begins.
3. **`t2_condition_end`**: Condition ends (subject prepares to stand or operator enters). Active sensing interval concludes.
4. **`t3_recording_stop`**: Serial port closes and file handles flush.

```
Time:   t0 ----------------> t1 ====================> t2 ----------------> t3
Stage:  [Countdown / Buffer] [  ACTIVE VALID WINDOW  ] [Buffer / Exit]
Action: Discarded            Extracted for Features    Discarded
```

### Midnight Date-Rollover Handling

For overnight sessions (such as Session K and Session L), the active interval $[t_1, t_2]$ may cross midnight UTC. The metadata parsing module in [`wifi_csi.parsing.loader`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/parsing/loader.py) automatically detects cases where $t_2 < t_1$ and advances $t_2$ by +1 day:

```python
if t2_condition_end < t1_condition_start:
    t2_condition_end += timedelta(days=1)
```

---

## 5. Metadata Schema Reference

The companion JSON file structure is illustrated below:

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
      "tx": {"role": "STA", "x_m": 0.5, "y_m": 1.72, "z_m": 1.0},
      "rx": {"role": "AP", "x_m": 2.5, "y_m": 1.72, "z_m": 1.0},
      "distance_m": 2.0
    },
    "rf": {
      "channel": 11,
      "bandwidth_mhz": 40,
      "subcarriers": 192,
      "nominal_rate_hz": 30
    }
  },
  "timing": {
    "t0_recording_start": "2026-09-23T00:26:10.123456+00:00",
    "t1_condition_start": "2026-09-23T00:27:10.000000+00:00",
    "t2_condition_end": "2026-09-23T00:37:10.000000+00:00",
    "t3_recording_stop": "2026-09-23T00:37:45.654321+00:00",
    "status": "VALID",
    "invalidation_reason": ""
  }
}
```

This strict ground-truth architecture guarantees zero label ambiguity and ensures that models are trained purely on stable physical states.
