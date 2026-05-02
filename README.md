# Wi-Fi CSI Presence Detection

> Binary classification of human presence (empty vs. occupied) using Wi-Fi Channel State Information (CSI) collected from low-cost ESP32-S3 hardware — no cameras, no wearables.

## Overview

This repository contains the exploratory notebooks and pilot data from an undergraduate thesis project (Engenharia de Controle e Automação, UFMG, 2026).

The goal is to build a **device-free presence detection system** that leverages the CSI extracted from Wi-Fi 802.11n signals. Two ESP32-S3-DevKitC-1U nodes form a dedicated TX/RX link: when a person occupies the monitored area, their body alters multipath propagation, causing measurable changes in the amplitude and phase of OFDM subcarriers. These variations are captured, processed, and fed into machine learning classifiers.

## Intended Pipeline

1. **Data collection** — ESP32-S3 firmware (via `esp-csi`) captures raw CSI frames over USB-serial, saved as `.csv` files
2. **Preprocessing** — subcarrier filtering, outlier removal, denoising (Butterworth / Daubechies wavelets)
3. **Feature extraction** — per-subcarrier temporal descriptors (variance, MAD, range, IQR) over sliding windows, yielding 204-dimensional feature vectors
4. **Classification** — binary classifiers trained with `scikit-learn` (Random Forest, SVM, XGBoost, MLP); target metric: F1-score ≥ 0.90 on the held-out test set

## Current Status

The repository is in its **early exploratory phase**. It currently consists of standalone Jupyter notebooks used for:
- Pilot data collection and raw CSI inspection
- Exploratory data analysis (EDA) of amplitude, phase, RSSI, and subcarrier behavior
- Visual comparison between empty and occupied conditions

No structured package or API exists yet. Scripts and notebooks will be progressively organized as the project matures.

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

---

*Undergraduate Thesis (PFC) — Engenharia de Controle e Automação, UFMG, 2026.*
