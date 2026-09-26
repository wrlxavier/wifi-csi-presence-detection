# Change History: `00_acquisition.md`

- **Date:** 2026-09-26
- **Target Document:** [`docs/content/00_acquisition.md`](file:///home/xavier/dev/wifi-csi-presence-detection/docs/content/00_acquisition.md)
- **Author/Verification:** Automated Verification & Review for Final Monograph Drafting

---

## 1. Overview & Motivation

The technical reference [`00_acquisition.md`](file:///home/xavier/dev/wifi-csi-presence-detection/docs/content/00_acquisition.md) was reviewed and validated against experimental notebooks ([`csi_collector_v2.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb), [`eda_main.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/01_eda/eda_main.ipynb)), modular source code in [`src/wifi_csi/`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/), and all 24 raw dataset captures in [`data/01_raw/`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/). The modifications resolve internal layout contradictions, reconcile legacy prototyping labels with final compiled firmware behavior, correct hardware power supply specifications, and document campaign duration variations.

---

## 2. Detailed Summary of Changes

### 2.1 Hardware Power Delivery (TX Node)
- **Sections Affected:** Section 2.1 (Table 2.1), Section 2.2 (Mermaid diagram), Section 9.4 (Item 3).
- **Previous Description:** Stated that the transmitter node was powered by a *"10,000 mAh portable DC power bank (5 V / 2.4 A)"* to eliminate mains noise and ground loops.
- **Updated Description:** Clarified that the transmitter node was powered by a **Samsung 5V/2A wall charger (mains DC adapter)** providing continuous regulated DC power. Updated Section 9.4 to state that high link stability in static empty conditions is maintained by the regulated DC wall supply and rigid tripod mountings.

### 2.2 Physical Communication Protocol: ESP-NOW vs. Legacy STA/AP ICMP Ping
- **Sections Affected:** Section 2.1, Section 2.2 (Text & Mermaid Diagram), Section 4.3 (Table 4.3, Field 16), Section 7.2 (Sample JSON Note).
- **Previous Description:** Described the link as an Access Point (AP) and Station (STA) pair exchanging ICMP echo request ping packets at 30 Hz.
- **Updated Description:** Clarified that physical layer transmission between `csi_send` and `csi_recv` firmware operates via Espressif's connectionless **ESP-NOW** protocol at the MAC layer. Documented that mentions of `ssid: "CSI_AP"` and `role: "STA (ICMP transmitter)"` in raw metadata sidecars represent historical prototyping remnants from early collector script templates, whereas actual packet delivery requires no 802.11 association handshakes or IP layer overhead.
- **Payload Field 16:** Updated description of `ampdu_cnt` to denote standalone ESP-NOW frames rather than ping packets.

### 2.3 Physical Bedroom Layout: Door Location Correction
- **Sections Affected:** Section 2.3 (Line 72).
- **Previous Description:** Stated that the single plywood interior door was *"situated on the east wall"*.
- **Updated Description:** Corrected the door location to the **west wall** ($x = 0.0\text{ m}$). This eliminates the direct contradiction with the Section 2.3 ASCII floorplan diagram (which correctly displays `Plywood Door` on the west boundary) and aligns with Section 6.1 (which describes the mirrored wardrobe on the east wall).

### 2.4 Campaign Protocol Durations & Scope
- **Sections Affected:** Section 5.1.
- **Previous Description:** Framed the 4-phase $T_{\text{total}} = 690\text{ s}$ duration ($60\text{ s}$ stabilization, $600\text{ s}$ active, $30\text{ s}$ buffer) as universal, noting only Session J ($1890\text{ s}$) as an exception.
- **Updated Description:** Clarified that the 690 s duration is the standard protocol for the Pilot and Main campaigns, and explicitly cataloged variations across all campaigns:
  - **First Test Campaign (`PLA`, `PLB`):** Single $60\text{ s}$ exploratory continuous runs.
  - **Generalization Campaign (`GA`–`GI`):** Compact $150\text{ s}$ protocol ($60\text{ s}$ stabilization, $60\text{ s}$ active, $30\text{ s}$ buffer) for rapid multi-distance sweeps in the outdoor patio.
  - **Session J:** Extended $1890\text{ s}$ baseline ($1800\text{ s}$ active).

### 2.5 Midnight Rollover Root Cause
- **Sections Affected:** Section 5.2.
- **Previous Description:** Stated that Session K traversed midnight without explaining why $t_2 < t_1$ in the raw metadata.
- **Updated Description:** Explained that [`csi_collector_v2.ipynb`](file:///home/xavier/dev/wifi-csi-presence-detection/notebooks/00_acquisition/csi_collector_v2.ipynb) fixed the session date reference from the recording start time $t_0$, causing timestamps past midnight (`00:04:51`) to be combined with the start date (`2026-09-22`), resulting in $t_2 < t_1$. Confirmed that [`get_active_interval_from_metadata`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/parsing/metadata_parser.py#L61-L72) resolves this by adding a one-day offset.

### 2.6 Spatial Positions, Occupied Conditions, and Campaign Counts
- **Sections Affected:** Section 6 (Introduction), Section 6.1.
- **Previous Description:** Stated that *"five distinct occupied scenarios were collected across three experimental campaigns"*.
- **Updated Description:** Clarified that data collection spanned **5 distinct spatial positions** (Center, P1, P2, P3, and P4) covering **6 distinct occupied conditions** (`occupied_still`, `occupied_moving`, `occupied_p1_still` through `occupied_p4_still`) across **4 experimental campaigns** (`first_test`, `pilot`, `main`, and `generalization`).
- **Metadata Note Added:** Added a callout note explaining that raw JSON sidecar files for multi-position sessions retained the template default coordinates $(1.45, 2.11)\text{ m}$ in `setup.protocol.subject_position`, while true ground truth is tracked by `session.label` and `setup.labels_description`.

### 2.7 Metadata Schema & Sample JSON Restoration
- **Sections Affected:** Section 7.2.
- **Previous Description:** The sample JSON metadata block omitted the `"labels_description"` dictionary from the `setup` block, and did not explain legacy absolute file paths.
- **Updated Description:** 
  - Restored the complete `"labels_description"` dictionary inside `setup` matching the raw file on disk ([`session_G_empty_20260922_1701_meta.json`](file:///home/xavier/dev/wifi-csi-presence-detection/data/01_raw/main/session_G_empty_20260922_1701_meta.json)).
  - Added an explanatory callout note documenting the schema evolution from Schema v2.0 (host-absolute paths recorded before repository restructuring) to Schema v2.1 (portable relative paths generated via [`generate_session_metadata`](file:///home/xavier/dev/wifi-csi-presence-detection/src/wifi_csi/acquisition/metadata_logger.py#L8-L65) for the generalization campaign).
