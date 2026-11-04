# Cross-Platform Installation & OS Compatibility Guide

This guide provides detailed instructions for setting up and running the **Wi-Fi CSI Presence Detection** project from scratch on **Linux**, **macOS**, and **Windows**.

---

## 1. Operating System Compatibility Matrix

The codebase, dependencies (`uv.lock` / `pyproject.toml`), data management scripts, and Jupyter Notebooks are designed to run natively across all three major operating systems:

> [!NOTE]
> Compatibility has been tested in practice **exclusively on Linux systems**; macOS and Windows environments have not been tested in practice.

| Component / Workflow | Linux (`x86_64`, `aarch64`) | macOS (`Intel`, `Apple Silicon M1–M4`) | Windows 10 / 11 (`x86_64`, `ARM64`, `WSL2`) |
| :--- | :---: | :---: | :---: |
| **Environment & Package Management (`uv`)** | Supported | Supported | Supported |
| **Zenodo Dataset Download & Restore** | Supported | Supported | Supported |
| **Offline Signal Processing & ML Pipeline** | Supported | Supported | Supported |
| **Interactive Jupyter Notebooks (`notebooks/`)** | Supported | Supported | Supported |
| **Automated Test Suite (`pytest`)** | Supported | Supported | Supported |
| **Real-Time USB-Serial Monitor (`make live`)** | Supported (`/dev/ttyUSB*`, `/dev/ttyACM*`) | Supported (`/dev/cu.usbserial*`, `/dev/cu.usbmodem*`) | Supported (`COM3`, `COM4`, etc.) |
| **Automation Runner** | `Makefile` (`make <target>`) | `Makefile` (`make <target>`) | `make.bat` (`.\make <target>`) & `make.ps1` (`.\make.ps1 <target>`) |

---

## 2. Prerequisites

### 2.1 Install `uv` (Recommended Package & Environment Manager)

