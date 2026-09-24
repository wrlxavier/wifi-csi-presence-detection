# Signal Processing and Feature Engineering

This document details the signal processing pipeline, OFDM subcarrier masking, temporal windowing, and statistical feature engineering methods implemented in [pipeline_v0.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v0.ipynb), [pipeline_v1.ipynb](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/02_pipeline/pipeline_v1.ipynb), and [`wifi_csi.features`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/features/).

---

## 1. Physical Layer I/Q Decomposition

Each ESP32-S3 packet contains raw channel measurements formatted as interleaved In-phase ($I$) and Quadrature ($Q$) signed 8-bit integers:

$$\text{CSI\_RAW} = [I_0, Q_0, I_1, Q_1, \dots, I_{N-1}, Q_{N-1}]$$

For 802.11n HT40 (40 MHz channel bandwidth), the total payload length is 384 bytes, representing $N = 192$ complex subcarrier values:

$$H_k = I_k + j \cdot Q_k, \quad k \in \{0, 1, \dots, 191\}$$

From the complex channel frequency response $H_k$, the instantaneous subcarrier amplitude $A_k$ is computed as the Euclidean norm:

$$A_k = |H_k| = \sqrt{I_k^2 + Q_k^2}$$

The unwrapped phase $\phi_k$ can also be computed when phase sanitization is performed:

$$\phi_k = \text{atan2}(Q_k, I_k)$$

---

## 2. Dynamic Subcarrier Masking

In 802.11n HT40, several subcarriers are non-informative or reserved:
- Direct Current (DC) carrier at the channel center.
- Guard band subcarriers at band edges to prevent adjacent-channel interference.
- High-attenuation carrier nulls.

### Validation Criterion

A subcarrier $k$ is considered active and valid within a session if its mean amplitude across the session exceeds an empirical noise floor threshold:

$$\overline{A}_k = \frac{1}{T} \sum_{t=1}^T A_k(t) \ge \theta_{\text{valid}} \quad (\theta_{\text{valid}} = 0.5)$$

Across all recordings, 26 subcarriers consistently remain zero or below the noise floor, leaving 166 or 165 valid subcarriers per session.

### Shared HT40 Subcarrier Mask

To enable cross-session generalization and train unified machine learning models, a shared mask is formed by taking the set intersection of valid subcarriers across all 11 valid sessions ($C$ through $M$):

$$\mathcal{K}_{\text{shared}} = \bigcap_{s \in \mathcal{S}_{\text{valid}}} \mathcal{K}_s$$

Across the entire dataset, $|\mathcal{K}_{\text{shared}}| = 162$ shared valid subcarriers. This mapping is dynamically saved to [`data/03_processed/valid_subcarrier_mapping.csv`](file:///home/xavier/dev/wifi-csi-presence-detection/data/03_processed/valid_subcarrier_mapping.csv).

---

## 3. Active Window Selection

Raw recordings include human transit periods while entering or leaving the room. The feature pipeline filters the time series to strictly retain the active condition interval $[t_1, t_2]$ specified in the session metadata:

$$t_1 \le t_{\text{packet}} \le t_2$$

This isolates pure physical states:
- Zero operator movement during empty sessions.
- Stable, continuous human posture during occupied sessions.

The loader incorporates automated date-rollover logic to correctly handle sessions where $t_2$ extends past 00:00:00 UTC.

---

## 4. Time-Based Window Segmentation

Packet transmission over wireless channels experiences minor network latency and packet arrival jitter ($4\text{ ms} \text{ to } 7\text{ ms}$). Segmenting by fixed packet counts (e.g. 60 packets) introduces variable physical time lengths.

Therefore, the pipeline enforces strict time-based windowing:
- **Window Length**: $T_w = 2.0\text{ seconds}$.
- **Window Stride**: $S_w = 2.0\text{ seconds}$ (0% overlap, non-overlapping windows).

Each window $W_m$ aggregates all packets falling within the time interval:

$$W_m = \{ A_k(t) \mid m \cdot T_w \le t < (m+1) \cdot T_w \}$$

Each 2.0-second window typically contains between 56 and 60 CSI packets, providing high temporal resolution without window-to-window autocorrelation.

---

## 5. Statistical Feature Extraction

For each shared valid subcarrier $k \in \mathcal{K}_{\text{shared}}$ within window $W_m$, four complementary statistical descriptors are computed:

### 1. Variance (Signal Energy Dispersion)
Captures amplitude variability driven by body motions and chest displacements:

$$\text{Var}(A_k) = \frac{1}{|W_m|} \sum_{t \in W_m} (A_k(t) - \overline{A}_k)^2$$

### 2. Mean Absolute Deviation (MAD - Robust Dispersion)
Robust estimator of dispersion that is resilient against sporadic packet noise:

$$\text{MAD}(A_k) = \text{median}\left( \left| A_k(t) - \text{median}(A_k) \right| \right)$$

### 3. Dynamic Range (Extremal Spread)
Measures the maximum peak-to-peak amplitude excursion:

$$\text{Range}(A_k) = \max_{t \in W_m} A_k(t) - \min_{t \in W_m} A_k(t)$$

### 4. Interquartile Range (IQR - Core Distribution Spread)
Captures the central 50% spread of amplitudes, filtering out impulse spikes:

$$\text{IQR}(A_k) = Q_{75}(A_k) - Q_{25}(A_k)$$

### Dimension of the Feature Vector

The final tabular feature vector $\mathbf{x}_m$ concatenates all 4 statistics across all 162 shared subcarriers:

$$\dim(\mathbf{x}_m) = 162 \times 4 = 648 \text{ features}$$

Feature names adhere to the canonical pattern:
- `sc000_var`, `sc000_mad`, `sc000_range`, `sc000_iqr`
- `sc001_var`, `sc001_mad`, `sc001_range`, `sc001_iqr`
- ... up to `sc161_*`

---

## 6. Dataset Assembly and Integrity Policies

1. **Natural Scale Preservation**: Feature values are saved in their natural, unstandardized scale in both [`data/03_processed/features_ht40.csv`](file:///home/xavier/dev/wifi-csi-presence-detection/data/03_processed/features_ht40.csv) and [`data/03_processed/features_ht40.parquet`](file:///home/xavier/dev/wifi-csi-presence-detection/data/03_processed/features_ht40.parquet). This preserves raw physical units for exploratory data analysis.
2. **Exclusion of RSSI**: While RSSI is tracked for diagnostic validation, it is intentionally excluded from the tabular training set. RSSI is prone to macroscopic power variations and temperature drift, whereas CSI subcarrier dynamics capture fine-grained multipath phase and amplitude interference.
3. **Partition Preprocessing**: Feature standardization (`StandardScaler`) is applied exclusively inside the model training pipeline, fitted strictly on the training partition to prevent test set data leakage.
