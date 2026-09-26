# Preprocessing and Feature Extraction Pipeline (`02_pipeline`)

This document summarizes the signal preprocessing and feature engineering pipelines implemented in [`notebooks/02_pipeline/`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/):
- [`pipeline_v0.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb): Initial pipeline prototype operating on the pilot dataset.
- [`pipeline_v1.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb): Production pipeline processing both pilot and main benchmark datasets.

---

## 1. Pipeline Overview & Comparison

| Parameter / Metric | Pipeline v0 ([`pipeline_v0.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb)) | Pipeline v1 ([`pipeline_v1.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb)) |
| :--- | :--- | :--- |
| **Input Campaigns** | Pilot collection (`data/01_raw/pilot/`) | Pilot + Main campaigns (`data/01_raw/pilot/`, `data/01_raw/main/`) |
| **Discovered Sessions** | 6 sessions | 13 sessions |
| **Excluded Sessions** | 2 sessions (`A`, `B` marked as `INVALID`) | 2 sessions (`A`, `B` marked as `INVALID`) |
| **Processed Sessions** | 4 sessions (`C`, `D`, `E`, `F`) | 11 sessions (`C`, `D`, `E`, `F`, `G`, `H`, `I`, `J`, `K`, `L`, `M`) |
| **Raw Subcarrier Bins** | 192 complex subcarriers | 192 complex subcarriers |
| **Shared Valid Subcarriers** | 162 subcarriers (mean amplitude $\ge 0.5$) | 162 subcarriers (mean amplitude $\ge 0.5$) |
| **Window Duration ($T_w$)** | 2.0 seconds, non-overlapping | 2.0 seconds, non-overlapping |
| **Feature Extraction** | 4 metrics $\times$ 162 subcarriers = 648 features | 4 metrics $\times$ 162 subcarriers = 648 features |
| **Total Windows (Samples)** | **1,200 windows** | **3,900 windows** |
| **Class Distribution** | Balanced: 600 empty (0) / 600 occupied (1) | Imbalanced: 2,100 empty (0) / 1,800 occupied (1) |
| **Target Output Directory** | `outputs/pilot/pipeline_v0/` | `data/03_processed/` |

---

## 2. Core Processing Stages

Both pipeline versions share the same fundamental transformation steps:

1. **Session Discovery & Metadata Validation:**
   - Ingests paired `.csv` and `_meta.json` files.
   - Programmatically excludes sessions where `timing.status != "VALID"` (excluding pilot sessions `A` and `B`).
2. **Shared Subcarrier Masking:**
   - Filters out dead subcarriers (guard bands and DC center carrier) where mean amplitude $< 0.5$.
   - Computes the intersection of valid subcarriers across all sessions, retaining **162 shared valid subcarriers**.
3. **Active Interval Slicing:**
   - Extracts samples within the ground-truth timestamps $[T_1, T_2]$ (`timing.t1_condition_start` to `timing.t2_condition_end`).
   - Automatically discards the initial 60 s RF stabilization window and the terminal 30 s buffer.
4. **Non-Overlapping Window Segmentation:**
   - Segments the continuous time series into fixed **2.0-second** windows with zero overlap.
   - Requires each valid window to contain at least 5 samples and maintain $\ge 50\%$ of the nominal sample rate.
5. **Statistical Feature Extraction:**
   - For each valid subcarrier, four statistical dispersion descriptors are computed over the 2.0 s window:
     - **Variance (`var`):** Measures amplitude power dispersion caused by presence or movement.
     - **Mean Absolute Deviation (`mad`):** Robust dispersion measure less sensitive to isolated spikes.
     - **Range (`range`):** Peak-to-peak amplitude excursion ($\max - \min$).
     - **Interquartile Range (`iqr`):** Non-parametric statistical spread ($Q_{75} - Q_{25}$).
   - Yields $162\text{ subcarriers} \times 4\text{ descriptors} = \mathbf{648}$ feature columns (`sc000_var` through `sc161_iqr`).
   - RSSI is excluded from the feature set to ensure models learn purely from Channel State Information.

---

## 3. Dataset Assembly & Output Artifacts

### 3.1 Column Structure (657 Columns Total)
- **Metadata Columns (9):** `session_id`, `source_csv`, `label_name`, `label`, `window_index`, `window_start_time`, `window_end_time`, `n_samples`, `effective_rate_hz_window`.
- **Feature Columns (648):** `sc000_var`, `sc000_mad`, `sc000_range`, `sc000_iqr`, ..., `sc161_iqr`.
- **Target Encoding (`label`):** Binary classification where `0 = empty` and `1 = occupied` (including `occupied_still`, `occupied_moving`, and spatial variants `occupied_p1` to `p4`).

### 3.2 Output Files
- **Pipeline v0 (`outputs/pilot/pipeline_v0/`):**
  - `features_v0_ht40.csv` / `features_v0_ht40.parquet` (1,200 rows $\times$ 657 cols).
  - `valid_subcarrier_mapping_v0.csv`.
  - `pipeline_report_v0.json`.
- **Pipeline v1 (`data/03_processed/`):**
  - `features_ht40.csv` / `features_ht40.parquet` (3,900 rows $\times$ 657 cols).
  - `valid_subcarrier_mapping.csv`.
  - `reports/logs/pipeline_report_latest.json`.

---

## 4. Final Dataset Composition (Pipeline v1)

| Session ID | Campaign | Label Name | Binary Label | Windows Produced |
| :---: | :---: | :--- | :---: | :---: |
| **C** | Pilot | `empty` | 0 | 300 |
| **D** | Pilot | `occupied_still` | 1 | 300 |
| **E** | Pilot | `occupied_moving` | 1 | 300 |
| **F** | Pilot | `empty` | 0 | 300 |
| **G** | Main | `empty` | 0 | 300 |
| **H** | Main | `occupied_p1_still` | 1 | 300 |
| **I** | Main | `occupied_p2_still` | 1 | 300 |
| **J** | Main | `empty` (extended 31.5 min) | 0 | 900 |
| **K** | Main | `occupied_p3_still` | 1 | 300 |
| **L** | Main | `empty` | 0 | 300 |
| **M** | Main | `occupied_p4_still` | 1 | 300 |
| **Total** | — | — | **0: 2,100 / 1: 1,800** | **3,900** |
