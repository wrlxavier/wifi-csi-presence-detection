# Wi-Fi CSI Human Presence Detection - Documentation Index

Welcome to the technical documentation for the Wi-Fi CSI Human Presence Detection repository. This project implements an end-to-end research and engineering pipeline that detects human presence in indoor environments using Channel State Information (CSI) acquired from commercial off-the-shelf ESP32-S3 microcontrollers.

---

## Documentation Navigation

This documentation suite synthesizes all technical specifications, empirical findings, and architectural decisions derived from the repository's Jupyter notebooks:

1. [Hardware and Acquisition Guide](file:///home/xavier/dev/wifi-csi-presence-detection/docs/HARDWARE_AND_ACQUISITION.md)
   - ESP32-S3 dual-node configuration (STA transmitter, AP receiver).
   - ESP-NOW protocol, 802.11n HT40 channel dynamics (192 subcarriers, 40 MHz, Channel 11).
   - High-speed serial logging protocol (921600 baud, 30 Hz nominal rate).
   - Dual-file session format (`.csv` data and companion `_meta.json` ground truth).
   - Derived from [csi_collector_v2.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb).

2. [Dataset and Experimental Sessions](file:///home/xavier/dev/wifi-csi-presence-detection/docs/DATASET_AND_SESSIONS.md)
   - Inventory of all 13 experimental sessions across First Test (PLA, PLB), Pilot (A to F), and Main Campaign (G to M).
   - Room geometry (3.40 m x 3.45 m x 2.85 m residential bedroom) and physical boundary characteristics.
   - Spatial presence topologies: Line-of-Sight (P2, P3) and Off-Line-of-Sight (P1, P4).
   - Automated session quality checks and invalidation criteria.
   - Derived from [eda_first_test.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb), [eda_pilot.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb), and [eda_main.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb).

3. [Signal Processing and Feature Engineering](file:///home/xavier/dev/wifi-csi-presence-detection/docs/SIGNAL_PROCESSING_AND_FEATURES.md)
   - Raw interleaved I/Q decomposition into subcarrier amplitudes.
   - Dynamic 162 shared HT40 subcarrier masking across sessions.
   - Time-based 2.0-second non-overlapping windowing.
   - Official natural-scale feature representation: Variance, Mean Absolute Deviation (MAD), Range, and Interquartile Range (IQR) yielding 648 features.
   - Derived from [pipeline_v0.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb) and [pipeline_v1.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb).

4. [Statistical Analysis and Separability](file:///home/xavier/dev/wifi-csi-presence-detection/docs/STATISTICAL_ANALYSIS_AND_SEPARABILITY.md)
   - Methodological finding: temporal rolling IQR versus cross-subcarrier IQR.
   - Unsupervised class separation via Principal Component Analysis (PCA) and Linear Discriminant Analysis (LDA).
   - One-way ANOVA F-statistic ranking of subcarriers and statistical feature types.
   - Derived from [separability_figures.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_figures.ipynb) and [separability_lda.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb).

5. [Machine Learning Benchmarks and Robustness](file:///home/xavier/dev/wifi-csi-presence-detection/docs/MODELING_AND_BENCHMARKS.md)
   - Stratified train/val/test partitioning (70/15/15) preserving session balance.
   - 10-fold Stratified Cross-Validation across 4 model families (Random Forest, SVM-RBF, Gradient Boosting, MLP).
   - Held-out test set performance against the target requirement (Macro F1 >= 0.90).
   - 4-axis robustness stress testing: across sessions, postures, spatial positions, and time-of-day.
   - Derived from [01_split.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/01_split.ipynb) through [05_robustness.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/05_robustness.ipynb).

6. [Repository Architecture Specification](file:///home/xavier/dev/wifi-csi-presence-detection/docs/REPO_STRUCTURE_PROPOSAL.md)
   - Structural design, tiered data organization (`data/01_raw`, `data/02_interim`, `data/03_processed`), packaging, CLI automation, and reproducibility standards.

---

## Notebooks to Codebase Mapping

| Notebook | Focus Area | Canonical Module / Script Equivalent |
|---|---|---|
| [csi_collector_v2.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb) | Serial data logging & metadata | [`wifi_csi.acquisition`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/acquisition/__init__.py) |
| [eda_first_test.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb) | Feasibility and link integrity | [`wifi_csi.signal.filters`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/signal/filters.py) |
| [eda_pilot.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb) | Pilot validation & noise checks | [`wifi_csi.signal.filters`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/signal/filters.py) |
| [eda_main.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb) | Multi-position campaign analysis | [`wifi_csi.parsing.loader`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/parsing/loader.py) |
| [pipeline_v0.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb) | Pilot feature extraction | [`wifi_csi.features.pipeline`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/features/pipeline.py) |
| [pipeline_v1.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb) | Full dataset pipeline | [scripts/run_pipeline.py](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/run_pipeline.py) |
| [separability_figures.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_figures.ipynb) | Temporal vs SC aggregation | [scripts/export_thesis_assets.py](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/export_thesis_assets.py) |
| [separability_lda.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb) | PCA, LDA, and ANOVA tests | [`wifi_csi.evaluation.metrics`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/evaluation/metrics.py) |
| [01_split.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/01_split.ipynb) | Stratified 70/15/15 splitting | [`wifi_csi.features.pipeline`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/features/pipeline.py) |
| [02_preprocessing.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/02_preprocessing.ipynb) | Feature standardization | [`wifi_csi.models.builder`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/models/builder.py) |
| [03_training.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/03_training.ipynb) | 10-fold CV model fitting | [scripts/train_models.py](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/train_models.py) |
| [04_evaluation.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/04_evaluation.ipynb) | Model selection & test metric | [scripts/evaluate.py](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/evaluate.py) |
| [05_robustness.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/05_robustness.ipynb) | Multi-axis stress testing | [scripts/evaluate.py](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/evaluate.py) |

---

## Execution Workflow

All steps documented herein can be reproduced through the unified Makefile:

```bash
# 1. Run full extraction pipeline
make pipeline

# 2. Train models with 10-fold CV
make train

# 3. Evaluate models on validation and test partitions
make evaluate

# 4. Generate LaTeX tables and vector figures
make figures

# Or run the complete workflow end-to-end:
make all
```
