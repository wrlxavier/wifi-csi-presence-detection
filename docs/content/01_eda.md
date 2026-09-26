# Exploratory Data Analysis (`01_eda`)

This document summarizes the core statistical and radio channel characteristics analyzed across the three exploratory notebooks in [`notebooks/01_eda/`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/):
- [`eda_first_test.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb): Hardware communication and parsing validation.
- [`eda_pilot.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb): Controlled pilot collection and protocol benchmarking.
- [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb): Benchmark multi-position dataset analysis.

---

## 1. Overview of EDA Campaigns

| Campaign | Notebook | Sessions | Total Duration | Key Findings & Progression |
| :--- | :--- | :--- | :--- | :--- |
| **First Test** | [`eda_first_test.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb) | A, B (`empty`, `occupied_still`) | 2 min (60 s each) | Verified serial ingestion, 192 raw subcarriers (166 valid), and strong channel separability (Cohen's $d = 25.43$). |
| **Pilot Study** | [`eda_pilot.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb) | C, D, E, F (`empty`, `still`, `moving`, `empty`) | 46 min (4 × 11.5 min) | Sessions C and F passed all criteria; sessions D and E exhibited rate drops ($26.16\text{ Hz}$ and $26.97\text{ Hz}$), establishing the need for refined acquisition controls. |
| **Main Benchmark** | [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb) | G through M (7 sessions) | 100.5 min (175,578 packets) | All 7 sessions passed all criteria; confirmed long-term stationarity (over 7 hours) and demonstrated CSI discriminability over RSSI in off-LoS scenarios. |

---

## 2. Automated Quality Acceptance Criteria

Each session is evaluated against a formal 4-point quality checklist:
1. **Packet Loss:** $< 5.0\%$ estimated loss.
2. **Effective Sampling Rate:** Within $\pm 10\%$ of nominal 30 Hz ($27.0\text{ Hz} \le f_{\text{eff}} \le 33.0\text{ Hz}$).
3. **RSSI Stability:** Standard deviation of RSSI $< 5.0\text{ dBm}$.
4. **Valid Subcarriers:** $\ge 40$ active subcarriers (with non-zero channel response).

---

## 3. Main Benchmark Campaign Summary (`eda_main.ipynb`)

All seven sessions of the main campaign (`G` to `M`) achieved **PASSED** status:

| Session ID | Label / Condition | Samples | Duration (s) | Effective Rate | Jitter $\sigma_{\Delta t}$ | Valid Subcarriers | Mean RSSI (std) | Packet Loss | Quality Verdict |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **G** | `empty` (baseline) | 20,151 | 690.0 | 29.20 Hz | 4.63 ms | 166 / 192 | -26.47 dBm (0.50) | 0.03% | **PASSED** |
| **H** | `occupied_p1_still` (Off-LoS West) | 19,984 | 690.0 | 28.96 Hz | 5.28 ms | 166 / 192 | -26.49 dBm (0.66) | 0.18% | **PASSED** |
| **I** | `occupied_p2_still` (On-LoS Near TX) | 19,911 | 690.0 | 28.86 Hz | 5.79 ms | 166 / 192 | -35.59 dBm (1.02) | 0.18% | **PASSED** |
| **J** | `empty` (extended 31.5 min) | 55,075 | 1889.9 | 29.14 Hz | 4.59 ms | 166 / 192 | -27.00 dBm (0.03) | 0.07% | **PASSED** |
| **K** | `occupied_p3_still` (On-LoS Near RX) | 20,050 | 690.0 | 29.06 Hz | 5.34 ms | 165 / 192 | -36.34 dBm (0.91) | 0.07% | **PASSED** |
| **L** | `empty` (repeat baseline) | 20,236 | 690.0 | 29.33 Hz | 3.93 ms | 166 / 192 | -27.13 dBm (0.33) | 0.01% | **PASSED** |
| **M** | `occupied_p4_still` (Off-LoS East) | 20,171 | 690.0 | 29.23 Hz | 4.37 ms | 166 / 192 | -29.31 dBm (0.52) | 0.01% | **PASSED** |

- **Subcarrier Consistency:** Out of 192 raw OFDM bins, **165 subcarriers** are mutually valid across all 7 sessions (26 dead bins correspond to guard bands and the DC center null).

---

## 4. Key Physical & Statistical Findings

### 4.1 RSSI Inadequacy vs. CSI Sensitivity
- **Line-of-Sight Blockage (Positions P2 & P3):** When the subject stands directly on the LoS axis, average RSSI drops significantly by $\approx 9.1\text{ dBm}$ (Session I, $-35.59\text{ dBm}$) and $\approx 9.9\text{ dBm}$ (Session K, $-36.34\text{ dBm}$) relative to the empty baseline ($-26.47\text{ dBm}$).
- **Off-Line-of-Sight Inadequacy (Position P1):** In Session H (subject positioned 30 cm off-LoS), the mean RSSI is $-26.49\text{ dBm}$, which is indistinguishable from the empty room baseline of $-26.47\text{ dBm}$ ($\Delta \text{RSSI} = 0.02\text{ dBm}$). RSSI alone cannot reliably detect off-LoS presence.
- **CSI Multipath Discriminability:** In contrast to RSSI, subcarrier amplitude variance ($\sigma_k^2$) increases substantially across specific subcarriers during off-LoS presence, confirming that multipath scattering provides a robust presence detection signature.

### 4.2 Link Stability & Stationarity
- **Continuous Acquisition (Session J):** An extended 31.5-minute empty recording demonstrated stationary variance, bounded unwrapped phase, and negligible rolling-mean thermal drift.
- **Long-Term Repeatability:** Empty sessions recorded across 7 hours (G at 17:01, J at 20:00, and L at 00:09) displayed nearly identical mean subcarrier amplitude profiles, verifying hardware and environmental repeatability.
