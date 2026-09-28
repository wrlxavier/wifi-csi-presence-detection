# Class Separability Analysis (`03_analysis`)

This document summarizes the exploratory class separability analysis conducted on the pilot dataset across the two notebooks in [`notebooks/03_analysis/`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/):
- [`separability_lda.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb): Dimensionality reduction (PCA, LDA) and statistical hypothesis testing on engineered features.
- [`separability_figures.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_figures.ipynb): Time-series dynamics, baseline selection strategy, and publication figures.

---

## 1. Study Scope & Objectives

The primary objective of this stage was to verify whether the 648 engineered statistical dispersion features provide clear class separability between empty and occupied environments before proceeding to machine learning model training:
- **Input Dataset:** Pilot feature dataset (`features_v0_ht40.parquet`), containing 1,200 non-overlapping 2.0 s windows (300 windows each from sessions `C`, `D`, `E`, and `F`).
- **Feature Space:** 648 features (162 shared valid subcarriers $\times$ 4 metrics: `var`, `mad`, `range`, `iqr`).
- **Evaluated Target Formulations:**
  - **Binary (2-class):** `empty` (600 windows) vs. `occupied` (600 windows).
  - **Categorical (3-class):** `empty` (600 windows), `occupied_still` (300 windows), and `occupied_moving` (300 windows).

---

## 2. Dimensionality Reduction & Linear Separability

| Technique | Projection Space | Key Metric / Explained Variance | Observation & Significance |
| :--- | :--- | :--- | :--- |
| **PCA** | Unsupervised (2 PCs) | 2 PCs: **86.3%** variance (10 PCs: 95.8%, 50 PCs: 98.3%) | Clean visual cluster separation between empty and occupied samples along principal variance axes. |
| **Binary LDA** | Supervised (1D projection) | Score range: $[-9.67, 9.11]$; **Cohen's $d = 12.643$** | Exceptionally high effect size, confirming near-complete linear separability between empty and occupied classes. |
| **3-Class LDA** | Supervised (2D projection) | Plane defined by LD1 and LD2 | Forms distinct, non-overlapping clusters for `empty`, `occupied_still`, and `occupied_moving`. |

---

## 3. Aggregated Feature Distributions & Hypothesis Tests

Evaluating the mean value across all 162 valid subcarriers per window yields clear statistical differentiation across conditions:

| Feature Type | Empty Mean | Occupied Mean | Binary Cohen's $d$ | Kruskal-Wallis $H$ (3-class) | $p$-value (3-class) | Still vs. Moving Cohen's $d$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Variance (`var`)** | 3.649 | 16.366 | 0.898 | 937.9 | $2.19 \times 10^{-204}$ | 2.483 |
| **Mean Absolute Deviation (`mad`)** | 1.165 | 2.283 | 0.851 | 974.3 | $2.72 \times 10^{-212}$ | 3.777 |
| **Range (`range`)** | 8.039 | 10.977 | 0.486 | 865.4 | $1.20 \times 10^{-188}$ | 4.232 |
| **Interquartile Range (`iqr`)** | 1.832 | 4.027 | 0.890 | 963.2 | $6.92 \times 10^{-210}$ | 3.215 |

- **Motion Sensitivity:** Peak-to-peak Range and MAD show the strongest divergence between motionless presence (`occupied_still`) and dynamic movement (`occupied_moving`), with Cohen's $d$ reaching $3.78$ and $4.23$.

---

## 4. Per-Subcarrier Discriminability (One-Way ANOVA F-Tests)

One-way ANOVA F-statistics were computed for every subcarrier-feature pair:
- **Binary F-statistic Range:** Min: $0.0$, Median: $169.3$, Max: $377.1$.
- **3-Class F-statistic Range:** Min: $137.8$, Median: $1,259.5$, Max: $2,253.5$.
- **Top 5 Most Discriminative Features (Binary):**
  1. `sc150_mad` ($F = 377.1$)
  2. `sc150_iqr` ($F = 375.4$)
  3. `sc150_var` ($F = 289.4$)
  4. `sc151_mad` ($F = 286.2$)
  5. `sc075_var` ($F = 280.8$)
- Subcarrier `sc150` (raw OFDM index 179) consistently demonstrated the highest individual discriminative power across all four statistical descriptors.

---

## 5. Physical Signal Dynamics & Baseline Selection (`separability_figures.ipynb`)

- **Empty Condition Strategy:**
  - Comparison between Session C (Day 1) and Session F (Day 2) showed a $13.90\%$ difference in median CSI amplitude ($40.22$ vs. $34.63$), reflecting inter-day radio environment drift.
  - To eliminate confounding inter-day variance, **Session C was chosen** as the primary baseline since it was collected on the same day under the exact same physical setup as Sessions D and E.
- **Physical Dynamics Across Conditions:**
  - `empty` (Session C): Highly stable median amplitude ($40.22$) with a tight IQR envelope width ($0.72$) and flat windowed MAD ($\approx 0.2 - 0.4$).
  - `occupied_still` (Session D): Direct Line-of-Sight occlusion induces strong attenuation ($10.72$ median amplitude) while retaining a narrow IQR band ($0.62$).
  - `occupied_moving` (Session E): Moderate attenuation ($13.40$ median amplitude) accompanied by substantial temporal fluctuation, expanding the IQR band width to $6.13$ and causing windowed MAD spikes up to $4 - 8$.
- **Saved Visual Artifacts:** Multi-panel publication figures (`final_figure.png`, `final_figure.pdf`) and the processed window time series (`temporal_series.csv`) were exported to `outputs/pilot/figures/`.
