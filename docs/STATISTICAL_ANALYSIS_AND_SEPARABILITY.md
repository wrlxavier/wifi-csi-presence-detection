# Statistical Analysis and Class Separability

This document details the exploratory data analysis, class separability investigations, dimensionality reduction analyses, and methodological findings established in [separability_figures.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_figures.ipynb) and [separability_lda.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb).

---

## 1. Methodological Breakthrough: Temporal vs. Cross-Subcarrier Dispersion

A key insight during early exploratory analysis was the distinction between channel frequency-selectivity and human-induced temporal perturbation.

### The Pitfall of Cross-Subcarrier Dispersion

An initial exploratory attempt computed the Interquartile Range ($Q_{75} - Q_{25}$) across all 162 subcarriers at each sample instant $t$:

$$\text{IQR}_{\text{cross}}(t) = Q_{75}^{(k)}(A_k(t)) - Q_{25}^{(k)}(A_k(t))$$

**Why this was flawed**:
Indoor wireless multipath creates natural frequency-selective fading. Certain subcarriers experience constructive interference (high amplitude), while others experience destructive interference (low amplitude), even in a completely vacant room. Computing dispersion across subcarriers measured this static frequency response rather than human dynamics, obscuring the true physical presence effect.

### The Temporal Aggregation Solution

The methodology was restructured into a two-stage temporal aggregation:
1. **Cross-Subcarrier Median Level**: At each packet $t$, compute the median amplitude across all 162 valid subcarriers to establish the instantaneous channel baseline:
   $$M(t) = \text{median}_{k \in \mathcal{K}_{\text{shared}}} (A_k(t))$$
2. **Temporal Rolling IQR**: Compute the IQR of the scalar time series $M(t)$ within a rolling window of 30 samples ($\approx 1.0\text{ second}$ at 30 Hz):
   $$\text{IQR}_{\text{temporal}}(t) = Q_{75}^{(\tau \in [t-15, t+15])}(M(\tau)) - Q_{25}^{(\tau \in [t-15, t+15])}(M(\tau))$$
3. **Windowed Subcarrier MAD**: Compute the Mean Absolute Deviation over 2.0-second non-overlapping windows for each subcarrier, then take the median across subcarriers.

This formulation isolates true physical perturbations:
- **Empty room**: Flat median amplitude line with a narrow, near-zero temporal IQR band and minimal MAD.
- **Occupied still**: Clear low-frequency respiratory baseline modulation and elevated temporal dispersion.
- **Occupied moving**: Violent multi-subcarrier phase shifts, wide temporal IQR bands, and prominent MAD peaks.

---

## 2. Dimensionality Reduction

### Principal Component Analysis (PCA)

PCA was applied across the 648 extracted features (1,200 windows from Pilot sessions C, D, E, and F):

| Component Subset | Cumulative Variance Explained |
|---|---|
| First 2 Principal Components (PC1, PC2) | 86.3% |
| First 10 Principal Components | 95.8% |
| First 50 Principal Components | 98.3% |

Key observations from 2D PCA projections:
- The first two principal components capture over 86% of total feature variance.
- Classes form distinct geometric clusters in the PC1-PC2 plane.
- The 2-sigma (95.4% confidence) ellipsoids for Empty and Occupied conditions exhibit minimal overlap, proving that presence information dominates the feature matrix.

### Linear Discriminant Analysis (LDA)

While PCA maximizes total variance regardless of class labels, LDA computes optimal projections that maximize between-class variance relative to within-class variance:

$$J(\mathbf{w}) = \frac{\mathbf{w}^T \mathbf{S}_B \mathbf{w}}{\mathbf{w}^T \mathbf{S}_W \mathbf{w}}$$

#### Binary Presence Projection (1D LDA)
- The 1D LDA projection collapses the 648 features onto a single discriminant axis.
- Discriminant scores span from -9.67 to +9.10.
- Class distributions form a completely bimodal distribution with zero overlap between empty and occupied samples.

#### 3-Class Condition Projection (2D LDA)
- Projecting onto the LD1-LD2 subspace separates the dataset into three distinct clusters:
  1. `empty` (clustered tightly near negative LD1).
  2. `occupied_still` (intermediate LD1, moderate dispersion).
  3. `occupied_moving` (high positive LD1 and high LD2 spread).
- Demonstrates that the feature set not only detects presence but also discriminates the degree of physical activity.

---

## 3. Subcarrier Discriminability and ANOVA F-Tests

To evaluate which subcarriers and statistical descriptors provide the highest discriminative power, a One-Way Analysis of Variance (ANOVA) was conducted across all 162 valid subcarriers:

$$F = \frac{\text{Between-class variance}}{\text{Within-class variance}} = \frac{\text{MSB}}{\text{MSW}}$$

### Key Findings from ANOVA Heatmaps

1. **Top Feature Descriptor**: Mean Absolute Deviation (`mad`) and Variance (`var`) achieved the highest overall F-statistics ($F > 500$ on sensitive subcarriers), outperforming Dynamic Range.
2. **Frequency-Selective Sensitivity**:
   - Subcarriers situated adjacent to deep multipath fading notches exhibit the largest relative amplitude swings when human tissue reflects or scatters energy into that notch.
   - Band edge subcarriers (near lower and upper HT40 limits) demonstrated heightened sensitivity to multipath changes.
3. **Statistical Significance**: All 162 shared subcarriers exhibited statistically significant between-class differences ($p < 10^{-15}$), confirming the validity of multi-subcarrier statistical pooling.

---

## 4. Summary of Analytical Artifacts

The analysis notebooks exported publication-grade figures utilizing color-blind safe palettes (Okabe-Ito):

| Artifact | Source Notebook | Description |
|---|---|---|
| `final_figure.png` / `final_figure.pdf` | [separability_figures.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_figures.ipynb) | Dual-panel time series showing median CSI amplitude with temporal IQR band and windowed MAD step plot |
| `temporal_series.csv` | [separability_figures.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_figures.ipynb) | Aggregated window-level statistics for condition comparison |
| `sep_01_pca.png` | [separability_lda.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb) | PCA scree plot and 2D cluster scatter with 95.4% confidence ellipses |
| `sep_02_lda.png` | [separability_lda.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb) | 1D binary LDA histogram and 2D three-class projection scatter |
| `sep_03_feature_distributions.png` | [separability_lda.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb) | Violin plots of mean subcarrier variance, MAD, range, and IQR |
| `sep_04_discriminability_heatmap.png` | [separability_lda.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb) | Per-subcarrier ANOVA F-statistic heatmap across all 4 feature types |
