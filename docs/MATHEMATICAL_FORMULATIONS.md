# Mathematical Formulations and Evaluation Metrics

This document compiles the foundational mathematical equations, signal processing transformations, statistical dispersion descriptors, hypothesis tests, and evaluation metrics computed across the project's Jupyter Notebooks. It serves as a unified, rigorous reference for the monograph.

---

## 1. Physical Layer & Baseband Signal Transformations

### 1.1 Complex Channel Frequency Response (CFR) Reconstruction
* **Notebooks:** [`eda_first_test.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb), [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb), [`pipeline_v1.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb)
* **Implementation:** [`raw_iq_to_complex`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/parsing/csi_decoder.py#L56-L65)

In IEEE 802.11n HT40 mode, each captured CSI packet payload consists of 384 signed 8-bit integers $\mathbf{D} \in \mathbb{Z}^{384}$ representing $N_{\text{raw}} = 192$ complex subcarrier pairs interleaved as $[\text{Im}_0, \text{Re}_0, \text{Im}_1, \text{Re}_1, \dots, \text{Im}_{191}, \text{Re}_{191}]$. For subcarrier $k \in \{0, 1, \dots, 191\}$:

$$\operatorname{Re}(H_k) = \mathbf{D}[2k + 1], \quad \operatorname{Im}(H_k) = \mathbf{D}[2k]$$

$$H(k) = \operatorname{Re}(H_k) + j \cdot \operatorname{Im}(H_k) = \mathbf{D}[2k + 1] + j \cdot \mathbf{D}[2k]$$

### 1.2 Instantaneous Euclidean Amplitude & Raw Phase Angle
* **Implementation:** [`compute_amplitudes`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/signal/amplitudes.py#L24-L26)

From each complex Channel Frequency Response coefficient $H(k)$, the physical observables are derived:

$$A(k) = |H(k)| = \sqrt{(\operatorname{Re}(H_k))^2 + (\operatorname{Im}(H_k))^2} = \sqrt{(\mathbf{D}[2k+1])^2 + (\mathbf{D}[2k])^2}$$

$$\phi(k) = \arg(H(k)) = \operatorname{atan2}(\operatorname{Im}(H_k), \operatorname{Re}(H_k)) = \operatorname{atan2}(\mathbf{D}[2k], \mathbf{D}[2k+1])$$

### 1.3 Subcarrier Validity & Shared Mask Calculation
* **Notebooks:** [`pipeline_v0.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb), [`pipeline_v1.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb)
* **Implementation:** [`detect_valid_subcarriers`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/signal/subcarrier_filter.py#L7-L16), [`compute_shared_valid_mask`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/signal/subcarrier_filter.py#L18-L39)

Out of 192 reported bins, non-informative carriers (guard bands and DC center nulls) have low power. A carrier $k$ is valid for session $s$ if its temporal mean amplitude exceeds a threshold $\tau = 0.5$:

$$\mathcal{M}_s(k) = \mathbb{I}\left( \frac{1}{N_s}\sum_{t=1}^{N_s} A_{s, t}(k) > \tau \right), \quad \text{where } \tau = 0.5$$

The unified physical subcarrier mask across all $S$ sessions is the logical conjunction:

$$\mathcal{M}_{\text{shared}} = \bigcap_{s=1}^S \mathcal{M}_s \implies \sum_{k=0}^{191} \mathcal{M}_{\text{shared}}(k) = 162 \text{ valid subcarriers}$$

*(30 bins pruned: 26 dead guard/DC carriers + 4 unstable boundary bins).*

---

## 2. Temporal Link Quality & Sampling Metrics

### 2.1 Inter-Packet Interval (IPI) & Sampling Rates
* **Notebooks:** [`csi_collector_v2.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb), [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb)

For a session of $N$ packets arriving at host timestamps $t_1, t_2, \dots, t_N$:

$$\Delta t_i = t_i - t_{i-1}, \quad \forall i \in \{2, 3, \dots, N\}$$

* **Effective Sampling Rate ($f_{\text{eff}}$):**
  $$f_{\text{eff}} = \frac{N - 1}{t_N - t_1}$$

* **Median Sampling Rate ($f_{\text{med}}$):**
  $$f_{\text{med}} = \frac{1}{\operatorname{median}(\{\Delta t_i \mid \Delta t_i > 0\})}$$

### 2.2 Packet Arrival Jitter
* **Notebooks:** [`eda_pilot.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb), [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb)

Quantified as the sample standard deviation of inter-packet arrival intervals:

$$\sigma_{\Delta t} = \sqrt{\frac{1}{N - 2}\sum_{i=2}^N (\Delta t_i - \overline{\Delta t})^2}, \quad \text{where } \overline{\Delta t} = \frac{1}{N-1}\sum_{i=2}^N \Delta t_i$$

### 2.3 Network Gap Detection & Packet Loss Estimation
* **Notebooks:** [`eda_pilot.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb), [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb), [`eda_first_test.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb)

* **Packet Gap Threshold:** With nominal period $T_{\text{nom}} = \frac{1}{30\text{ Hz}} \approx 33.33\text{ ms}$:
  $$\Delta t_{\text{gap}} = 2.5 \times T_{\text{nom}} = 83.33\text{ ms}$$
  Any interval $\Delta t_i > \Delta t_{\text{gap}}$ is flagged as an arrival stall event.

* **Nominal Expected Packet Count:**
  $$N_{\text{expected}} = \left\lfloor \frac{t_N - t_1}{T_{\text{nom}}} \right\rceil$$

* **Rejected Alternative (Naive Difference Estimator):**
  $$\text{Loss}_{\text{naive}} (\%) = \max\left(0, \frac{N_{\text{expected}} - N}{N_{\text{expected}}}\right) \times 100\%$$
  > [!NOTE]
  > **Rejection Rationale:** The naive estimator computes a global count deficit against nominal clock. However, physical crystal oscillators on the ESP32-S3 transmitter exhibit natural frequency tolerances and host OS receive jitter (e.g., transmitting at ~29.8 Hz instead of exactly 30.0 Hz). Over a 10-minute session ($N \approx 18{,}000$ packets), this clock drift accumulates an artificial deficit of ~120 packets ($\approx 0.67\%$ apparent loss), despite zero dropped packets.

* **Implemented Gap-Accumulation Formulation:**
  To guarantee robustness against oscillator drift, packet loss is estimated strictly across flagged arrival gap intervals ($\Delta t_i > \Delta t_{\text{gap}}$):
  $$N_{\text{lost, est}} = \max\left(0, \, \left\lfloor \sum_{i \in \text{gaps}} \frac{\Delta t_i}{T_{\text{nom}}} \right\rceil - |\text{gaps}|\right)$$
  $$\text{Loss } (\%) = \frac{N_{\text{lost, est}}}{N_{\text{expected}}} \times 100\%$$
  This formulation isolates physical transmission dropout events from benign crystal frequency drift.

### 2.4 Mean Received Signal Strength Indicator (RSSI)
* **Notebooks:** [`csi_collector_v2.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb), [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb)

$$\mu_{\text{RSSI}} = \frac{1}{N}\sum_{i=1}^N \text{RSSI}_i, \quad \sigma_{\text{RSSI}} = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (\text{RSSI}_i - \mu_{\text{RSSI}})^2}$$

---

## 3. Windowing & Statistical Feature Extraction

### 3.1 Non-Overlapping Temporal Segmentation
* **Notebooks:** [`pipeline_v0.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb), [`pipeline_v1.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb)
* **Implementation:** [`segment_non_overlapping_windows`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/signal/segmentation.py#L64-L130)

Active condition samples within $[T_1, T_2]$ are segmented into contiguous windows of duration $T_w = 2.0\text{ s}$ with zero overlap (step size $S = T_w = 2.0\text{ s}$):

$$W_m = \{t \mid t_{\text{start}, m} \le t < t_{\text{start}, m} + T_w\}, \quad t_{\text{start}, m+1} = t_{\text{start}, m} + T_w$$

* **Window Ingestion Condition:**
  A window is accepted if and only if:
  $$|W_m| \ge \max\left(5, \, \lfloor 0.5 \times f_{\text{eff}} \times T_w \rfloor\right)$$

### 3.2 The Four Core Statistical Dispersion Descriptors
* **Notebooks:** [`pipeline_v1.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb), [`separability_lda.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb)
* **Implementation:** [`extract_official_features`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/features/statistical.py#L24-L50)

For each valid subcarrier $k \in \{0, 1, \dots, 161\}$ and window $W$ containing $M$ amplitude observations $\{A_1, A_2, \dots, A_M\}$:

1. **Unbiased Sample Variance (`var`):**
   $$\text{var}_k = \frac{1}{M - 1} \sum_{m=1}^M \left(A_m - \overline{A}\right)^2, \quad \text{where } \overline{A} = \frac{1}{M}\sum_{m=1}^M A_m$$

2. **Mean Absolute Deviation (`mad`):**
   $$\text{mad}_k = \frac{1}{M} \sum_{m=1}^M \left|A_m - \overline{A}\right|$$

3. **Peak-to-Peak Range (`range`):**
   $$\text{range}_k = \max_{m \in W}(A_m) - \min_{m \in W}(A_m)$$

4. **Interquartile Range (`iqr`):**
   $$\text{iqr}_k = Q_{75}(A) - Q_{25}(A)$$

* **Tabular Dimensionality:**
  $$D = N_{\text{sub}} \times 4 = 162 \times 4 = 648 \text{ features per window}$$

> [!NOTE]
> **Implementation Nuance on MAD (Official Pipeline vs. Exploratory Figures):**
> In the official machine learning feature extraction pipeline ([`statistical.py`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/features/statistical.py#L8-L11)), `mad` is strictly the **Mean Absolute Deviation around the sample mean** ($\frac{1}{M}\sum |A_m - \overline{A}|$). In the preliminary exploratory visualization notebook ([`separability_figures.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_figures.ipynb#L13)), the **median absolute deviation around the median** ($\operatorname{median}(|A_m - \operatorname{median}(A)|)$) was used solely for qualitative graphic plots to minimize visual outliers. The machine learning pipeline, tabular datasets, and models exclusively use the sample mean formulation presented above.

### 3.3 Zero-Leakage Standardization
* **Notebooks:** [`02_preprocessing.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/02_preprocessing.ipynb)

Features are normalized via `StandardScaler`, fitted exclusively on the training matrix $\mathbf{X}_{\text{train}} \in \mathbb{R}^{N_{\text{train}} \times 648}$:

$$\mu_j = \frac{1}{N_{\text{train}}} \sum_{i=1}^{N_{\text{train}}} X_{i, j}, \quad \sigma_j = \sqrt{\frac{1}{N_{\text{train}}} \sum_{i=1}^{N_{\text{train}}} (X_{i, j} - \mu_j)^2}$$

$$\tilde{X}_{i, j} = \frac{X_{i, j} - \mu_j}{\sigma_j}$$

---

## 4. Statistical Hypothesis Testing & Dimensionality Reduction

### 4.1 Subcarrier Quality & Anomaly Profiling
* **Notebooks:** [`eda_pilot.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb), [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb)

* **Coefficient of Variation (CV):**
  $$\text{CV}_k = \frac{\sigma_k}{\mu_k}, \quad \text{flagged as noisy if } \text{CV}_k > \text{Percentile}_{90}$$

* **Fisher Excess Kurtosis:**
  $$\gamma_{2, k} = \frac{\frac{1}{N}\sum_{t=1}^N (A_{k, t} - \mu_k)^4}{\sigma_k^4} - 3, \quad \text{flagged as anomalous if } |\gamma_{2, k}| > 5$$

* **Subcarrier Discriminability Ratio:**
  $$\text{Ratio}_k = \frac{\sigma^2_{k, \text{occupied}}}{\max\left(\sigma^2_{k, \text{empty}}, \, 10^{-4}\right)}$$

### 4.2 Effect Size: Cohen's $d$
* **Notebooks:** [`eda_first_test.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb), [`separability_lda.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb)

Measures the standardized difference between two group means ($\overline{x}_1, \overline{x}_2$):

$$d = \frac{\overline{x}_1 - \overline{x}_2}{s_{\text{pooled}}}, \quad \text{where } s_{\text{pooled}} = \sqrt{\frac{(n_1 - 1)s_1^2 + (n_2 - 1)s_2^2}{n_1 + n_2 - 2}}$$

> [!NOTE]
> **Implementation Nuance on Pooled Variance:**
> The equation above specifies the canonical unbiased pooled standard deviation with degrees-of-freedom weighting ($(n_1 - 1)s_1^2 + (n_2 - 1)s_2^2$). In [`separability_lda.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb#L8), NumPy's `x.var()` default (`ddof=0`) is called on group arrays before scaling by $(n_i - 1)$. Because group sample sizes are large ($n_i \ge 400$ windows), the finite-sample difference between $\frac{n_i - 1}{n_i} \approx 0.998$ produces a negligible numerical effect ($< 0.2\%$), with the equation above representing the exact, standard analytical definition.

### 4.3 Principal Component Analysis (PCA)
* **Notebooks:** [`separability_lda.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb)

For standardized centered matrix $\tilde{\mathbf{X}} \in \mathbb{R}^{N \times D}$, eigendecomposition of the empirical covariance matrix $\mathbf{\Sigma} = \frac{1}{N-1}\tilde{\mathbf{X}}^T\tilde{\mathbf{X}}$ yields:

$$\mathbf{\Sigma} \mathbf{v}_i = \lambda_i \mathbf{v}_i, \quad \lambda_1 \ge \lambda_2 \ge \dots \ge \lambda_D \ge 0$$

$$\text{EVR}_i = \frac{\lambda_i}{\sum_{j=1}^D \lambda_j}$$

*(First 2 components explain $86.3\%$ of total feature variance).*

### 4.4 Linear Discriminant Analysis (LDA)
* **Notebooks:** [`separability_lda.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb)

Finds linear projection $\mathbf{w}$ maximizing between-class scatter relative to within-class scatter:

$$\mathbf{S}_B = \sum_{c \in \{0, 1\}} N_c (\boldsymbol{\mu}_c - \boldsymbol{\mu})(\boldsymbol{\mu}_c - \boldsymbol{\mu})^T$$

$$\mathbf{S}_W = \sum_{c \in \{0, 1\}} \sum_{i \in c} (\mathbf{x}_i - \boldsymbol{\mu}_c)(\mathbf{x}_i - \boldsymbol{\mu}_c)^T$$

$$\mathbf{w}^* = \arg\max_{\mathbf{w}} \frac{\mathbf{w}^T \mathbf{S}_B \mathbf{w}}{\mathbf{w}^T \mathbf{S}_W \mathbf{w}} = \mathbf{S}_W^{-1}(\boldsymbol{\mu}_1 - \boldsymbol{\mu}_0)$$

*(Binary 1D projection yields Cohen's $d = 12.643$).*

### 4.5 One-Way ANOVA F-Statistic
* **Notebooks:** [`separability_lda.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/03_analysis/separability_lda.ipynb)

Evaluates individual feature discriminability across $K$ classes:

$$F = \frac{\text{MS}_{\text{between}}}{\text{MS}_{\text{within}}} = \frac{\frac{\text{SS}_B}{K - 1}}{\frac{\text{SS}_W}{N - K}} = \frac{\frac{\sum_{c=1}^K N_c (\overline{x}_c - \overline{x})^2}{K - 1}}{\frac{\sum_{c=1}^K \sum_{i=1}^{N_c} (x_{c, i} - \overline{x}_c)^2}{N - K}}$$

---

## 5. Model Evaluation & Benchmark Metrics

### 5.1 Binary Confusion Matrix
* **Implementation:** [`false_alarm_rate`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/evaluation/metrics.py#L7-L21), [`compute_metrics`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/evaluation/metrics.py#L23-L35)

With True Positive ($\text{TP}$), True Negative ($\text{TN}$), False Positive ($\text{FP}$), and False Negative ($\text{FN}$), with positive class = occupied ($1$) and negative class = empty ($0$):

* **Classification Accuracy:**
  $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$

* **Sensitivity (Recall / True Positive Rate - TPR):**
  $$\text{Sensitivity} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$

* **Specificity (True Negative Rate - TNR):**
  $$\text{Specificity} = \frac{\text{TN}}{\text{TN} + \text{FP}}$$

* **False Alarm Rate (FAR / False Positive Rate - FPR):**
  $$\text{FAR} = \frac{\text{FP}}{\text{FP} + \text{TN}} = 1 - \text{Specificity}$$

* **Precision (Positive Predictive Value - PPV):**
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$

### 5.2 $F_1$-Score Formulations
* **Implementation:** [`f1_score(average='macro')`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/evaluation/metrics.py#L33)

* **Per-Class $F_1$-Score:**
  $$F_{1, c} = 2 \times \frac{\text{Precision}_c \times \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c} = \frac{2 \text{TP}_c}{2 \text{TP}_c + \text{FP}_c + \text{FN}_c}$$

* **Macro-Averaged $F_1$-Score (Primary Project Optimization Metric):**
  $$\text{Macro } F_1 = \frac{1}{C} \sum_{c=1}^C F_{1, c} = \frac{F_{1, \text{empty}} + F_{1, \text{occupied}}}{2}$$

* **Weighted $F_1$-Score:**
  $$\text{Weighted } F_1 = \sum_{c=1}^C \frac{N_c}{N} F_{1, c}$$

### 5.3 Cross-Validation & Standard Error
* **Notebooks:** [`03_training.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/03_training.ipynb), [`06_feature_minimization.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/06_feature_minimization.ipynb)

For $K$-fold cross-validation scores $\{F_{1, 1}, F_{1, 2}, \dots, F_{1, K}\}$:

$$\overline{F}_1 = \frac{1}{K}\sum_{k=1}^K F_{1, k}, \quad s_{\text{folds}} = \sqrt{\frac{1}{K - 1}\sum_{k=1}^K \left(F_{1, k} - \overline{F}_1\right)^2}$$

$$\text{SE} = \frac{s_{\text{folds}}}{\sqrt{K}}$$

---

## 6. Subcarrier Minimization & Generalization

### 6.1 Physical Subcarrier Group Importance
* **Notebooks:** [`06_feature_minimization.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/06_feature_minimization.ipynb)

Permutation feature importance is grouped across all 4 metrics for each physical subcarrier index $j$:

$$I(\text{sc}_j) = \sum_{m \in \{\text{var, mad, range, iqr}\}} \left| \text{Score}_{\text{baseline}} - \text{Score}_{\text{permuted}(j, m)} \right|$$

### 6.2 The One-Standard-Error (1-SE) Stopping Rule
* **Notebooks:** [`06_feature_minimization.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/06_feature_minimization.ipynb)

The minimal optimal subcarrier subset count $N^*$ is the smallest set satisfying:

$$N^* = \min \left\{ N \in [5, \dots, 162] \;\middle|\; \overline{\text{F1}}_N \ge \overline{\text{F1}}_{\text{full}} - \text{SE}(\text{F1}_{\text{full}}) \right\}$$

$$\text{Threshold}_{1\text{-SE}} = 0.5606 - 0.1124 = 0.4482 \implies N^* = 5 \text{ subcarriers (20 features)}$$

### 6.3 Feature Dimensionality Reduction Ratio
* **Notebooks:** [`06_feature_minimization.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/06_feature_minimization.ipynb)

$$\text{Reduction } (\%) = \left( 1 - \frac{N^* \times 4}{N_{\text{full}} \times 4} \right) \times 100\% = \left( 1 - \frac{20}{648} \right) \times 100\% = 96.91\%$$

### 6.4 Cross-Domain Generalization Degradation
* **Notebooks:** [`02_model_evaluation.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/05_generalization/02_model_evaluation.ipynb)

$$\Delta F_1 = F_{1, \text{OOD}} - F_{1, \text{in-domain}}$$
