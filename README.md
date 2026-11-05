# Wi-Fi CSI Presence Detection

> Binary classification of human presence (`empty` vs. `occupied`) using Wi-Fi Channel State Information (CSI) collected from low-cost ESP32-S3 hardware, no cameras, no wearables.

*Undergraduate Thesis (PFC), Engenharia de Controle e Automação, UFMG, 2026.*

---

## Overview

This repository contains the modular Python package (`wifi_csi`), reproducible Jupyter Notebooks, trained model bundles, and real-time inference tools for a **device-free human presence detection system** based on IEEE 802.11n HT40 Channel State Information (CSI).

Two ESP32-S3-DevKitC-1U nodes form a dedicated 2.4 GHz HT40 wireless link. When a person occupies the monitored area, their body alters multipath propagation across 162 valid OFDM subcarriers. Statistical dispersion descriptors (`var`, `mad`, `range`, `iqr`) are extracted over 2.0-second windows and classified using supervised machine learning models:
* **Full Modality (162 Subcarriers / 648 Features):** Achieves up to **$F_1 = 0.9948$** (Accuracy = **99.49%**, FAR $\le 0.63\%$) on the held-out test set.
* **Light Modality (5 Subcarriers / 20 Features):** Cuts DSP and feature dimensionality by **96.91%** while maintaining **$F_1 = 0.9759$** (`gradient_boosting_light`, 0.63% FAR), sub-4 µs inference latency (`mlp_light`), an 83 KB flash footprint (`svm_light`), and $+25\text{ to }+29$ pp higher zero-shot generalization in unseen environments.

> For detailed system architecture, hardware specifications, and benchmark tables, see [`docs/ARCHITECTURE_AND_HARDWARE.md`](docs/ARCHITECTURE_AND_HARDWARE.md) and [`docs/FEATURE_MINIMIZATION.md`](docs/FEATURE_MINIMIZATION.md).

---

## Cross-Platform Compatibility (Linux, macOS, Windows)

The project is structured to support **Linux**, **macOS** (Intel & Apple Silicon), and **Windows** (PowerShell, CMD, and WSL2):

> [!NOTE]
> Compatibility has been tested in practice **exclusively on Linux systems**; macOS and Windows environments have not been tested in practice.

| Operating System | Automation Runner | Offline Pipeline & Jupyter Notebooks | Real-Time USB-Serial Monitor (`ESP32-S3`) |
| :--- | :--- | :---: | :---: |
| **Linux** (`x86_64`, `aarch64`) | `Makefile` (`make <target>`) | Supported (Tested) | Supported (`/dev/ttyUSB0`, `/dev/ttyACM0`) |
| **macOS** (`Intel`, `Apple Silicon`) | `Makefile` (`make <target>`) | Supported (Untested) | Supported (`/dev/cu.usbserial-*`, `/dev/cu.usbmodem*`) |
| **Windows 10 / 11** (`x86_64`, `ARM64`) | `make.bat` (`.\make <target>`) & `make.ps1` (`.\make.ps1 <target>`) | Supported (Untested) | Supported (`COM3`, `COM4`, etc.) |

> For OS-specific USB driver notes, Linux `dialout` group permissions, and troubleshooting, see the [Cross-Platform Installation Guide](docs/INSTALLATION.md).

---

## Getting Started (Step-by-Step from Scratch)

Follow the steps below in order to clone the project, configure the Python environment, download the dataset, verify the setup, and execute the Jupyter Notebooks.

### Step 1: Prerequisites & Clone

