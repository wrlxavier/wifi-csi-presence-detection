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
| Hardware setup & data collection | Done | ESP32-S3 HT40 link, 15 recorded sessions across 3 campaigns (11 valid ingested: C-M) |
| Signal processing & mask | Done | 162 shared valid HT40 subcarriers (out of 192 raw subcarriers) |
| Feature dataset assembly | Done | 3,889 windows $\times$ 648 statistical features (2,095 empty, 1,794 occupied) |
| ML model training (10-fold CV) | Done | MLP (0.9922), GB (0.9789), SVM (0.9748), RF (0.9721) Macro $F_1$ |
| Held-out test set evaluation | Done | Best model (MLP): $F_1 = 0.9897$, Accuracy = 98.97%, FAR = 0.32% (584 test windows) |
| Robustness & thesis reporting | Done | LaTeX tables & publication figures in `reports/` (per-session, condition, time-of-day) |

## Repository Structure

```text
wifi-csi-presence-detection/
├── Makefile                            # Reproducible automation targets (uv run)
├── pyproject.toml                      # PEP 621 dependencies & package specification
├── configs/                            # Centralized YAML configurations
│   └── pipeline.yaml                   # Windowing, filtering, and feature parameters
├── data/                               # 3-Tier Unidirectional Data Storage
│   ├── 01_raw/                         # Immutable raw acquisition dumps
│   │   ├── first_test/                 # Exploratory benchmark campaign
│   │   ├── pilot/                      # Pilot campaign (sessions A-F)
│   │   └── main/                       # Main campaign (sessions G-M)
│   ├── 02_interim/                     # Calibrated amplitude arrays & masks
│   └── 03_processed/                   # Canonical feature datasets & splits
│       ├── features_ht40.parquet       # Canonical tabular feature dataset (Parquet)
│       ├── features_ht40.csv           # Canonical tabular feature dataset (CSV)
│       ├── valid_subcarrier_mapping.csv # Retained subcarrier indices mapping
│       └── splits/                     # train.parquet, val.parquet, test.parquet (70/15/15)
├── docs/                               # Project documentation
├── models/                             # Trained models & registry
│   ├── registry/                       # Bundled pipelines (pipeline.joblib + model_card.json)
│   │   ├── mlp_bundle/                 # Multilayer Perceptron bundle (best model)
│   │   ├── svm_bundle/                 # Support Vector Machine bundle
│   │   ├── gradient_boosting_bundle/   # Gradient Boosting bundle
│   │   └── random_forest_bundle/       # Random Forest bundle
│   ├── gradient_boosting.pkl           # Standalone model pickles
│   ├── mlp.pkl
│   ├── random_forest.pkl
│   ├── svm.pkl
│   └── scaler.pkl                      # Fitted StandardScaler
├── notebooks/                          # Interactive pipeline workflow notebooks
│   ├── 00_acquisition/                 # csi_collector_v2.ipynb (data collection)
│   ├── 01_eda/                         # eda_first_test.ipynb, eda_pilot.ipynb, eda_main.ipynb
│   ├── 02_pipeline/                    # pipeline_v0.ipynb, pipeline_v1.ipynb (features & filtering)
│   ├── 03_analysis/                    # separability_figures.ipynb, separability_lda.ipynb
│   └── 04_modeling/                    # 01_split.ipynb to 05_robustness.ipynb (training & evaluation)
├── outputs/                            # Diagnostic figures, artifacts, and backups
│   ├── backups/                        # Backup archives (.gitkeep, ignored .zip archives)
│   ├── first_test/                     # Exploratory campaign plots
│   ├── main/                           # Main campaign plots
│   ├── pilot/                          # Pilot campaign plots & figures
│   └── pipeline_v1/                    # Pipeline v1 figures & evaluation artifacts
├── reports/                            # Publication & thesis assets
│   ├── figures/                        # High-resolution PNG and vector PDF plots
│   ├── tables/                         # LaTeX (.tex) and CSV tables for thesis
│   └── logs/                           # Automated pipeline & evaluation JSON logs
├── scripts/                            # Automation & live inference tools
│   ├── backup_data.py                  # Compress and restore untracked/ignored project data
│   └── realtime_presence.py            # Live real-time CSI presence detection monitor
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
# or sync environment: uv sync --extra dev
```

