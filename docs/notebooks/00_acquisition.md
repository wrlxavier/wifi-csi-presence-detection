# Data Acquisition (`00_acquisition`)

This document summarizes the core experimental setup, acquisition protocol, and metadata schema implemented in [`csi_collector_v2.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb).

---

## 1. Overview & Objective

The primary objective of the data acquisition stage is to record raw 802.11n Channel State Information (CSI) using commodity ESP32-S3 microcontrollers, producing standardized and synchronized data pairs for each session:
- **Raw CSI Data (`.csv`):** Continuous serial stream of CSI packet frames with host timestamps.
- **Session Metadata (`.json`):** Standardized experiment metadata (Schema Version 2.0) documenting physical setup, ground truth timing, and ambient conditions.

Data artifacts are saved directly under `data/01_raw/<FOLDER_NAME>/`.

---

## 2. Hardware & Radio Configuration

| Parameter | Specification | Notes / Details |
| :--- | :--- | :--- |
| **Nodes** | 2× ESP32-S3-DevKitC-1 | Dedicated transmitter (`csi_send`) and receiver (`csi_recv`) |
| **Link-Layer Protocol** | ESP-NOW (HT40) | Peer-to-peer MAC-layer frames; no IP association or ICMP required |
| **Transmission Rate** | 30 Hz | Periodic frame transmission by the TX node |
| **Frequency / Channel** | 2.4 GHz / Channel 11 | Wi-Fi 802.11n HT40 |
| **Bandwidth** | 40 MHz (HT40) | Captures 802.11n HT40 CSI subcarrier frames |
| **TX Power Supply** | Samsung 5 V / 2 A wall charger | Regulated AC/DC wall adapter |
| **RX Interface & Power** | USB connection (`/dev/ttyUSB0`) | Host-powered serial UART logging at `921600` bps |

---

## 3. Physical Environment & Geometry

- **Room:** Residential bedroom with brick walls and a concrete slab ceiling ($3.40\text{ m}$ East-West $\times$ $3.45\text{ m}$ North-South $\times$ $2.85\text{ m}$ ceiling height).
- **Fixtures:** Plywood door, iron and glass window, wardrobe, desk, bed, and mirror.
- **Node Geometry:**
  - Both nodes mounted on tripods at a height of **1.20 m**.
  - **TX Position:** $(x = 1.45\text{ m}, y = 3.08\text{ m})$ measured from West and North walls.
  - **RX Position:** $(x = 1.45\text{ m}, y = 1.14\text{ m})$ measured from West and North walls.
  - **Line of Sight (LOS):** 2.00 m direct distance, oriented parallel to the North-South axis.
- **Subject Reference Position:** $(x = 1.45\text{ m}, y = 2.11\text{ m})$, positioned along the LOS axis facing North (towards the RX node).

---

## 4. Collection Protocol & Timing Windows

Each acquisition session is conducted under a strict time schedule of **690 seconds** (11.5 minutes) total recording time:

1. **Pre-start Countdown (`15 s`):** Operator leaves the room or assumes position before serial port opens.
2. **Link Stabilization Window ($T_0 \to T_1$, `60 s`):** RF environment settles and serial streaming stabilizes before labeling starts.
3. **Active Labeled Window ($T_1 \to T_2$, `600 s` / 10 min):** Valid ground-truth experimental period for the selected presence label.
4. **Safety Buffer Window ($T_2 \to T_3$, `30 s`):** Tail buffer ensuring the full active window is captured before closing the serial connection.

$$\text{Total Duration} = 60\text{ s (stabilization)} + 600\text{ s (active window)} + 30\text{ s (buffer)} = 690\text{ s}$$

---

## 5. Experimental Classes & Spatial Variations

| Label Key | Type | Description |
| :--- | :--- | :--- |
| `empty` | Baseline | No human presence; operator outside the room with door closed. |
| `occupied_still` | Center | Subject standing motionless at the center mark on the LOS. |
| `occupied_moving` | Dynamic | Subject standing at the center mark with slight movements ($\pm 0.30\text{ m}$). |
| `occupied_p1_still` | Spatial Off-LOS | Subject standing motionless ~30 cm West of the LOS. |
| `occupied_p2_still` | Spatial Near-TX | Subject standing motionless on the LOS, ~30 cm from TX node. |
| `occupied_p3_still` | Spatial Near-RX | Subject standing motionless on the LOS, ~30 cm from RX node. |
| `occupied_p4_still` | Spatial Off-LOS | Subject standing motionless ~30 cm East of the LOS. |

---

## 6. Metadata Schema & Quality Assurance

Every run exports a matching JSON metadata file alongside the CSV with:
- **Session Identification:** Sequential session ID (`A`, `B`, `...`, `ZZZ`), label, and timestamps.
- **Timing Timestamps:** ISO-8601 timestamps for $T_0$ (start), $T_1$ (condition start), $T_2$ (condition end), and $T_3$ (stop).
- **Environmental Context:** Average RSSI (`avg_rssi_dbm`), visible Wi-Fi network count, door state (`closed`/`open`), window state (`closed`/`open`), and ambient notes.
- **Session Validation:** Quality flag (`VALID` or `INVALID`) with explicit invalidation reasons to prevent corrupted or anomalous recordings from entering the training dataset.
