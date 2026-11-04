# Zenodo Dataset Integration Guide

This guide explains how to automatically download and restore the official research dataset published on **Zenodo** into your local clone of this repository.

---

## 1. Dataset Metadata

* **Zenodo Record:** [https://zenodo.org/records/23960575](https://zenodo.org/records/23960575)
* **Digital Object Identifier (DOI):** [10.5281/zenodo.23960575](https://doi.org/10.5281/zenodo.23960575)
* **Archive File:** `wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip` (~163 MB)
* **MD5 Checksum:** `e4ccadccdcf58f8b6401cc10c2a3e48e`
* **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0)

---

## 2. Automatic Setup (Recommended)

You can download and restore the complete dataset into the repository in a single automated step:

```bash
make fetch-zenodo
```

This command will:
1. Download `wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip` directly from Zenodo into `outputs/backups/`.
2. Extract all raw recordings, processed splits, model checkpoints, and feature selection metadata to their canonical paths.
3. Validate repository integrity and component structure automatically.

---

## 3. Step-by-Step Command Line Setup

If you prefer to run each step individually:

### Step 1: Download Archive

Using `make`:
```bash
make download-zenodo
```

Or using `curl` / `wget`:
```bash
mkdir -p outputs/backups

# Using curl:
curl -L -o outputs/backups/wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip \
  "https://zenodo.org/records/23960575/files/wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip?download=1"

# Or using wget:
wget -O outputs/backups/wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip \
  "https://zenodo.org/records/23960575/files/wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip?download=1"
```

### Step 2: Restore and Validate Structure

Extract files into their project paths and verify integrity:

```bash
make restore-zenodo
# or directly: uv run python scripts/backup_data.py restore --zenodo
```

---

## 4. Manual Browser Download (Alternative)

1. Open the Zenodo record in your browser: [https://zenodo.org/records/23960575](https://zenodo.org/records/23960575).
2. In the **Files** section, click **Download** on `wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip`.
3. Move the downloaded `.zip` file into the `outputs/backups/` folder of this repository:
   ```bash
   mkdir -p outputs/backups
   mv ~/Downloads/wifi-csi-presence-detection-zenodo-2026-v2.0.0.zip outputs/backups/
   ```
4. Restore and validate the archive:
   ```bash
   make restore-zenodo
   ```

---

## 5. Restored Project Components

Once restored, the following assets are immediately available:

| Directory / File | Description |
|---|---|
| `data/01_raw/` | Raw CSI session CSV recordings and JSON metadata sidecars across campaigns (`first_test`, `pilot`, `main`, `generalization`). |
| `data/03_processed/` | Canonical feature tables (`features_ht40.parquet`, `features_ht40.csv`), subcarrier mapping (`valid_subcarrier_mapping.csv`), and train/val/test splits (`splits/*.parquet`). |
| `models/` | Trained scikit-learn model checkpoints (`.pkl`), fitted `StandardScaler`, and deployable pipeline bundles (`models/registry/*_bundle`). |
| `reports/logs/optimal_features.json` | Subcarrier index mappings and benchmark metadata for lightweight model deployment. |

---

## 6. Verification

To verify that the dataset and models are fully functional, run the automated test suite:

```bash
make test
# or directly: uv run pytest
```

All unit and integration tests should pass without errors.
