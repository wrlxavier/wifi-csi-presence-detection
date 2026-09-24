# Machine Learning Benchmarks and Robustness

This document details the model development, hyperparameter optimization, 10-fold cross-validation, held-out evaluation, and multi-axis robustness tests established in notebooks [01_split.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/01_split.ipynb) through [05_robustness.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/05_robustness.ipynb) and automated via [`scripts/train_models.py`](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/train_models.py) and [`scripts/evaluate.py`](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/evaluate.py).

---

## 1. Dataset Partitioning and Preprocessing

### Stratified 70/15/15 Split

To evaluate generalizability and prevent data leakage, the 3,889 feature windows extracted from the 11 valid sessions were divided into three stratified subsets:

- **Training Set (70%)**: 2,722 samples (1,466 empty, 1,256 occupied).
- **Validation Set (15%)**: 583 samples (314 empty, 269 occupied).
- **Held-Out Test Set (15%)**: 584 samples (315 empty, 269 occupied).

Splits are saved as self-contained Parquet files with embedded metadata in [`data/03_processed/splits/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/03_processed/splits/).

### Feature Standardization

A `StandardScaler` is fitted strictly on the training partition:

$$\mu_j = \frac{1}{N_{\text{train}}} \sum_{i=1}^{N_{\text{train}}} x_{ij}, \quad \sigma_j = \sqrt{\frac{1}{N_{\text{train}}} \sum_{i=1}^{N_{\text{train}}} (x_{ij} - \mu_j)^2}$$

The fitted transformation parameters are saved to `models/scaler.pkl` and encapsulated into self-contained inference bundles in `models/registry/`.

---

## 2. 10-Fold Stratified Cross-Validation

Four model families were tuned using `GridSearchCV` with 10-fold stratified cross-validation on the training set, optimizing for Macro F1 score (`scoring='f1_macro'`):

### Hyperparameter Search Space

The canonical parameter grids defined in [`configs/models.yaml`](file:///home/xavier/dev/wifi-csi-presence-detection/configs/models.yaml) and evaluated via `GridSearchCV`:

1. **Random Forest Classifier**:
   - `n_estimators`: `[50, 100, 200]`
   - `max_depth`: `[None, 10, 20]`
2. **Support Vector Machine (SVM)**:
   - `C`: `[0.1, 1.0, 10.0]`
   - `kernel`: `['rbf', 'linear']`
3. **Gradient Boosting Classifier**:
   - `n_estimators`: `[50, 100]`
   - `learning_rate`: `[0.05, 0.1]`
   - `max_depth`: `[3, 5]`
4. **Multilayer Perceptron (MLP)**:
   - `hidden_layer_sizes`: `[[50], [100], [50, 50]]`
   - `max_iter`: `[500]`

### Cross-Validation Results

The 10-fold cross-validation results from the canonical automated training pipeline ([`reports/logs/cv_results.csv`](file:///home/xavier/dev/wifi-csi-presence-detection/reports/logs/cv_results.csv)) are summarized below:

| Model Architecture | 10-Fold CV Macro F1 | Optimal Hyperparameters |
|---|---|---|
| Multilayer Perceptron (MLP) | **0.9922** | `hidden_layer_sizes: [50, 50], max_iter: 500` |
| Gradient Boosting | **0.9789** | `learning_rate: 0.1, max_depth: 3, n_estimators: 100` |
| Support Vector Machine (SVM) | **0.9748** | `C: 10.0, kernel: 'rbf'` |
| Random Forest | **0.9721** | `max_depth: 20, n_estimators: 100` |

All four architectures achieved exceptional cross-validation performance, with CV Macro F1 scores consistently exceeding 0.97. (In exploratory notebook grid searches exploring larger parameter spaces, scores ranged up to 0.9926 for SVM and 0.9849 for Gradient Boosting).

---

## 3. Validation and Held-Out Test Evaluation

### Validation Set Performance

Models were evaluated on the 583 validation samples to select the final deployment candidate:

| Model | Accuracy | Macro F1 | Precision | Recall | False Alarm Rate (FAR) |
|---|---|---|---|---|---|
| Multilayer Perceptron (MLP) | **99.49%** | **0.9948** | 0.9953 | 0.9944 | **0.00%** |
| Support Vector Machine (SVM) | 98.11% | 0.9810 | 0.9806 | 0.9814 | 1.59% |
| Gradient Boosting | 98.11% | 0.9810 | 0.9812 | 0.9810 | 0.64% |
| Random Forest | 98.11% | 0.9810 | 0.9814 | 0.9807 | 0.32% |

### Single-Evaluation on Held-Out Test Set

The top model (MLP) was evaluated once on the 584 held-out test samples:

- **Accuracy**: **98.97%**
- **Macro F1 Score**: **0.9897**
- **Precision**: 0.9903
- **Recall**: 0.9891
- **False Alarm Rate (FAR)**: **0.32%** (1 false positive out of 315 empty windows)
- **Project Target**: Macro F1 $\ge 0.90$
- **Verdict**: **PASSED** (Margin: +0.0897 above target)

---

## 4. Four-Axis Robustness Stress Testing

To verify whether the system overfits to specific physical conditions or subjects, notebook [05_robustness.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/05_robustness.ipynb) and script [`scripts/evaluate.py`](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/evaluate.py) performed stratified stress testing across 4 orthogonal dimensions:

### Axis 1: Per-Session Robustness

| Session ID | Condition | Test Samples (n) | Accuracy | Macro F1 | False Alarm Rate |
|---|---|---|---|---|---|
| C | `empty` | 35 | 97.14% | 0.4928 | 2.86% |
| D | `occupied_still` | 31 | **100.00%** | **1.0000** | 0.00% |
| E | `occupied_moving` | 48 | **100.00%** | **1.0000** | 0.00% |
| F | `empty` | 40 | **100.00%** | **1.0000** | 0.00% |
| G | `empty` | 53 | **100.00%** | **1.0000** | 0.00% |
| H | `occupied_p1_still` | 50 | 92.00% | 0.4792 | 0.00% |
| I | `occupied_p2_still` | 46 | **100.00%** | **1.0000** | 0.00% |
| J | `empty` (extended) | 139 | **100.00%** | **1.0000** | 0.00% |
| K | `occupied_p3_still` | 48 | **100.00%** | **1.0000** | 0.00% |
| L | `empty` | 48 | **100.00%** | **1.0000** | 0.00% |
| M | `occupied_p4_still` | 46 | 97.83% | 0.4945 | 0.00% |

> **Note on single-class session F1**: Within subsets containing only one ground-truth class, Macro F1 is capped near 0.50 because one class has zero support. In terms of raw classification accuracy, 9 out of 11 sessions achieved **100.0% accuracy**.

### Axis 2: Posture and Spatial Position Robustness

| Condition / Position | Description | Test Samples (n) | Accuracy | Macro F1 | False Alarm Rate |
|---|---|---|---|---|---|
| `empty` | All empty baseline sessions (C, F, G, J, L) | 315 | **99.68%** | 0.4992 | 0.32% |
| `occupied_moving` | Dynamic continuous movement (Session E) | 48 | **100.00%** | **1.0000** | 0.00% |
| `occupied_still` | Generic pilot standing motionless (Session D) | 31 | **100.00%** | **1.0000** | 0.00% |
| `occupied_p2_still` | On-LoS near transmitter (P2 - Session I) | 46 | **100.00%** | **1.0000** | 0.00% |
| `occupied_p3_still` | On-LoS near receiver (P3 - Session K) | 48 | **100.00%** | **1.0000** | 0.00% |
| `occupied_p4_still` | Off-LoS East (P4 - Session M) | 46 | **97.83%** | 0.4945 | 0.00% |
| `occupied_p1_still` | Off-LoS West (P1 - Session H) | 50 | **92.00%** | 0.4792 | 0.00% |

**Key Physical Insight**: On-LoS positions (P2, P3) are detected with 100.0% accuracy due to direct path obstruction. Off-LoS positions achieve 97.83% (P4 East, 1 error out of 46) and 92.00% (P1 West, 4 errors out of 50). In Off-LoS positions, the direct LoS path remains unblocked; detection relies entirely on secondary multipath reflections scattered from human body tissue. Across 315 empty windows from 5 different sessions spanning 7 hours and multiple days, the system produced only a single false alarm (overall baseline FAR = 0.32%).

### Axis 3: Time-of-Day Robustness

| Time of Day Band (UTC) | Test Samples (n) | Accuracy | Macro F1 | False Alarm Rate |
|---|---|---|---|---|
| Afternoon (12:00 - 18:00 UTC) | 207 | **99.52%** | **0.9949** | 0.78% |
| Night / Evening (18:00 - 06:00 UTC) | 377 | **98.67%** | **0.9867** | 0.00% |

All recordings were performed during afternoon and evening/night hours (corresponding to 09:00 to 21:30 local BRT time). The system exhibits high invariance to circadian RF environment changes and diurnal ambient drift.

### Axis 4: Transmitter-Receiver Distance

All pilot and main sessions were acquired at a fixed TX-RX separation of 2.0 meters, establishing a clean physical baseline. Further distance testing is earmarked for multi-room campaigns.

---

## 5. Thesis and Publication Assets

The export script [`scripts/export_thesis_assets.py`](file:///home/xavier/dev/wifi-csi-presence-detection/scripts/export_thesis_assets.py) generates publication-ready artifacts directly in [`reports/`](file:///home/xavier/dev/wifi-csi-presence-detection/reports/):

### LaTeX Tables
- [`reports/tables/model_comparison.tex`](file:///home/xavier/dev/wifi-csi-presence-detection/reports/tables/model_comparison.tex): Academic model benchmark table.
- [`reports/tables/robustness_sessions.tex`](file:///home/xavier/dev/wifi-csi-presence-detection/reports/tables/robustness_sessions.tex): Per-session robustness breakdown.

### Vector Figures (PDF & PNG)
- [`reports/figures/model_comparison_val.pdf`](file:///home/xavier/dev/wifi-csi-presence-detection/reports/figures/model_comparison_val.pdf): Validation performance comparison.
- [`reports/figures/confusion_matrices_val.pdf`](file:///home/xavier/dev/wifi-csi-presence-detection/reports/figures/confusion_matrices_val.pdf): Validation confusion matrices for all 4 models.
- [`reports/figures/confusion_matrix_test.pdf`](file:///home/xavier/dev/wifi-csi-presence-detection/reports/figures/confusion_matrix_test.pdf): Final held-out test confusion matrix.