### 2. Run Tests
Verify all parsing, filtering, and feature algorithms:
```bash
make test
# or directly: uv run pytest tests/ -v
```

### 3. Pipeline Workflow (Jupyter Notebooks)

The entire workflow—including data acquisition, preprocessing, training, and validation—is executed using interactive Jupyter Notebooks in the `notebooks/` directory:

1. **Acquisition:** [`notebooks/00_acquisition/csi_collector_v2.ipynb`](notebooks/00_acquisition/csi_collector_v2.ipynb)
2. **Preprocessing & Feature Extraction:** [`notebooks/02_pipeline/pipeline_v1.ipynb`](notebooks/02_pipeline/pipeline_v1.ipynb)
3. **Dataset Splitting:** [`notebooks/04_modeling/01_split.ipynb`](notebooks/04_modeling/01_split.ipynb)
4. **Data Normalization & Preprocessing:** [`notebooks/04_modeling/02_preprocessing.ipynb`](notebooks/04_modeling/02_preprocessing.ipynb)
5. **Model Training (10-fold CV):** [`notebooks/04_modeling/03_training.ipynb`](notebooks/04_modeling/03_training.ipynb)
6. **Validation & Evaluation:** [`notebooks/04_modeling/04_evaluation.ipynb`](notebooks/04_modeling/04_evaluation.ipynb)
7. **Robustness & Thesis Reporting:** [`notebooks/04_modeling/05_robustness.ipynb`](notebooks/04_modeling/05_robustness.ipynb)

### 4. Real-Time Live Presence Detection

To launch the live system monitoring and presence detection interface with the ESP32-S3 RX node:
```bash
make live
# or directly: uv run python scripts/realtime_presence.py
```

### 5. Data Backup & Recovery (Untracked Assets)

Large raw datasets, model pickles, reports, and generated images are excluded from Git via `.gitignore`. You can create and restore self-contained `.zip` backup archives stored in `outputs/backups/`:

```bash
# Compress all untracked data/models/reports into a timestamped zip in outputs/backups/
make compress
# or directly: uv run python scripts/backup_data.py compress

# Compress with a custom archive name
make compress ARCHIVE=my_backup.zip
# or directly: uv run python scripts/backup_data.py compress --file my_backup.zip

# Restore from the latest archive in outputs/backups/ and validate file structure
make restore
# or directly: uv run python scripts/backup_data.py restore

# Restore a specific archive version
make restore ARCHIVE=my_backup.zip
# or directly: uv run python scripts/backup_data.py restore --file my_backup.zip
```

The restoration process verifies archive integrity (CRC-32), extracts files to their original repository paths, and validates that all expected project components (`data/01_raw/`, `data/03_processed/splits/`, `models/`, `outputs/`, `reports/`) are present and intact.

## Hardware

| Component | Qty | Role |
|---|---|---|
| ESP32-S3-DevKitC-1U-N8R8 | 2 | TX (STA transmitter) and RX (AP CSI receiver) nodes |
| 2.4 GHz Wi-Fi antenna (3 dBi, U.FL) | 2 | External omnidirectional antennas |
| Aluminum tripod (2.1 m max height) | 2 | Fixed positioning at 1.20 m height, 2.0 m LoS distance |
| Power bank 10,000 mAh | 1 | Portable battery for isolated TX node power supply |

## References

- Hernandez & Bulut (2022) - *WiFi Sensing on the Edge*, IEEE COMST. [DOI](https://doi.org/10.1109/COMST.2022.3209144)
- Natarajan et al. (2023) - *Passive Human Motion Detection Using WiFi*, IEEE TIM. [DOI](https://doi.org/10.1109/TIM.2023.3272374)
- Wong et al. (2024) - *SHD-HAR Dataset*, Data in Brief. [DOI](https://doi.org/10.1016/j.dib.2024.110673)
