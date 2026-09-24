# Dataset and Experimental Sessions

This document inventories the experimental campaigns, spatial presence topologies, physical conditions, and automated quality validation criteria across the repository.

---

## 1. Experimental Campaigns Overview

Three acquisition campaigns were recorded in the residential bedroom environment:

1. **First Test Campaign (2026-04-05)**: Proof-of-concept recordings (Sessions PLA, PLB) stored in [`data/01_raw/first_test/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/first_test/), analyzed in [eda_first_test.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb).
2. **Pilot Campaign (2026-05-02 to 2026-05-03)**: Initial controlled protocol (Sessions A through F) stored in [`data/01_raw/pilot/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/pilot/), analyzed in [eda_pilot.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb) and [pipeline_v0.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb).
3. **Main Campaign (2026-09-22 to 2026-09-23)**: Definitive multi-position and stability campaign (Sessions G through M) stored in [`data/01_raw/main/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/main/), analyzed in [eda_main.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb) and [pipeline_v1.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb).

---

## 2. Spatial Presence Topologies

During occupied recordings, human subjects remained standing motionless (or pacing in Session E) in specific positions relative to the 2.0 m North-South Line-of-Sight (LoS) path ($x = 1.45\text{ m}$ from West wall, tripod height 1.2 m):

```
                      [ NORTH WALL: Window ]
      ------------------------------------------------------
      |                                                    |
      |                 [RX Node] (AP, y=1.14m)            |
      |                     |                              |
      |               [P3] On-LoS (near RX, ~30cm)         |
      |                     |                              |
      |   [P1] Off-LoS West | [P4] Off-LoS East            |
WEST  |   (~30cm West)      | (~30cm East)                 |  EAST
WALL  |                     |                              |  WALL
[MDF  |             [Center / LoS Midpoint]                | [Desk /
Ward- |             (Pilot Sessions D & E)                 |  Work-
robe] |                     |                              | station]
      |               [P2] On-LoS (near TX, ~30cm)         |
      |                     |                              |
      |                 [TX Node] (STA, y=3.08m)           |
      |                                                    |
      |                      [ Bed ]                       |
      ------------------------------------------------------
                       [ SOUTH WALL: Door ]
```

### Position Descriptions

- **On-LoS Near TX (P2 - Session I)**: Subject standing motionless directly on the LoS beam, ~30 cm from TX ($y \approx 2.78\text{ m}$). Causes severe direct-path shadowing.
- **On-LoS Near RX (P3 - Session K)**: Subject standing motionless directly on the LoS beam, ~30 cm from RX ($y \approx 1.44\text{ m}$). Causes strong near-antenna scattering.
- **Off-LoS West (P1 - Session H)**: Subject standing motionless ~30 cm West of LoS ($x \approx 1.15\text{ m}$). Direct LoS unblocked; sensed via secondary reflections.
- **Off-LoS East (P4 - Session M)**: Subject standing motionless ~30 cm East of LoS ($x \approx 1.75\text{ m}$). Direct LoS unblocked; multipath disturbance dominates.
- **Static Standing (Occupied Still - Session D)**: Subject standing motionless at center mark ($x = 1.45\text{ m}, y = 2.11\text{ m}$).
- **Dynamic Movement (Occupied Moving - Session E)**: Pacing and movement within $\pm 0.30\text{ m}$ of center mark.
- **Extended Empty Baseline (Session J)**: 31.5-minute empty recording (55,075 samples) verifying long-term environmental drift.

---

## 3. Automated Quality Validation Criteria

Sessions are evaluated against four criteria prior to pipeline ingestion:
1. **Packet Loss**: $< 5.0\%$.
2. **Effective Sampling Rate**: Within $\pm 10\%$ of nominal 30 Hz ($27.0\text{ Hz} \le f_s \le 33.0\text{ Hz}$).
3. **RSSI Stability**: Standard deviation across session $< 5.0\text{ dBm}$.
4. **Valid Subcarrier Count**: $\ge 40$ non-dead subcarriers (out of 192).

---

## 4. Master Session Inventory and Status

| Session ID | Campaign | Condition | Date / Time (Local BRT) | Duration | Packets | Valid SCs | Eff. Rate | Status |
|---|---|---|---|---|---|---|---|---|
| PLA | First Test | `empty` | 2026-04-05 18:47 | 60.0 s | 1,735 | 166 | 29.41 Hz | Excluded (sanity check) |
| PLB | First Test | `occupied_still` | 2026-04-05 18:50 | 60.0 s | 1,736 | 161 | 29.42 Hz | Excluded (sanity check) |
| A | Pilot | `empty` | 2026-05-02 12:01 | 690.0 s | 19,755 | 166 | 28.63 Hz | INVALID (t1/t2 timing mismatch in metadata) |
| B | Pilot | `empty` | 2026-05-02 12:24 | 690.0 s | 19,715 | 166 | 28.57 Hz | INVALID (t1 timing mismatch in metadata) |
| C | Pilot | `empty` | 2026-05-02 12:41 | 690.0 s | 19,589 | 166 | 28.39 Hz | VALID |
| D | Pilot | `occupied_still` | 2026-05-02 13:18 | 690.0 s | 18,048 | 166 | 26.16 Hz | VALID (pilot baseline) |
| E | Pilot | `occupied_moving` | 2026-05-02 14:05 | 690.0 s | 18,610 | 166 | 26.97 Hz | VALID (pilot movement) |
| F | Pilot | `empty` | 2026-05-03 15:39 | 690.0 s | 20,239 | 166 | 29.33 Hz | VALID |
| G | Main | `empty` | 2026-09-22 17:03 | 690.0 s | 20,151 | 166 | 29.21 Hz | VALID |
| H | Main | `occupied_p1_still` | 2026-09-22 19:11 | 690.0 s | 19,984 | 166 | 28.96 Hz | VALID |
| I | Main | `occupied_p2_still` | 2026-09-22 19:33 | 690.0 s | 19,911 | 166 | 28.86 Hz | VALID |
| J | Main | `empty` (extended) | 2026-09-22 20:01 | 1,890.0 s | 55,075 | 166 | 29.14 Hz | VALID |
| K | Main | `occupied_p3_still` | 2026-09-22 23:53 | 690.0 s | 20,050 | 166 | 29.06 Hz | VALID |
| L | Main | `empty` | 2026-09-23 00:11 | 690.0 s | 20,236 | 166 | 29.33 Hz | VALID |
| M | Main | `occupied_p4_still` | 2026-09-23 00:31 | 690.0 s | 20,171 | 166 | 29.23 Hz | VALID |

> **Note on Sessions A and B**: Both exhibited intact RF reception (~19.7k packets, ~28.6 Hz), but were invalidated due to human timing marker discrepancies in the metadata sidecar ($t_1$/$t_2$ mismatch relative to planned recording intervals).

### Downstream Eligibility Summary

- **Total Sessions Discovered**: 15 recordings.
- **Valid Sessions Ingested**: 11 sessions (Pilot C, D, E, F + Main G, H, I, J, K, L, M).
- **Total Valid Raw Packets**: 252,064 CSI packets.
- **Total Valid Window Segments (2.0 s)**: 3,889 non-overlapping windows.
- **Binary Class Balance**: Class 0 (`empty`): 2,095 windows (53.87%), Class 1 (`occupied`): 1,794 windows (46.13%).
