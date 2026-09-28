# Machine Learning Modeling and Evaluation (`04_modeling`)

This document summarizes the end-to-end machine learning modeling lifecycle, hyperparameter optimization, model evaluation, robustness testing, and feature minimization implemented across the six notebooks in [`notebooks/04_modeling/`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/):
- [`01_split.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/01_split.ipynb): Dataset partitioning into stratified train, validation, and hold-out test sets.
- [`02_preprocessing.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/02_preprocessing.ipynb): Leakage-free feature scaling using `StandardScaler`.
- [`03_training.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/03_training.ipynb): 10-fold cross-validation and hyperparameter grid search across four model architectures.
- [`04_evaluation.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/04_evaluation.ipynb): Validation selection and single blind evaluation on the hold-out test set.
- [`05_robustness.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/05_robustness.ipynb): Fine-grained robustness evaluation across sessions, postures, and time-of-day.
- [`06_feature_minimization.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/04_modeling/06_feature_minimization.ipynb): Subcarrier ablation, 1-SE rule stopping, and lightweight model family optimization.

---

## 1. Dataset Partitioning & Preprocessing

### 1.1 Stratified Splits (`01_split.ipynb`)
The processed feature table (`features_ht40.parquet`, 3,900 windows $\times$ 657 columns) is partitioned into three disjoint subsets:
- **Training Set (70%):** 2,730 windows (1,470 empty / 1,260 occupied). Saved to `data/03_processed/splits/train.parquet`.
- **Validation Set (15%):** 585 windows (315 empty / 270 occupied). Saved to `data/03_processed/splits/val.parquet`.
- **Test Set (15%):** 585 windows (315 empty / 270 occupied). Saved to `data/03_processed/splits/test.parquet`.

The hold-out test set remains strictly isolated until final blind verification.

### 1.2 Feature Scaling (`02_preprocessing.ipynb`)
To prevent data leakage, a `StandardScaler` is fitted exclusively on the 2,730 training samples across the 648 feature columns and serialized to `models/scaler.pkl`. It is subsequently used to transform validation and test sets.

---

## 2. Model Training & Hyperparameter Tuning (`03_training.ipynb`)

Four supervised classification architectures were trained using 10-fold stratified cross-validation on the training set, optimizing for Macro F1 (`scoring='f1_macro'`):

| Model Architecture | Optimal Hyperparameters | 10-Fold CV Macro F1 |
| :--- | :--- | :---: |
| **Random Forest** | `{'max_depth': 20, 'n_estimators': 200}` | 0.9730 |
| **Support Vector Machine (SVM-RBF)** | `{'C': 10, 'gamma': 0.01}` | 0.9926 |
| **Gradient Boosting (GBDT)** | `{'learning_rate': 0.1, 'max_depth': 3, 'n_estimators': 200}` | 0.9849 |
| **Multi-Layer Perceptron (MLP)** | `{'alpha': 0.0001, 'hidden_layer_sizes': (128, 64)}` | 0.9911 |

---

## 3. Model Evaluation & Benchmark Verification (`04_evaluation.ipynb`)

### 3.1 Validation Performance ($N = 585$)
All candidate estimators were evaluated on the validation set to select the production model:

| Model Architecture | Accuracy | Macro F1 | False Alarm Rate (FAR) | Selection Status |
| :--- | :---: | :---: | :---: | :---: |
| **Gradient Boosting** | **98.63%** | **0.9862** | **0.00%** | **Selected Best Model** |
| **SVM (RBF)** | 98.29% | 0.9828 | 1.59% | Runner-up |
| **Random Forest** | 98.12% | 0.9810 | 0.32% | Candidate |
| **MLP** | 97.95% | 0.9793 | 0.32% | Candidate |

### 3.2 Single Blind Hold-Out Test Evaluation ($N = 585$)
The selected **Gradient Boosting** model was evaluated once on the untouched hold-out test set:
- **Test Accuracy:** **99.49%**
- **Test Macro F1:** **0.9948**
- **Test False Alarm Rate:** **0.00%**
- **Project Benchmark Criterion ($\text{F1} \ge 0.90$):** **PASS**

---

## 4. Robustness & Subgroup Analysis (`05_robustness.ipynb`)

The top-performing model was subjected to sub-cohort evaluation on the test set:

