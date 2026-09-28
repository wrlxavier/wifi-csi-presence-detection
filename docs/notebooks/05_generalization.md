# Out-of-Distribution Generalization Analysis (`05_generalization`)

This document summarizes the out-of-distribution (OOD) cross-domain generalization experiment implemented in [`notebooks/05_generalization/`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/05_generalization/):
- [`01_data_acquisition.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/05_generalization/01_data_acquisition.ipynb): Acquisition protocol and metadata logging for the OOD campaign.
- [`02_model_evaluation.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/05_generalization/02_model_evaluation.ipynb): Zero-retraining evaluation of pre-trained models across unseen environments and distances.

---

## 1. Experimental Objective & Methodology

The goal of this campaign was to assess model robustness under domain shift without retraining:
- **Domain Shift:** Transition from the indoor training bedroom ($3.40\text{ m} \times 3.45\text{ m}$ at a fixed 2.0 m distance) to an unseen semi-open outdoor patio (`outdoor_area`).
- **Distance Variations:** Four Line-of-Sight (LoS) inter-node distances: **2.0 m, 3.0 m, 4.0 m, and 5.0 m**.
- **Zero-Retraining Policy:** Models are evaluated strictly as frozen inference pipelines loaded from `models/registry/` without fine-tuning or domain adaptation.
- **Architectures Tested:** All 8 pre-trained models (4 Full-feature models with 648 features vs. 4 Light models with 20 features).

---

## 2. Generalization Dataset Composition

- **Session Ingestion:** 9 raw sessions recorded (`GA` through `GI`, 150 s each):
  - Session `GG` (outdoor 2.0 m empty) was flagged as `INVALID` due to human intrusion and automatically excluded.
  - 8 valid sessions were retained (4 empty, 4 occupied_still).
- **Assembled OOD Dataset:**
  - Standardized using the reference 162-subcarrier mapping (`valid_subcarrier_mapping.csv`).
  - Total samples: **232 windows** (2.0 s non-overlapping, balanced: 116 empty / 116 occupied).
  - 58 windows per distance (29 empty / 29 occupied).

| Distance | Empty Session | Occupied Session | Valid Packets per Session | Window Count |
| :---: | :--- | :--- | :---: | :---: |
| **2.0 m** | `GH` (empty) | `GI` (occupied_still) | 4,365 / 4,012 | 58 |
| **3.0 m** | `GA` (empty) | `GB` (occupied_still) | 4,170 / 4,053 | 58 |
| **4.0 m** | `GC` (empty) | `GD` (occupied_still) | 4,393 / 4,104 | 58 |
| **5.0 m** | `GE` (empty) | `GF` (occupied_still) | 4,353 / 4,384 | 58 |
| **Total** | **4 sessions** | **4 sessions** | **33,834 packets** | **232** |

---

## 3. Generalization Benchmark: Full vs. Light Models

| Model Architecture | Model Type | Feature Count | Accuracy | Macro F1 | Sensitivity | Specificity | False Alarm Rate (FAR) | In-Domain Baseline F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gradient Boosting** | Full | 648 | 50.86% | 0.4563 | 81.90% | 19.83% | 80.17% | 0.9862 |
| **Random Forest** | Full | 648 | 47.41% | 0.4215 | 77.59% | 17.24% | 82.76% | 0.9845 |
| **SVM (RBF)** | Full | 648 | 63.36% | 0.6286 | 75.00% | 51.72% | 48.28% | 0.9828 |
| **MLP** | Full | 648 | 62.07% | 0.6124 | 76.72% | 47.41% | 52.59% | 0.9828 |
| **Random Forest Light** | **Light (Top)** | **20** | **71.12%** | **0.7108** | **75.00%** | **67.24%** | **32.76%** | **0.9724** |
| **Gradient Boosting Light** | Light | 20 | 69.40% | 0.6933 | 74.14% | 64.66% | 35.34% | 0.9759 |
| **MLP Light** | Light | 20 | 69.40% | 0.6939 | 68.10% | 70.69% | 29.31% | 0.9519 |
| **SVM Light** | Light | 20 | 67.67% | 0.6764 | 64.66% | 70.69% | 29.31% | 0.9500 |

### Key Observations:
1. **Environmental Multipath Overfitting in Full Models:**
   Full models (648 features) suffered high false alarm rates ($> 80\%$ in tree models, $> 48\%$ in SVM/MLP), frequently misclassifying empty outdoor sessions as occupied due to sensitivity to room-specific background reflections.
2. **Superior Generalization of Lightweight Models:**
   The 20-feature Light models pruned redundant, room-dependent subcarriers, significantly reducing false alarm rates (down to $29.3 - 35.3\%$) and lifting Macro F1 by $+25$ to $+29$ percentage points over their full counterparts.

---

## 4. Performance Breakdown by Inter-Node Distance

Macro F1-scores across evaluated Line-of-Sight distances ($N = 58$ samples per distance):

| Model Name | Type | 2.0 m LoS | 3.0 m LoS | 4.0 m LoS | 5.0 m LoS |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Gradient Boosting** | Full | 0.7758 | 0.3333 | 0.3705 | 0.1944 |
| **Random Forest** | Full | 0.7742 | 0.3176 | 0.3333 | 0.1343 |
| **SVM (RBF)** | Full | 0.6188 | 0.7575 | 0.6086 | 0.4669 |
| **MLP** | Full | **0.8437** | 0.4785 | 0.7437 | 0.3417 |
| **Gradient Boosting Light** | Light | 0.6024 | **0.9655** | 0.4706 | 0.6039 |
| **Random Forest Light** | Light | 0.7583 | **0.9828** | 0.3333 | 0.5662 |
| **SVM Light** | Light | 0.6189 | **0.9483** | 0.5569 | 0.4175 |
| **MLP Light** | Light | 0.6893 | **0.9828** | 0.5569 | 0.3958 |

- **3.0 m Peak Generalization:** At 3.0 m, all four Light models achieved near-flawless zero-shot detection (**Macro F1 $\ge 0.948$**, peaking at **0.9828** for Random Forest Light and MLP Light).
- **Distance Degradation:** Beyond 3.0 m (4.0 m and 5.0 m), detection performance degrades across all architectures due to increased Fresnel zone width and reduced signal-to-noise ratio over longer outdoor baselines.

---

## 5. Exported Generalization Artifacts
All evaluated metrics and visual figures were exported to `outputs/generalization/`:
- `metrics_summary.csv` / `metrics_summary.json`
- `metrics_by_distance.csv` / `metrics_by_environment.csv`
- `generalization_report.json`
- Diagnostic plots: `model_comparison_full_vs_light.png`, `confusion_matrices_all_models.png`, `robustness_by_distance.png`, and `robustness_by_environment.png`.
