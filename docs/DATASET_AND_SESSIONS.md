# Dataset and Experimental Sessions

This document provides a comprehensive inventory of all data collection campaigns, spatial presence topologies, physical conditions, and automated quality validation criteria across the repository.

---

## 1. Experimental Campaigns Overview

The repository incorporates three distinct experimental campaigns recorded in the residential bedroom environment:

1. **First Test Campaign (2026-04-05)**:
   - Initial proof-of-concept recordings (Sessions PLA and PLB) testing firmware stability and serial packet framing.
   - Stored in [`data/01_raw/first_test/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/first_test/).
   - Analyzed in [eda_first_test.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb).

2. **Pilot Campaign (2026-05-02 to 2026-05-03)**:
   - First controlled protocol collection (Sessions A through F) evaluating empty baseline, static sitting, and active walking.
   - Stored in [`data/01_raw/pilot/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/pilot/).
   - Analyzed in [eda_pilot.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb) and [pipeline_v0.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb).

3. **Main Campaign (2026-09-22 to 2026-09-23)**:
   - Definitive multi-position and temporal stability campaign (Sessions G through M).
   - Stored in [`data/01_raw/main/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/main/).
   - Analyzed in [eda_main.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb) and [pipeline_v1.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb).

---

## 2. Spatial Presence Topologies

During occupied sessions, human subjects were positioned according to specific spatial configurations relative to the 2.0-meter Direct Line-of-Sight (LoS) path between TX and RX nodes:

```
                  [ NORTH WALL: Window ]
      ------------------------------------------------
      |                                              |
      |   [P1] Off-LoS West          [P4] Off-LoS    |
      |   (dx=1.0m, dy=-0.3m)        (dx=1.0m, dy=+0.3m)|
      |                                              |
WEST  |   [TX Node] === LoS Beam === [RX Node]       |  EAST
WALL  |   (STA)                       (AP)           |  WALL
      |         \                   /                |
      |          [P2] On-LoS     [P3] On-LoS         |
      |          (near TX)       (near RX)           |
      |                                              |
      |   [ Bed ]                     [ Workstation ]|
      ------------------------------------------------
                  [ SOUTH WALL: Door ]
```

### Detailed Position Descriptions

- **On-LoS Near TX (P2 - Session I)**:
  - Subject seated directly along the line connecting TX and RX, approximately 0.75 m from the TX node.
  - Causes significant direct-path attenuation and deep multipath shadow fading.
- **On-LoS Near RX (P3 - Session K)**:
  - Subject seated directly along the line connecting TX and RX, approximately 0.75 m from the RX node.
  - Causes strong scattering into the receiving antenna array with substantial phase disruption.
- **Off-LoS West (P1 - Session H)**:
  - Subject seated 1.0 m from the TX node, offset 30 cm perpendicular to the LoS path toward the West wall.
  - Direct LoS remains largely unshadowed; human presence is sensed entirely through secondary reflected and scattered multipath components.
- **Off-LoS East (P4 - Session M)**:
  - Subject seated 1.0 m from the RX node, offset 30 cm perpendicular to the LoS path toward the East wall.
  - Reflective interactions with room boundaries and furniture dominate the CSI disturbance signature.
- **Dynamic Movement (Occupied Moving - Session E)**:
  - Continuous pacing and arm movements throughout the room to evaluate high-velocity Doppler signatures.
- **Extended Empty Baseline (Session J)**:
  - 31.5-minute uninterrupted empty chamber recording (55,075 samples) verifying long-term environmental drift, temperature stability, and false alarm resistance.

---

## 3. Automated Quality Validation Criteria

Every session undergoes automated validation checks prior to inclusion in the downstream machine learning pipeline:

1. **Packet Loss**: Must be strictly `< 5.0%`.
2. **Effective Sampling Rate**: Must remain within `+/- 10%` of the nominal 30 Hz rate ($27.0\text{ Hz} \le f_s \le 33.0\text{ Hz}$).
3. **RSSI Stability**: Standard deviation of RSSI across the session must be `< 5.0 dBm`.
4. **Valid Subcarrier Count**: Must maintain $\ge 40$ non-dead subcarriers (out of 192).

---

## 4. Master Session Inventory and Status

| Session ID | Campaign | Experimental Condition | Date / Time (UTC) | Duration | Packets | Valid SCs | Eff. Rate | Status |
|---|---|---|---|---|---|---|---|---|
| PLA | First Test | `empty` | 2026-04-05 18:47 | 60.0 s | 1,735 | 166 | 29.41 Hz | Excluded (sanity check) |
| PLB | First Test | `occupied_still` | 2026-04-05 18:50 | 60.0 s | 1,736 | 166 | 29.42 Hz | Excluded (sanity check) |
| A | Pilot | `empty` | 2026-05-02 12:00 | 180.0 s | 3,120 | 148 | 17.33 Hz | INVALID (firmware dropout) |
| B | Pilot | `empty` | 2026-05-02 12:23 | 240.0 s | 4,210 | 152 | 17.54 Hz | INVALID (serial buffer overrun) |
| C | Pilot | `empty` | 2026-05-02 12:40 | 690.0 s | 19,589 | 166 | 28.39 Hz | VALID |
| D | Pilot | `occupied_still` | 2026-05-02 13:17 | 690.0 s | 18,048 | 162 | 26.16 Hz | VALID (pilot restriction) |
| E | Pilot | `occupied_moving` | 2026-05-02 14:04 | 690.0 s | 18,610 | 166 | 26.97 Hz | VALID (pilot restriction) |
| F | Pilot | `empty` | 2026-05-03 15:37 | 690.0 s | 20,240 | 166 | 29.33 Hz | VALID |
| G | Main | `empty` | 2026-09-22 17:01 | 690.0 s | 20,151 | 166 | 29.20 Hz | VALID |
| H | Main | `occupied_p1_still` | 2026-09-22 19:08 | 690.0 s | 19,984 | 166 | 28.96 Hz | VALID |
| I | Main | `occupied_p2_still` | 2026-09-22 19:32 | 690.0 s | 19,911 | 166 | 28.86 Hz | VALID |
| J | Main | `empty` (extended) | 2026-09-22 20:00 | 1,890.0 s | 55,075 | 166 | 29.14 Hz | VALID |
| K | Main | `occupied_p3_still` | 2026-09-22 23:51 | 690.0 s | 20,050 | 165 | 29.06 Hz | VALID |
| L | Main | `empty` | 2026-09-23 00:09 | 690.0 s | 20,236 | 166 | 29.33 Hz | VALID |
| M | Main | `occupied_p4_still` | 2026-09-23 00:26 | 690.0 s | 20,171 | 166 | 29.23 Hz | VALID |

### Downstream Eligibility Summary

- **Total Sessions Discovered**: 15 recordings.
- **Valid Sessions Ingested**: 11 sessions (Pilot C, D, E, F + Main G, H, I, J, K, L, M).
- **Total Valid Raw Packets**: 252,065 CSI packets.
- **Total Valid Window Segments (2.0 s)**: 3,889 non-overlapping windows.
- **Binary Class Balance**:
  - Class 0 (`empty`): 2,095 windows (53.88%).
  - Class 1 (`occupied`): 1,794 windows (46.12%).
