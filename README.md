# Wi-Fi CSI Presence Detection

> Binary classification of human presence (empty vs. occupied) using Wi-Fi Channel State Information (CSI) collected from low-cost ESP32-S3 hardware - no cameras, no wearables.

*Undergraduate Thesis (PFC) - Engenharia de Controle e Automação, UFMG, 2026.*

## Overview

This repository contains the codebase, datasets, and experiment reports from an undergraduate thesis project (Engenharia de Controle e Automação, UFMG, 2026).

The goal is to build a **device-free presence detection system** that leverages the CSI extracted from Wi-Fi 802.11n signals. Two ESP32-S3-DevKitC-1U nodes form a dedicated TX/RX link over 802.11n HT40: when a person occupies the monitored area (specifically, a residential bedroom), their body alters multipath propagation, causing measurable changes in the amplitude and phase of OFDM subcarriers. These variations are captured, processed, and fed into machine learning classifiers.

## Pipeline Architecture

1. **Data Collection** - ESP32-S3 firmware captures raw CSI frames over USB-serial, saved as `.csv` + companion `_meta.json` sidecar.
2. **Preprocessing & Filtering** - Subcarrier noise detection, DC/null removal, shared HT40 valid-subcarrier mask (162 carriers), and temporal filtering (Butterworth / Wavelet).
3. **Feature Extraction** - Per-subcarrier statistical descriptors (Variance, MAD, Range, IQR $\times$ 162 subcarriers = 648 features) over 2.0-second non-overlapping windows.
4. **Classification & Robustness** - Binary classifiers trained with `scikit-learn` (MLP, Gradient Boosting, SVM, Random Forest) evaluated across cross-validation, held-out test set, and multi-session spatial positions. Target metric: $F_1 \ge 0.90$ (Achieved: $F_1 = 0.9897$).

## Current Status

| Stage | Status | Metric / Output |
|---|---|---|
| Hardware setup & data collection | Done | ESP32-S3 HT40 link, 13 sessions (pilot + main) |
| Signal processing & mask | Done | 162 shared valid HT40 subcarriers |
| Feature dataset assembly | Done | 3,889 windows $\times$ 648 statistical features |
| ML model training (10-fold CV) | Done | MLP (0.9922), GB (0.9789), SVM (0.9748), RF (0.9721) |
| Held-out test set evaluation | Done | $F_1 = 0.9897$, Accuracy = 98.97%, FAR = 0.32% |
| Robustness & thesis reporting | Done | LaTeX tables & publication figures in `reports/` |

## Repository Structure

