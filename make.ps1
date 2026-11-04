<#
.SYNOPSIS
    Cross-platform PowerShell automation runner for Wi-Fi CSI Presence Detection.
.DESCRIPTION
    Provides the same targets as the Unix Makefile on Windows PowerShell and PowerShell Core.
.EXAMPLE
    .\make.ps1 install
    .\make.ps1 fetch-zenodo
    .\make.ps1 test
    .\make.ps1 notebook
    .\make.ps1 live
#>

param(
    [Parameter(Position = 0)]
    [string]$Target = "help",

    [Parameter(Position = 1)]
    [string]$Archive = ""
)

$ErrorActionPreference = "Stop"

# Support ARCHIVE=name.zip or FILE=name.zip syntax if passed as second argument
if ($Archive -match "^(ARCHIVE|FILE)=(.+)$") {
    $Archive = $Matches[2]
}

$ArchiveArgs = @()
if (-not [string]::IsNullOrWhiteSpace($Archive)) {
    $ArchiveArgs = @("--file", $Archive)
}

function Show-Help {
    Write-Host "Available commands (PowerShell):" -ForegroundColor Cyan
    Write-Host "  .\make.ps1 install          - Create .venv and install project + dev/notebook dependencies via uv"
    Write-Host "  .\make.ps1 fetch-zenodo     - Download and restore official Zenodo dataset & models in one step"
    Write-Host "  .\make.ps1 download-zenodo  - Download official dataset archive from Zenodo (record 23960575)"
    Write-Host "  .\make.ps1 restore          - Restore and validate Zenodo dataset archive (opt: -Archive name.zip)"
    Write-Host "  .\make.ps1 compress         - Package Zenodo academic dataset archive into outputs/backups/"
    Write-Host "  .\make.ps1 test             - Run automated pytest suite"
    Write-Host "  .\make.ps1 notebook         - Launch interactive JupyterLab server in the project environment"
    Write-Host "  .\make.ps1 jupyter          - Alias for .\make.ps1 notebook"
    Write-Host "  .\make.ps1 notebook-classic - Launch classic Jupyter Notebook interface"
    Write-Host "  .\make.ps1 live             - Launch real-time presence detection live monitor (model menu)"
    Write-Host "  .\make.ps1 live-reduced     - Launch real-time presence detection with recommended light model (5 SCs)"
    Write-Host "  .\make.ps1 live-light       - Alias for .\make.ps1 live-reduced"
    Write-Host "  .\make.ps1 live-svm-light   - Launch real-time presence detection with lightweight SVM (83 KB, 5 SCs)"
    Write-Host "  .\make.ps1 live-mlp-light   - Launch real-time presence detection with lightweight MLP (3 us, 5 SCs)"
    Write-Host "  .\make.ps1 live-rf-light    - Launch real-time presence detection with lightweight Random Forest (5 SCs)"
    Write-Host "  .\make.ps1 live-gb-light    - Launch real-time presence detection with lightweight Gradient Boosting (5 SCs)"
    Write-Host "  .\make.ps1 clean            - Clean Python bytecode caches and transient build files"
}

switch ($Target.ToLower()) {
    "help"             { Show-Help }
    "install"          { & uv sync --extra dev; exit $LASTEXITCODE }
    "test"             { & uv run pytest tests/ -v; exit $LASTEXITCODE }
    "notebook"         { & uv run jupyter lab; exit $LASTEXITCODE }
    "jupyter"          { & uv run jupyter lab; exit $LASTEXITCODE }
    "notebook-classic" { & uv run jupyter notebook; exit $LASTEXITCODE }
    "live"             { & uv run python scripts/realtime_presence.py; exit $LASTEXITCODE }
    "live-reduced"     { & uv run python scripts/realtime_presence.py --reduced; exit $LASTEXITCODE }
    "live-light"       { & uv run python scripts/realtime_presence.py --reduced; exit $LASTEXITCODE }
    "live-svm-light"   { & uv run python scripts/realtime_presence.py --model svm_light; exit $LASTEXITCODE }
    "live-mlp-light"   { & uv run python scripts/realtime_presence.py --model mlp_light; exit $LASTEXITCODE }
    "live-rf-light"    { & uv run python scripts/realtime_presence.py --model random_forest_light; exit $LASTEXITCODE }
    "live-gb-light"    { & uv run python scripts/realtime_presence.py --model gradient_boosting_light; exit $LASTEXITCODE }
    { $_ -in "compress", "backup", "zenodo", "compress-zenodo" } {
        & uv run python scripts/backup_data.py compress @ArchiveArgs
        exit $LASTEXITCODE
    }
    { $_ -in "restore", "decompress", "restore-zenodo", "decompress-zenodo" } {
        & uv run python scripts/backup_data.py restore @ArchiveArgs
        exit $LASTEXITCODE
    }
    "download-zenodo" {
        & uv run python scripts/backup_data.py download @ArchiveArgs
        exit $LASTEXITCODE
    }
    "fetch-zenodo" {
        & uv run python scripts/backup_data.py fetch @ArchiveArgs
        exit $LASTEXITCODE
    }
    "clean" {
        & uv run python scripts/backup_data.py clean
        exit $LASTEXITCODE
    }
    default {
        Write-Host "[ERROR] Unknown target: '$Target'" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