1. **Per-Session Robustness:**
   - 10 out of 11 sessions achieved **100% Accuracy and 1.0000 Macro F1** (Sessions C, D, E, F, G, I, J, K, L, M) with 0.0% false alarms.
   - Session H (`occupied_p1_still`, off-LoS 30 cm West): Achieved **93.18% Accuracy** and **0.4824 Macro F1**, confirming that static presence outside the direct Line of Sight represents the primary challenge for the classifier.
2. **Time-of-Day Robustness:**
   - Morning ($N = 133$): Accuracy = **100.0%**, Macro F1 = **1.0000**
   - Afternoon ($N = 209$): Accuracy = **100.0%**, Macro F1 = **1.0000**
   - Evening ($N = 243$): Accuracy = **98.77%**, Macro F1 = **0.9876**
3. **Link Distance:** Constant at 2.0 m LoS across all benchmark sessions.

---

## 5. Feature & Subcarrier Minimization (`06_feature_minimization.ipynb`)

To enable lightweight inference on resource-constrained embedded microcontrollers (such as the ESP32-S3), an ablation experiment was performed to minimize the number of required physical subcarriers.

### 5.1 Methodology & Stopping Rule
- **Physical Subcarrier Grouping:** Subcarriers are pruned in physical units of 4 features (`var`, `mad`, `range`, `iqr`).
- **Subcarrier Ranking:** Computed via out-of-fold Permutation Importance using 5-fold session-isolated cross-validation (`StratifiedGroupKFold` grouped by `session_id`).
- **Stopping Criterion (1-SE Rule):** Selects the smallest subcarrier set $N^*$ whose cross-validation score falls within one standard error of the full baseline:
  $$\overline{\text{F1}}_{N^*} \ge \overline{\text{F1}}_{\text{full}} - \text{SE}(\text{F1}_{\text{full}})$$

### 5.2 Optimal Subcarrier Subset
- **Optimal Subcarrier Count ($N^*$):** **5 subcarriers** (`sc041`, `sc040`, `sc042`, `sc047`, `sc012`), corresponding to raw OFDM indices `[48, 47, 49, 54, 18]`.
- **Dimensionality Reduction:** Slashes feature count from 648 down to **20 features** (**96.91% reduction**).
- **Cross-Validation Performance:** Out-of-fold CV Macro F1 improved from $0.5606 \pm 0.1124$ (full 648 features) to **$0.6474$** (reduced 20 features), indicating that discarding noisy, uninformative subcarriers effectively mitigates multipath overfitting.

### 5.3 Blind Test Benchmark: Full Baseline vs. Light Model Family

| Architecture | Model Variant | Subcarriers | Feature Count | Reduction | Test Macro F1 | Test Accuracy | FAR | Inference Latency | Model Size |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gradient Boosting** | Full Baseline | 162 | 648 | 0.0% | **0.9862** | 98.63% | 0.95% | 0.0078 ms | 1,604.2 KB |
| **Gradient Boosting** | **Light (Top)** | **5** | **20** | **96.91%** | **0.9759** | **97.61%** | **0.63%** | **0.0043 ms** | **389.9 KB** |
| **Random Forest** | Full Baseline | 162 | 648 | 0.0% | 0.9845 | 98.46% | 0.00% | 0.0447 ms | 1,278.6 KB |
| **Random Forest** | Light | 5 | 20 | 96.91% | 0.9724 | 97.26% | 1.27% | 0.0420 ms | 1,693.1 KB |
| **MLP** | Full Baseline | 162 | 648 | 0.0% | 0.9828 | 98.29% | 0.63% | 0.0109 ms | 2,173.9 KB |
| **MLP** | Light | 5 | 20 | 96.91% | 0.9519 | 95.21% | 4.44% | 0.0035 ms | 268.3 KB |
| **SVM (RBF)** | Full Baseline | 162 | 648 | 0.0% | 0.9828 | 98.29% | 1.59% | 0.1097 ms | 2,398.7 KB |
| **SVM (RBF)** | Light | 5 | 20 | 96.91% | 0.9500 | 95.04% | 3.17% | 0.0209 ms | 83.2 KB |

- **Top Light Architecture:** **`gradient_boosting_light`** achieved the best trade-off with **0.9759 Macro F1**, **97.61% Accuracy**, **0.63% FAR**, $1.8\times$ faster inference latency ($0.0043\text{ ms}$), and a $75.7\%$ reduction in model storage size ($389.9\text{ KB}$).
- All configurations, index mappings, and benchmark metrics are exported to [`optimal_features.json`](file:///home/xavier/dev/wifi-csi-presence-detection/optimal_features.json).