This project uses **[`uv`](https://docs.astral.sh/uv/)** to manage Python versions, virtual environments (`.venv`), and cross-platform dependency locking (`uv.lock`). If Python `>= 3.10` is not present on your machine, `uv` will automatically download and configure a compatible Python interpreter.

* **Linux & macOS:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  *(On macOS, you can also run `brew install uv`).*

* **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  *(Or via Winget: `winget install --id=Astral-sh.uv -e`).*

After installation, restart your terminal and verify that `uv` is available:
```bash
uv --version
```

### 2.2 Automation Tooling (`make` vs. Windows Wrappers)

* **Linux:** GNU `make` is typically pre-installed (or available via `sudo apt install make` / `sudo dnf install make`).
* **macOS:** Available via Xcode Command Line Tools (`xcode-select --install`).
* **Windows:** Windows does **not** include GNU `make` by default. To provide the exact same workflow without additional installations, this repository includes native Windows automation scripts in the project root:
  * **`make.bat`** — Works in both **Command Prompt (`cmd.exe`)** (`make <target>`) and **PowerShell** (`.\make <target>`).
  * **`make.ps1`** — Native **PowerShell** script (`.\make.ps1 <target>`).

---

## 3. Environment Setup

Clone the repository and navigate to the project root:

```bash
git clone https://github.com/xavier/wifi-csi-presence-detection.git
cd wifi-csi-presence-detection
```

### Option A: Automated Setup via `uv` (Recommended)

Run the `install` command for your operating system. This automatically creates the `.venv/` virtual environment, installs all core scientific/ML libraries, installs JupyterLab/Notebook and `pytest`, and registers the local `wifi_csi` package in editable mode:

* **Linux / macOS:**
  ```bash
  make install
  ```
* **Windows (PowerShell):**
  ```powershell
  .\make install
  # or: .\make.ps1 install
  ```
* **Windows (Command Prompt `cmd.exe`):**
  ```cmd
  make install
  ```
* **Any OS (Direct `uv` command):**
  ```bash
  uv sync --extra dev
  ```

> [!NOTE]
> **Why `uv sync --extra dev` instead of `uv pip install -e ".[dev]"`?**
> On a freshly cloned repository, the `.venv/` directory does not exist yet. Running `uv pip install` directly without first running `uv venv` fails with `error: No virtual environment found`. In contrast, `make install` (which runs `uv sync --extra dev`) automatically creates `.venv/` if missing, resolves platform-specific wheels from `uv.lock`, and installs the project in editable mode in a single step.

### Option B: Standard `python -m venv` + `pip` (Alternative)

If you prefer not to use `uv`, you can use Python's built-in `venv` module (`Python >= 3.10` required):

* **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -e ".[dev]"
  # or: pip install -r requirements.txt
  ```

* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -e ".[dev]"
  # or: pip install -r requirements.txt
  ```

---

## 4. OS-Specific USB-Serial Setup (ESP32-S3 Hardware)

> [!TIP]
> **Running Offline Only?**
> If you are only analyzing the Zenodo dataset, training models, or executing the offline Jupyter Notebooks (`01_eda` through `04_modeling` and `05_generalization/02_model_evaluation.ipynb`), **no physical ESP32-S3 hardware is required** and you can skip this section.

When connecting an ESP32-S3 RX node via USB for real-time presence detection (`make live`) or raw data acquisition (`00_acquisition/`), serial port naming and permissions depend on your operating system:

| Operating System | Typical UART Bridge Port (`CP210x` / `CH34x`) | Typical Native USB/JTAG Port | Driver / Permission Requirement |
| :--- | :--- | :--- | :--- |
| **Linux** | `/dev/ttyUSB0`, `/dev/ttyUSB1` | `/dev/ttyACM0`, `/dev/ttyACM1` | User must belong to `dialout` (Debian/Ubuntu/Fedora) or `uucp` (Arch) group. |
| **Windows** | `COM3`, `COM4`, `COM5`, ... | `COM3`, `COM4`, ... | Silicon Labs CP210x or WCH CH34x USB-to-UART driver (if using UART bridge port). |
| **macOS** | `/dev/cu.usbserial-0001`, `/dev/cu.SLAB_USBtoUART` | `/dev/cu.usbmodem1101` | Built-in CDC/serial drivers; always use `/dev/cu.*` (call-out) rather than `/dev/tty.*`. |

### 4.1 Listing Connected Serial Ports (All Platforms)

With the ESP32-S3 plugged in, you can inspect all detected serial ports on Linux, macOS, or Windows using:

```bash
uv run python -m serial.tools.list_ports -v
```

The real-time inference engine (`scripts/realtime_presence.py`) automatically scans for Espressif/UART USB Vendor IDs (`0x303A`, `0x10C4`, `0x1A86`, `0x0403`) and OS-specific device paths when `--port auto` (default) is used. You can also specify the port explicitly:

```bash
# Linux example
uv run python scripts/realtime_presence.py --port /dev/ttyUSB0

# Windows example
uv run python scripts/realtime_presence.py --port COM3

# macOS example
uv run python scripts/realtime_presence.py --port /dev/cu.usbserial-0001
```

### 4.2 Linux Serial Port Permissions (`PermissionError: [Errno 13]`)

On Linux distributions, serial devices (`/dev/ttyUSB*` and `/dev/ttyACM*`) are owned by the `dialout` (or `uucp`) group. If you encounter `PermissionError: [Errno 13] Permission denied`, add your user to the group:

```bash
# Ubuntu / Debian / Fedora / RHEL:
sudo usermod -a -G dialout $USER

# Arch Linux:
sudo usermod -a -G uucp $USER
```
Log out and log back in (or run `newgrp dialout`) for the group membership to take effect.

### 4.3 Windows USB Drivers & Terminal Rendering

1. **USB-to-UART Drivers:** Check **Device Manager -> Ports (COM & LPT)**. If the ESP32-S3 appears under *Other devices* with a warning icon, install the [Silicon Labs CP210x Universal Windows Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) or WCH CH34x driver matching your board's bridge chip.
2. **Terminal Dashboard:** `scripts/realtime_presence.py` automatically enables Windows Console Virtual Terminal Processing (`ENABLE_VIRTUAL_TERMINAL_PROCESSING`) and reconfigures `stdout`/`stderr` to `UTF-8`. For the best visual experience with Unicode box-drawing gauges, **Windows Terminal** (or VS Code's integrated terminal) is recommended.
3. **WSL2 Note:** If running inside WSL2 on Windows, either run the live monitor directly from native Windows PowerShell (`.\make live`) or forward the USB bus into WSL2 using [`usbipd-win`](https://learn.microsoft.com/en-us/windows/wsl/connect-usb).

### 4.4 macOS Call-Out Devices (`/dev/cu.*` vs. `/dev/tty.*`)

On macOS, each USB serial device exposes two device nodes: `/dev/tty.*` (dial-in, which blocks waiting for a Data Carrier Detect signal) and `/dev/cu.*` (call-out, which opens immediately). Always specify `/dev/cu.usbserial-*` or `/dev/cu.usbmodem*`. Note that `find_serial_port()` automatically normalizes `/dev/tty.usb*` paths to `/dev/cu.usb*` on macOS.

---

## 5. Troubleshooting Common Issues

| Symptom / Error Message | Cause | Solution |
| :--- | :--- | :--- |
| `error: No virtual environment found; run uv venv to create an environment` | Running `uv pip install` directly in a fresh clone before `.venv/` exists. | Run `make install` (Linux/macOS), `.\make install` (Windows), or `uv sync --extra dev`. |
| `'make' is not recognized as an internal or external command` (Windows) | GNU `make` is not installed by default on Windows. | Use the included Windows wrappers: `.\make <target>` (CMD/PowerShell) or `.\make.ps1 <target>` (PowerShell). |
| `File scripts\...\make.ps1 cannot be loaded because running scripts is disabled` (Windows PowerShell) | PowerShell execution policy restricts local `.ps1` scripts. | Use `.\make <target>` (which invokes `make.bat`), or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| `FileNotFoundError: No Zenodo backup archives found` or missing `.parquet` / `.joblib` files | Raw data, processed splits, and trained models are stored on Zenodo and ignored by Git. | Run `make fetch-zenodo` (Linux/macOS) or `.\make fetch-zenodo` (Windows) to download and restore all dataset and model files. |
| `ModuleNotFoundError: No module named 'wifi_csi'` or `'pywt'` in Jupyter | Jupyter Notebook is running with a system/global Python kernel instead of the project's `.venv`. | Launch Jupyter via `make notebook` (`uv run jupyter lab`), or in VS Code select the `.venv` Python interpreter as the notebook kernel. |