Ensure **[`uv`](https://docs.astral.sh/uv/)** is installed on your system (`uv` automatically manages Python `>= 3.10` and virtual environments):

```bash
# Linux / macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Clone the repository and enter the project directory:
```bash
git clone https://github.com/xavier/wifi-csi-presence-detection.git
cd wifi-csi-presence-detection
```

---

### Step 2: Configure the Environment & Install Dependencies

Create the local `.venv` virtual environment and install the `wifi_csi` package (in editable mode) along with all scientific, machine learning, testing, and Jupyter Notebook dependencies:

* **Linux / macOS:**
  ```bash
  make install
  ```
* **Windows (PowerShell or CMD):**
  ```powershell
  .\make install
  ```
* **Direct `uv` command (any OS):**
  ```bash
  uv sync --extra dev
  ```

*(Alternative without `uv`: create and activate a virtual environment via `python -m venv .venv`, then run `pip install -e ".[dev]"`. See [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for details).*

---

### Step 3: Obtain the Dataset & Trained Models (Zenodo)

Raw CSI session recordings (`data/01_raw/`), processed canonical feature tables and train/val/test splits (`data/03_processed/`), and trained model bundles (`models/`) are hosted on **Zenodo** ([DOI: 10.5281/zenodo.23960575](https://doi.org/10.5281/zenodo.23960575)).

Download, verify checksums, and restore all dataset and model files into their canonical repository paths in a single step:

* **Linux / macOS:**
  ```bash
  make fetch-zenodo
  ```
* **Windows (PowerShell or CMD):**
  ```powershell
  .\make fetch-zenodo
  ```
* **Direct `uv` command (any OS):**
  ```bash
  uv run python scripts/backup_data.py fetch
  ```

> For manual browser download instructions or custom archive backups (`make compress` / `make restore`), see the [Zenodo Dataset Guide](docs/ZENODO.md).

---

### Step 4: Verify the Installation (Automated Tests)

Run the automated `pytest` suite to confirm that all I/Q parsers, signal filters, feature extractors, model bundles, and Zenodo dataset paths are working properly:

* **Linux / macOS:**
  ```bash
  make test
  ```
* **Windows (PowerShell or CMD):**
  ```powershell
  .\make test
  ```
* **Direct `uv` command (any OS):**
  ```bash
  uv run pytest tests/ -v
  ```

---

### Step 5: Execute the Jupyter Notebooks

Launch JupyterLab directly inside the configured project environment:

* **Linux / macOS:**
  ```bash
  make notebook
  ```
* **Windows (PowerShell or CMD):**
  ```powershell
  .\make notebook
  ```
* **Direct `uv` command (any OS):**
  ```bash
  uv run jupyter lab
  ```
*(Or open the `.ipynb` files in **VS Code / Cursor / Positron** and select the local `.venv` Python interpreter as the notebook kernel).*

#### Recommended Notebook Execution Order

| Stage | Notebook Path | Requires ESP32 Hardware? | Execution Notes & Dependencies |
| :---: | :--- | :---: | :--- |
| **0. Acquisition** | [`notebooks/00_acquisition/csi_collector_v2.ipynb`](notebooks/00_acquisition/csi_collector_v2.ipynb) | **Yes** | Captures live USB-serial CSI sessions. **Skip if using the Zenodo dataset.** |
| **1. EDA** | [`notebooks/01_eda/eda_first_test.ipynb`](notebooks/01_eda/eda_first_test.ipynb)<br>[`notebooks/01_eda/eda_pilot.ipynb`](notebooks/01_eda/eda_pilot.ipynb)<br>[`notebooks/01_eda/eda_main.ipynb`](notebooks/01_eda/eda_main.ipynb) | No | Ready to run immediately after `make fetch-zenodo`. |
| **2. Pipeline** | [`notebooks/02_pipeline/pipeline_v0.ipynb`](notebooks/02_pipeline/pipeline_v0.ipynb)<br>[`notebooks/02_pipeline/pipeline_v1.ipynb`](notebooks/02_pipeline/pipeline_v1.ipynb) | No | `pipeline_v0` builds pilot tables (`outputs/pilot/pipeline_v0/`).<br>`pipeline_v1` builds canonical dataset (`data/03_processed/`). |
| **3. Separability** | [`notebooks/03_analysis/separability_figures.ipynb`](notebooks/03_analysis/separability_figures.ipynb)<br>[`notebooks/03_analysis/separability_lda.ipynb`](notebooks/03_analysis/separability_lda.ipynb) | No | Run `02_pipeline/pipeline_v0.ipynb` before running `separability_lda.ipynb`. |
| **4. Modeling** | [`notebooks/04_modeling/01_split.ipynb`](notebooks/04_modeling/01_split.ipynb)<br>[`notebooks/04_modeling/02_preprocessing.ipynb`](notebooks/04_modeling/02_preprocessing.ipynb)<br>[`notebooks/04_modeling/03_training.ipynb`](notebooks/04_modeling/03_training.ipynb)<br>[`notebooks/04_modeling/04_evaluation.ipynb`](notebooks/04_modeling/04_evaluation.ipynb)<br>[`notebooks/04_modeling/05_robustness.ipynb`](notebooks/04_modeling/05_robustness.ipynb)<br>[`notebooks/04_modeling/06_feature_minimization.ipynb`](notebooks/04_modeling/06_feature_minimization.ipynb) | No | Execute sequentially (`01` $\to$ `06`). Note that `05_robustness.ipynb` requires `reports/logs/metrics_report.json` generated by `04_evaluation.ipynb`. |
| **5. Generalization** | [`notebooks/05_generalization/01_data_acquisition.ipynb`](notebooks/05_generalization/01_data_acquisition.ipynb)<br>[`notebooks/05_generalization/02_model_evaluation.ipynb`](notebooks/05_generalization/02_model_evaluation.ipynb) | `01`: **Yes**<br>`02`: No | `01` is for live hardware capture (skip with Zenodo).<br>`02` evaluates zero-retraining OOD generalization (2–5 m). |

> For the complete workflow diagram, input/output tables, and troubleshooting tips, see the [Jupyter Notebooks Execution Guide](docs/NOTEBOOKS_GUIDE.md).

---

### Step 6: Real-Time Live Presence Detection (Optional Hardware)

If you have the ESP32-S3 RX node connected over USB-serial (`921600` bps), launch the interactive real-time terminal monitor:

* **Linux / macOS:**
  ```bash
  make live          # Interactive model selection menu (Full & Light models)
  make live-reduced  # Directly launch top Light model (5 subcarriers / 20 features)
  ```
* **Windows (PowerShell or CMD):**
  ```powershell
  .\make live
  .\make live-reduced
  ```
* **Direct `uv` command (any OS):**
  ```bash
  uv run python scripts/realtime_presence.py
  ```

---

## Cross-Platform Automation Commands Reference

All project tasks can be executed identically on Linux/macOS (`make <target>`), Windows (`.\make <target>` or `.\make.ps1 <target>`), or directly via `uv`:

| Task Description | Linux / macOS (`Makefile`) | Windows (`make.bat` / `make.ps1`) | Direct `uv` Command |
| :--- | :--- | :--- | :--- |
| **Create `.venv` & install dependencies** | `make install` | `.\make install` | `uv sync --extra dev` |
| **Download & restore Zenodo dataset** | `make fetch-zenodo` | `.\make fetch-zenodo` | `uv run python scripts/backup_data.py fetch` |
| **Download Zenodo archive only** | `make download-zenodo` | `.\make download-zenodo` | `uv run python scripts/backup_data.py download` |
| **Restore local Zenodo archive** | `make restore` | `.\make restore` | `uv run python scripts/backup_data.py restore` |
| **Package data into Zenodo archive** | `make compress` | `.\make compress` | `uv run python scripts/backup_data.py compress` |
| **Run automated test suite** | `make test` | `.\make test` | `uv run pytest tests/ -v` |
| **Launch JupyterLab server** | `make notebook` | `.\make notebook` | `uv run jupyter lab` |
| **Launch real-time monitor (menu)** | `make live` | `.\make live` | `uv run python scripts/realtime_presence.py` |
| **Launch real-time monitor (Light)** | `make live-reduced` | `.\make live-reduced` | `uv run python scripts/realtime_presence.py --reduced` |
| **Clean caches & build artifacts** | `make clean` | `.\make clean` | `uv run python scripts/backup_data.py clean` |

---

## Repository Structure

```text
wifi-csi-presence-detection/
├── Makefile                            # Automation targets for Linux / macOS / WSL
├── make.bat                            # Automation wrapper for Windows (CMD & PowerShell)
├── make.ps1                            # Native PowerShell automation runner for Windows
├── pyproject.toml                      # PEP 621 package specification & dependencies
├── uv.lock                             # Universal cross-platform lockfile (Linux/macOS/Windows)
├── requirements.txt                    # Standard pip compatibility requirements
├── configs/
│   └── pipeline.yaml                   # Centralized windowing, filtering, & feature parameters
├── data/                               # 3-Tier Data Storage (populated via make fetch-zenodo)
│   ├── 01_raw/                         # Raw CSI sessions (.csv + _meta.json: first_test, pilot, main, generalization)
│   ├── 02_interim/                     # Calibrated intermediate amplitude arrays & masks
│   └── 03_processed/                   # Canonical datasets (features_ht40.parquet/.csv) & splits/
├── docs/                               # Project Documentation & Technical Reports
│   ├── INSTALLATION.md                 # Cross-platform setup & OS compatibility guide (Linux/macOS/Windows)
│   ├── NOTEBOOKS_GUIDE.md              # Step-by-step Jupyter Notebooks execution & dependency guide
│   ├── ARCHITECTURE_AND_HARDWARE.md    # Pipeline architecture, hardware setup, & live monitor CLI guide
│   ├── ZENODO.md                       # Zenodo dataset download, backup, & restoration guide
│   ├── FEATURE_MINIMIZATION.md         # Subcarrier ablation & Light model family study (5 SCs / 20 features)
│   ├── MATHEMATICAL_FORMULATIONS.md    # Formal mathematical derivations & evaluation metrics
│   ├── REFERENCES.md                   # Complete academic bibliography & BibTeX source
│   └── notebooks/                      # Stage-by-stage experimental reports (00_acquisition to 05_generalization)
├── models/                             # Trained models & deployable registry bundles (Standard & Light)
│   ├── registry/                       # Atomic bundles (pipeline.joblib + model_card.json)
│   └── *.pkl                           # Standalone scikit-learn checkpoints & fitted StandardScaler
├── notebooks/                          # Interactive Jupyter Notebooks (00_acquisition through 05_generalization)
├── outputs/                            # Generated diagnostic figures, generalization outputs, & backups/
├── reports/                            # Thesis publication assets (figures/, tables/, logs/)
├── scripts/                            # CLI Automation & Live Inference Tools
│   ├── backup_data.py                  # Cross-platform Zenodo dataset downloader, packager, & validator
│   └── realtime_presence.py            # Real-time CSI presence detection terminal dashboard
├── src/                                # Installable Python package (wifi_csi)
│   └── wifi_csi/                       # Modular subpackages: core, parsing, signal, features, models, evaluation, acquisition
└── tests/                              # Automated unit and end-to-end integration test suite (pytest)
```

---

## Documentation Index (`docs/`)

All in-depth documentation, mathematical formulations, and experimental reports are organized in [`docs/`](docs/):

### Setup & Operational Guides
* **[Cross-Platform Installation & OS Compatibility (`docs/INSTALLATION.md`)](docs/INSTALLATION.md):** Detailed setup for Linux, macOS, and Windows, including USB-serial drivers and permissions.
* **[Jupyter Notebooks Execution Guide (`docs/NOTEBOOKS_GUIDE.md`)](docs/NOTEBOOKS_GUIDE.md):** How to launch JupyterLab/VS Code and execute all 13 notebooks in the proper dependency order.
* **[Zenodo Dataset Integration (`docs/ZENODO.md`)](docs/ZENODO.md):** Downloading, verifying, restoring, and packaging the research dataset and models.
* **[Architecture, Hardware & Real-Time Monitor (`docs/ARCHITECTURE_AND_HARDWARE.md`)](docs/ARCHITECTURE_AND_HARDWARE.md):** System architecture, ESP32-S3 hardware setup, benchmark summary, and live CLI options.

### Research & Theoretical Documentation
* **[Mathematical Formulations (`docs/MATHEMATICAL_FORMULATIONS.md`)](docs/MATHEMATICAL_FORMULATIONS.md):** Equations for CFR reconstruction, Butterworth/Wavelet denoising, statistical dispersion metrics, and evaluation scores.
* **[Feature & Subcarrier Minimization (`docs/FEATURE_MINIMIZATION.md`)](docs/FEATURE_MINIMIZATION.md):** Physical subcarrier grouping, 1-SE stopping rule ($N^* = 5$ subcarriers), and Light model benchmarks.
* **[Academic References (`docs/REFERENCES.md`)](docs/REFERENCES.md):** Complete bibliography and BibTeX entries supporting the thesis.

### Stage-by-Stage Notebook Reports (`docs/notebooks/`)
* [`00_acquisition.md`](docs/notebooks/00_acquisition.md) Hardware setup, collection protocol, and Schema v2.0 metadata.
* [`01_eda.md`](docs/notebooks/01_eda.md) Exploratory data analysis across `first_test`, `pilot`, and `main` campaigns.
* [`02_pipeline.md`](docs/notebooks/02_pipeline.md) Shared 162-subcarrier masking and 648-feature extraction (`pipeline_v0` & `pipeline_v1`).
* [`03_analysis.md`](docs/notebooks/03_analysis.md) PCA/LDA separability, hypothesis tests, and physical signal dynamics.
* [`04_modeling.md`](docs/notebooks/04_modeling.md) Stratified splitting, 10-fold CV tuning, hold-out evaluation, robustness, and feature minimization.
* [`05_generalization.md`](docs/notebooks/05_generalization.md) Out-of-distribution generalization across unseen environments and 2.0–5.0 m distances.
