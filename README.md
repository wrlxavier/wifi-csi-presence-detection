# Wi-Fi CSI Presence Detection

> Binary classification of human presence (empty vs. occupied) using Wi-Fi Channel State Information (CSI) collected from low-cost ESP32-S3 hardware — no cameras, no wearables.

*Undergraduate Thesis (PFC) — Engenharia de Controle e Automação, UFMG, 2026.*

## Overview

This repository contains the notebooks, data, and outputs from an undergraduate thesis project (Engenharia de Controle e Automação, UFMG, 2026).

The goal is to build a **device-free presence detection system** that leverages the CSI extracted from Wi-Fi 802.11n signals. Two ESP32-S3-DevKitC-1U nodes form a dedicated TX/RX link over 802.11n HT40: when a person occupies the monitored area, their body alters multipath propagation, causing measurable changes in the amplitude and phase of OFDM subcarriers. These variations are captured, processed, and fed into machine learning classifiers.

## Intended Pipeline

1. **Data collection** — ESP32-S3 firmware (via `esp-csi`) captures raw CSI frames over USB-serial, saved as `.csv` + `_meta.json`
2. **Preprocessing** — subcarrier filtering, outlier removal, denoising (Butterworth / Daubechies wavelets)
3. **Feature extraction** — per-subcarrier temporal descriptors (variance, MAD, range, IQR) over sliding windows
4. **Classification** — binary classifiers trained with `scikit-learn` (Random Forest, SVM, XGBoost, MLP); target metric: F1-score ≥ 0.90 on the held-out test set

## Current Status

**Pipeline v0 complete — classification pending.**

| Stage | Status |
|---|---|
| Hardware setup & data collection | Done |
| EDA (amplitude, phase, RSSI, subcarriers) | Done |
| Pipeline v0: parsing → cleaning → feature extraction | Done |
| ML model training & evaluation | Not started |

### Pilot dataset (2026-05-02/03)

6 sessions collected (A–F); 4 passed metadata validation (C: empty, D: occupied-still, E: occupied-moving, F: empty).

Pipeline v0 output (`pilot/outputs/pipeline_v0/`):
- **162 shared valid HT40 subcarriers** (from 192 complex)
- **648 features** per window (variance, MAD, range, IQR × 162 subcarriers)
- **1 200 windows** — 600 empty / 600 occupied, perfectly balanced
- 2-second non-overlapping windows at ~29 Hz effective rate

## Repository Structure

```
data/
  first_test/          # Initial April 2026 test (2 raw sessions)
  pilot/               # Pilot May 2026 (6 raw sessions — C, D, E, F valid)
  main/                # Main dataset (Card 6 — future collection)
notebooks/
  00_acquisition/      # csi_collector_v2.ipynb — data collection helper
  01_eda/              # eda_first_test.ipynb, eda_pilot.ipynb
  02_pipeline/         # pipeline_v0.ipynb — parsing → features → report
  03_analysis/         # separability_figures.ipynb, separability_lda.ipynb
  04_modeling/         # ML classifiers (Random Forest, SVM, XGBoost, MLP) — Card 7
src/
  parsing.py           # CSV/JSON parsing, subcarrier extraction
  preprocessing.py     # I/Q → amplitude, filtering, windowing
  features.py          # variance, MAD, range, IQR per window
outputs/
  pilot/pipeline_v0/   # features_v0_ht40.csv/.parquet + pipeline_report_v0.json
  pilot/figures/       # final_figure.pdf + LDA/PCA separation plots
models/                # Serialised trained models (.pkl / .joblib) — Card 7
docs/
  REPO_STRUCTURE_PROPOSAL.md
  artigo_SBrT.md
  trello_board.md
```

## Hardware

| Component | Qty | Role |
|---|---|---|
| ESP32-S3-DevKitC-1U-N8R8 | 2 | TX (STA) and RX (AP) nodes |
| 2.4 GHz Wi-Fi antenna (3 dBi, U.FL) | 2 | External antennas |
| Aluminum tripod (2.1 m) | 2 | Fixed positioning |
| Power bank 10,000 mAh | 1 | Portable TX power supply |

## References

- Hernandez & Bulut (2022) — *WiFi Sensing on the Edge*, IEEE COMST. [DOI](https://doi.org/10.1109/COMST.2022.3209144)
- Natarajan et al. (2023) — *Passive Human Motion Detection Using WiFi*, IEEE TIM. [DOI](https://doi.org/10.1109/TIM.2023.3272374)
- Wong et al. (2024) — *SHD-HAR Dataset*, Data in Brief. [DOI](https://doi.org/10.1016/j.dib.2024.110673)
