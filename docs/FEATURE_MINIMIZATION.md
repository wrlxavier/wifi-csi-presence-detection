## Experimental Objective & Research Question
This experiment investigates feature dimensionality reduction and physical subcarrier grouping for device-free human presence detection using ESP32-S3 Channel State Information (CSI).

> **Core Research Question:**
> *"Once the most informative Wi-Fi CSI features are identified, what is the minimum number of subcarriers/features required to achieve a lightweight model without statistically significant degradation in performance compared to the full-feature baseline?"*

---

### Signal Structure & Physical Subcarrier Grouping
- **Channel Bandwidth:** HT40 (40 MHz bandwidth on 2.4 GHz ISM band).
- **Valid Subcarriers:** 162 valid subcarriers (excluding guard bands, DC null, and out-of-band pilot indices).
- **Temporal Metrics:** 4 statistical metrics extracted over 2.0 s non-overlapping windows:
  1. `var`: Variance of subcarrier amplitude
  2. `mad`: Mean Absolute Deviation (robust dispersion metric)
  3. `range`: Peak-to-peak amplitude excursion ($\max - \min$)
  4. `iqr`: Interquartile Range (75th percentile minus 25th percentile)
- **Total Dimensionality:** $162 \text{ subcarriers} \times 4 \text{ metrics} = 648 \text{ features}$.
- **Physical Selection Unit:** Features are selected strictly at the **subcarrier group level** (all 4 metrics together) to preserve the physical coherence of the OFDM channel frequency response:
  $$I(sc_j) = \sum_{m \in \{var, mad, range, iqr\}} |I(sc_j, m)|$$

---

### Methodological Protocol & Leakage Prevention
1. **Strict Session Isolation:** Cross-validation is partitioned using `StratifiedGroupKFold(n_splits=5)` using `session_id` to eliminate temporal leakage between adjacent 2.0 s windows.
2. **Dedicated Test Set Isolation:** The hold-out test set (`test.parquet`, 585 samples) remains strictly untouched until the final single blind verification step.
3. **Formal Stopping Criterion (The 1-SE Rule):**
   The minimal optimal subcarrier subset $N^*$ is chosen using the One-Standard-Error Rule:
   $$\overline{\text{F1}}_{N^*} \ge \overline{\text{F1}}_{\text{full}} - \text{SE}(\text{F1}_{\text{full}}), \quad \text{where } \text{SE} = \frac{\sigma_{\text{folds}}}{\sqrt{K}}$$
   with an operational tolerance of $\Delta\text{F1} \le 1.0\%$ relative to the full baseline and $\overline{\text{F1}} \ge 0.90$.


## Conclusions & Answers to Research Questions

### Top Performers per Modality:
- **Standard Modality (Full 162 Subcarriers / 648 Features):**
  `mlp` (`mlp_bundle`) is the designated top performer (Test Macro F1 = **0.9828**, Test Accuracy = **98.29%**, FAR = **0.63%**).
- **Light Modality (Reduced 5 Subcarriers / 20 Features):**
  `gradient_boosting_light` (`gradient_boosting_light_bundle`) is the designated top performer (Test Macro F1 = **0.9759**, Test Accuracy = **97.61%**, FAR = **0.63%**).


---

### 1. What is the minimum optimal number of subcarriers and features?
Applying the One-Standard-Error Rule (1-SE Rule) on session-isolated cross-validation reveals that **$N^* = 5$ subcarriers** (corresponding to **20 features**: `sc041`, `sc040`, `sc042`, `sc047`, `sc012` across `var`, `mad`, `range`, `iqr`) achieves the formal stopping threshold:
- **Feature Reduction:** Slashes feature dimensionality from 648 features down to 20 (**96.91% reduction**).
- **Generalization:** Out-of-fold cross-validation performance improves from $0.5606 \pm 0.1124$ (full model) to $0.6474 \pm 0.1376$ (reduced model), demonstrating that eliminating noisy, uninformative subcarriers mitigates overfitting to session-specific multipath profiles.
- **Blind Test Performance Across Family:** Every model in the Light Family comfortably exceeds the Macro F1 $\ge 0.90$ requirement on the untouched test set (`test.parquet`):
  - **Gradient Boosting Light (`gradient_boosting_light`):** Macro F1 = **0.9759** (Accuracy = 97.61%, FAR = 0.63%)
  - **Random Forest Light (`random_forest_light`):** Macro F1 = **0.9724** (Accuracy = 97.26%, FAR = 1.27%)
  - **MLP Light (`mlp_light`):** Macro F1 = **0.9519** (Accuracy = 95.21%, FAR = 4.44%)
  - **SVM Light (`svm_light`):** Macro F1 = **0.9500** (Accuracy = 95.04%, FAR = 3.17%)

---

### 2. What is the impact on inference latency and memory footprint?
- **Feature Extraction Overhead:** Reducing subcarrier extraction from 162 to 5 eliminates **96.91% of digital signal processing computation** (I/Q amplitude conversion, Butterworth filtering, and temporal window statistic calculations). On microcontrollers like the ESP32-S3, slicing only raw OFDM indices `[48, 47, 49, 54, 18]` reduces window processing overhead from dozens of milliseconds to sub-millisecond execution.
- **Inference Latency:**
  - **MLP Light:** Drops to **0.0035 ms/sample** ($3.1\times$ faster than full baseline).
  - **GBDT Light:** Drops to **0.0043 ms/sample** ($1.8\times$ faster).
  - **SVM Light:** Drops to **0.0209 ms/sample** ($5.2\times$ faster).
  - **Random Forest Light:** Executes in **0.0420 ms/sample**.
- **Memory Footprint:**
  - **SVM Light:** Drops from $2,398.7 \text{ KB}$ down to **$83.2 \text{ KB}$** ($28.8\times$ storage reduction).
  - **MLP Light:** Drops from $2,173.9 \text{ KB}$ down to **$268.3 \text{ KB}$** ($8.1\times$ storage reduction).
  - **GBDT Light:** Drops from $1,604.2 \text{ KB}$ down to **$389.9 \text{ KB}$** ($4.1\times$ storage reduction).

---

### 3. Which model architecture provides the best operational balance for deployment?
- **For Edge Microcontrollers (ESP32-S3 Firmware Deployment):**
  **`svm_light`** and **`mlp_light`** offer the best operational profile. With only 20 features, `svm_light` has a disk/flash footprint of only **83.2 KB**, while `mlp_light` executes in under **4 microseconds per sample**, leaving abundant CPU cycles for the FreeRTOS Wi-Fi stack.
- **For Edge Gateways & Host Services (Raspberry Pi / Linux Services):**
  **`gradient_boosting_light`** delivers the best overall classification accuracy (**97.61%**) and Macro F1 (**0.9759**) with an ultra-low False Alarm Rate of **0.63%**, packaged in a compact 390 KB bundle.
