# Change History: `01_eda.md`

- **Date:** 2026-09-26
- **Target Document:** [`docs/content/01_eda.md`](file:///home/xavier/dev/wifi-csi-presence-detection/docs/content/01_eda.md)
- **Author/Verification:** Automated Verification & Review for Final Monograph Drafting

---

## 1. Overview & Motivation

The technical reference [`01_eda.md`](file:///home/xavier/dev/wifi-csi-presence-detection/docs/content/01_eda.md) was reviewed and verified against the exploratory analysis notebooks ([`eda_first_test.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_first_test.ipynb), [`eda_pilot.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_pilot.ipynb), and [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb)), modular source code in [`src/wifi_csi/`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/), raw captures in [`data/01_raw/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/), and the data acquisition reference [`00_acquisition.md`](file:///home/xavier/dev/wifi-csi-presence-detection/docs/content/00_acquisition.md).

The changes eliminate discrepancies regarding physical layer operating modes, correct indexing errors in noise classification, rectify metric bounds in the quality assurance matrix, reconcile timeline timestamps with file naming conventions, and clarify subcarrier masking numbers for downstream pipeline stages.

---

## 2. Detailed Summary of Changes

### 2.1 Physical Layer Operating Mode: First Test HT40 vs. Legacy JSON Template Metadata
- **Sections Affected:** Section 1 (Item 1 & 2), Section 3 (Introduction, Mermaid diagram, Section 3.1, Section 3.2 Item 4), Section 4 (Introduction).
- **Previous Description:** Stated that the First Test campaign (`PLA`, `PLB`) was operated in IEEE 802.11n HT20 mode ($20\text{ MHz}$ bandwidth) on Channel 6, and that the Pilot campaign "scaled the radio link to 802.11n HT40 mode ($40\text{ MHz}$ bandwidth, 192 reported subcarriers)".
- **Updated Description:** Clarified that the First Test link was physically operating in 802.11n HT40 on Channel 11 ($40\text{ MHz}$ bandwidth, yielding 192 complex subcarrier bins with 161–166 valid subcarriers and the characteristic 26 null subcarriers). Documented that mentions of Channel 6 and HT20 in raw sidecars (`session_PLA_empty_20260405_1847_meta.json`) represent legacy template defaults from initial collector prototyping scripts (consistent with [`00_acquisition.md`](file:///home/xavier/dev/wifi-csi-presence-detection/docs/content/00_acquisition.md#L499)). Updated the Section 3 Mermaid diagram and Section 4 introductory text accordingly.

### 2.2 Plot 7: Flagged Noisy Subcarrier Index Enumeration
- **Sections Affected:** Section 6.7 (Line 224).
- **Previous Description:** Stated: *"The 90th percentile threshold was calculated at $\text{CV}_{\text{thresh}} = 0.091$ ($\approx 0.0908$). Exactly $17\text{ subcarriers}$ (index 15, and indices 134–142, 144, 146–147, 149–150) were flagged as noisy ($CV > p_{90}$)."* This contained only 15 subcarriers, erroneously included index 144 ($\text{CV} = 0.0898 < p_{90}$), and omitted indices 143, 145, and 148.
- **Updated Description:** Corrected the enumeration to: *"Exactly $17\text{ subcarriers}$ (index 15, and indices 134–143 and 145–150, i.e., all indices from 134 to 150 except 144) were flagged as noisy ($CV > p_{90}$)."*

### 2.3 Table 8.1: Quality Assurance Checklist Metric Status Corrections
- **Sections Affected:** Section 8 (Table 8.1).
- **Previous Description:**
  - First Test RSSI Stability: Reported as `PASSED ($\sigma < 0.5\text{ dB}$)`.
  - First Test Subcarrier Count: Reported as `PASSED ($192\text{ raw}$)`.
  - Pilot Subcarrier Count: Reported as `PASSED ($166\text{ valid}$)`.
  - Main Packet Loss: Reported as `**PASSED** ($< 0.18\%$)`.
- **Updated Description:**
  - **First Test RSSI:** Updated to `PASSED ($\sigma \le 1.28\text{ dB}$)` against the formal $\sigma_{\text{RSSI}} < 5.0\text{ dBm}$ criterion (since Session `PLB` exhibited $\sigma = 1.28\text{ dBm}$, which violated the erroneous $\sigma < 0.5\text{ dB}$ label).
  - **First Test Subcarrier Count:** Updated to `PASSED ($161 - 166\text{ valid}$)` to reflect true valid subcarrier counts ($N_{\text{valid}} \ge 40$) rather than raw bin length.
  - **Pilot Subcarrier Count:** Updated to `PASSED ($162 - 166\text{ valid}$)` to accurately account for Session `D` (where torso blockage dropped four edge subcarriers below threshold, yielding 162 valid carriers).
  - **Main Packet Loss:** Updated to `**PASSED** ($0.01 - 0.18\%$)` to document the full observed loss range across sessions (Sessions L and M had $0.01\%$, Session G had $0.03\%$, Sessions H and I had $0.18\%$).

### 2.4 Plot 3: Recording Duration Annotation
- **Sections Affected:** Section 6.3 (Line 197).
- **Previous Description:** Stated that Plot 3 visualizes representative subcarriers *"across the full $690\text{ s}$ duration of each session"*.
- **Updated Description:** Corrected to clarify that Plot 3 renders each session across its individual recording duration ($690.0\text{ s}$ for standard sessions, and $1,889.9\text{ s} \approx 31.5\text{ min}$ for extended baseline Session J), as plotted with unshared x-axes in [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb).

### 2.5 Plot 5: Cross-Session Consistency Delta Metric
- **Sections Affected:** Section 6.5 (Line 213).
- **Previous Description:** Stated: *"with an overall mean amplitude difference of only $\sim 1.1\%$ ($24.91$ vs. $25.19$, per-subcarrier delta $< 2.9\%$)"*.
- **Updated Description:** Clarified that $2.85\%$ is the **mean** relative per-subcarrier delta across all valid carriers, with the maximum delta reaching $8.93\%$: *"with an overall mean amplitude difference of only $\sim 1.1\%$ ($24.91$ vs. $25.19$, mean per-subcarrier delta of $2.85\%$, maximum delta $< 9.0\%$)"*.

### 2.6 Plot 6: Packet Gap Loss Range Lower Bound
- **Sections Affected:** Section 6.6 (Line 219).
- **Previous Description:** Stated that packet gap events occurred at most 20 times per session *"(0.03% - 0.18% of total frames)"*.
- **Updated Description:** Corrected the lower bound to $0.01\%$, reflecting Sessions L and M (3 lost packets out of 20,699 expected): *"($0.01\% - 0.18\%$ of total frames across all sessions, with Sessions L and M exhibiting only $0.01\%$)"*.

### 2.7 Plot 10: Session H Variance Ratio Metric
- **Sections Affected:** Section 6.10 (Line 245).
- **Previous Description:** Stated that the variance ratio in Session H was *"averaging 1.97 and peaking at 2.57x"*.
- **Updated Description:** Clarified that $1.97$ is the **median** variance ratio across the 165 shared valid subcarriers (mean ratio is $1.85$): *"exhibiting a median ratio of $1.97$ (mean $1.85$) and peaking at $2.57\times$ the empty baseline"*.

### 2.8 Section 9: Downstream Subcarrier Masking Specification
- **Sections Affected:** Section 9 (Item 1, Lines 313–317).
- **Previous Description:** Stated: *"26 subcarriers must be discarded permanently as dead carriers (guard bands and DC subcarrier). A shared valid subcarrier mask of 162 subcarriers (across Pilot C-F and Main G-M) or 165 subcarriers (Main G-M) must be used."*
- **Updated Description:** Clarified the exact accounting across stages:
  - 26 dead subcarriers in standard clean sessions ($192 - 26 = 166$).
  - 27 discarded subcarriers for the Main campaign (Session K drops subcarrier 58, leaving 165 valid subcarriers).
  - 30 permanently discarded subcarriers for the combined Pilot + Main pipeline ($192 - 30 = 162$), yielding the 162 valid active subcarriers serialized in downstream processing.
  - Noted noisy carrier clustering across indices 134–150.

### 2.9 Session Timeline Overview: Timestamps and Naming Alignment
- **Sections Affected:** Section 5 (Lines 144–153).
- **Previous Description:** The ASCII timeline mixed filename timestamps for Sessions G, H, I (`17:01`, `19:08`, `19:32`) with recording start $t_0$ timestamps for Sessions J, K, L, M (`20:01`, `23:53`, `00:11`, `00:31`), creating an internal mismatch with Section 6.5 (`Session J (20:00), and Session L (00:09)`).
- **Updated Description:** Standardized the timeline to report both the filename stem timestamp (matching filesystem naming and Section 6.5 text) and the exact host recording start time $t_0$:
  - `17:01 [Session G: Empty Baseline 1] (t0 = 17:03, ~11.5 min, 20,151 samples)`
  - `19:08 [Session H: Occupied P1 (Off-LoS West)] (t0 = 19:11, ~11.5 min, 19,984 samples)`
  - `19:32 [Session I: Occupied P2 (On-LoS Near TX)] (t0 = 19:33, ~11.5 min, 19,911 samples)`
  - `20:00 [Session J: Extended Empty Baseline] (t0 = 20:01, ~31.5 min, 55,075 samples)`
  - `23:51 [Session K: Occupied P3 (On-LoS Near RX)] (t0 = 23:53, ~11.5 min, 20,050 samples)`
  - `00:09 [Session L: Repeat Empty Baseline 2] (t0 = 00:11, ~11.5 min, 20,236 samples)`
  - `00:26 [Session M: Occupied P4 (Off-LoS East)] (t0 = 00:31, ~11.5 min, 20,171 samples)`