```text
wifi-csi-presence-detection/
├── Makefile                            # Reproducible automation targets (uv run)
├── pyproject.toml                      # PEP 621 dependencies & package specification
├── configs/                            # Centralized YAML configurations
│   ├── acquisition.yaml                # Serial port, baudrate, timeouts
│   ├── pipeline.yaml                   # Windowing, filtering, and split parameters
│   └── models.yaml                     # Search spaces, CV folds, scoring metrics
├── data/                               # 3-Tier Unidirectional Data Storage
│   ├── 01_raw/                         # Immutable raw acquisition dumps
│   │   ├── first_test/                 # Exploratory benchmark campaign
│   │   ├── pilot/                      # Pilot campaign (sessions A–F)
│   │   └── main/                       # Main campaign (sessions G–M)
│   ├── 02_interim/                     # Calibrated amplitude arrays & masks
│   └── 03_processed/                   # Canonical feature datasets & splits
│       ├── features_ht40.parquet       # Canonical tabular feature dataset
│       └── splits/                     # train.parquet, val.parquet, test.parquet
├── docs/                               # Project documentation & architecture proposals
│   └── REPO_STRUCTURE_PROPOSAL.md      # Detailed repository architecture & migration guide
├── models/                             # Trained models & registry
│   ├── registry/                       # Atomic Pipeline(Scaler+Classifier) + model_card.json
│   ├── gradient_boosting.pkl           # Legacy flat pickles for backward compatibility
│   ├── mlp.pkl
│   ├── random_forest.pkl
│   ├── svm.pkl
│   └── scaler.pkl
├── notebooks/                          # Narrative exploration & visualization (read-only)
│   ├── 00_acquisition/                 # csi_collector_v2.ipynb
│   ├── 01_eda/                         # eda_pilot.ipynb, eda_main.ipynb
│   ├── 02_pipeline/                    # pipeline_v1.ipynb
│   ├── 03_analysis/                    # separability_figures.ipynb, separability_lda.ipynb
│   └── 04_modeling/                    # 01_split to 05_robustness
├── reports/                            # Publication & thesis assets
│   ├── figures/                        # High-resolution PNG and vector PDF plots
│   ├── tables/                         # LaTeX (.tex) and CSV tables for thesis
│   └── logs/                           # Automated pipeline & evaluation JSON logs
├── scripts/                            # Headless CLI automation entry points
│   ├── collect_csi.py                  # Standalone serial acquisition daemon
│   ├── run_pipeline.py                 # Raw -> Interim -> Features -> Splits
│   ├── train_models.py                 # Model training & CV grid search
│   ├── evaluate.py                     # Held-out test set & robustness benchmarks
│   └── export_thesis_assets.py         # Generate LaTeX tables & vector figures
├── src/                                # Installable Python package (uv pip install -e .)
│   ├── wifi_csi/                       # Core modular package
│   │   ├── core/                       # Config loader and domain constants
│   │   ├── parsing/                    # I/Q complex decoding and metadata parsers
│   │   ├── signal/                     # Amplitudes, masks, Butterworth & wavelet denoise
│   │   ├── features/                   # Statistical descriptor extractors (var, mad, etc.)
│   │   ├── models/                     # Pipeline builder, CV tuner, model cards
│   │   ├── evaluation/                 # Metrics, robustness, publication plots
│   │   └── acquisition/                # PySerial reader with buffer recovery
│   ├── preprocessing.py                # Backward-compatibility wrapper
│   ├── evaluation.py                   # Backward-compatibility wrapper
│   ├── parsing.py                      # Backward-compatibility wrapper
│   └── features.py                     # Backward-compatibility wrapper
└── tests/                              # Automated test suite (pytest)
    ├── conftest.py                     # Synthetic CSI fixtures
    ├── unit/                           # Unit tests for decoder, signal, features, models, metrics
    └── integration/                    # End-to-end pipeline integration tests
```

## Quickstart (`uv`)

This project uses **[`uv`](https://github.com/astral-sh/uv)** for fast, reliable package and environment management.

### 1. Installation
Install the project in editable mode with development dependencies:
```bash
make install
# or directly: uv pip install -e ".[dev]"
```

### 2. Run Tests
Verify all parsing, filtering, and feature algorithms:
```bash
make test
# or directly: uv run pytest tests/ -v
```

### 3. Execute End-to-End Pipeline
Run data processing, training, evaluation, and report generation with one command:
```bash
make all
```

Or execute individual pipeline stages:
```bash
make pipeline    # Process raw data into features_ht40.parquet and splits
make train       # Run 10-fold CV and register models
make evaluate    # Evaluate held-out test set and compute robustness metrics
make figures     # Export publication figures and LaTeX tables to reports/
```

## Hardware

| Component | Qty | Role |
|---|---|---|
| ESP32-S3-DevKitC-1U-N8R8 | 2 | TX (STA) and RX (AP) nodes |
| 2.4 GHz Wi-Fi antenna (3 dBi, U.FL) | 2 | External antennas |
| Aluminum tripod (2.1 m) | 2 | Fixed positioning |
| Power bank 10,000 mAh | 1 | Portable TX power supply |

## References

- Hernandez & Bulut (2022) - *WiFi Sensing on the Edge*, IEEE COMST. [DOI](https://doi.org/10.1109/COMST.2022.3209144)
- Natarajan et al. (2023) - *Passive Human Motion Detection Using WiFi*, IEEE TIM. [DOI](https://doi.org/10.1109/TIM.2023.3272374)
- Wong et al. (2024) - *SHD-HAR Dataset*, Data in Brief. [DOI](https://doi.org/10.1016/j.dib.2024.110673)
