@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM Wi-Fi CSI Presence Detection - Windows Batch Automation Wrapper (make.bat)
REM Usage (CMD):        make <target> [archive_name.zip]
REM Usage (PowerShell): .\make <target> [archive_name.zip]
REM ============================================================================

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=help"

set "ARCHIVE_VAL=%~2"
if /I "%~2"=="ARCHIVE" set "ARCHIVE_VAL=%~3"
if /I "%~2"=="FILE" set "ARCHIVE_VAL=%~3"

set "ARCHIVE_ARG="
if not "%ARCHIVE_VAL%"=="" set "ARCHIVE_ARG=--file "%ARCHIVE_VAL%""

if /I "%TARGET%"=="help" goto :help
if /I "%TARGET%"=="install" goto :install
if /I "%TARGET%"=="test" goto :test
if /I "%TARGET%"=="notebook" goto :notebook
if /I "%TARGET%"=="jupyter" goto :notebook
if /I "%TARGET%"=="notebook-classic" goto :notebook_classic
if /I "%TARGET%"=="live" goto :live
if /I "%TARGET%"=="live-reduced" goto :live_reduced
if /I "%TARGET%"=="live-light" goto :live_reduced
if /I "%TARGET%"=="live-svm-light" goto :live_svm_light
if /I "%TARGET%"=="live-mlp-light" goto :live_mlp_light
if /I "%TARGET%"=="live-rf-light" goto :live_rf_light
if /I "%TARGET%"=="live-gb-light" goto :live_gb_light
if /I "%TARGET%"=="compress" goto :compress
if /I "%TARGET%"=="backup" goto :compress
if /I "%TARGET%"=="zenodo" goto :compress
if /I "%TARGET%"=="compress-zenodo" goto :compress
if /I "%TARGET%"=="restore" goto :restore
if /I "%TARGET%"=="decompress" goto :restore
if /I "%TARGET%"=="restore-zenodo" goto :restore
if /I "%TARGET%"=="decompress-zenodo" goto :restore
if /I "%TARGET%"=="download-zenodo" goto :download_zenodo
if /I "%TARGET%"=="fetch-zenodo" goto :fetch_zenodo
if /I "%TARGET%"=="clean" goto :clean

echo [ERROR] Unknown target: "%TARGET%"
echo.
goto :help

:help
echo Available commands (Windows CMD / PowerShell):
echo   .\make install          - Create .venv and install project + dev/notebook dependencies via uv
echo   .\make fetch-zenodo     - Download and restore official Zenodo dataset ^& models in one step
echo   .\make download-zenodo  - Download official dataset archive from Zenodo (record 23960575)
echo   .\make restore          - Restore and validate Zenodo dataset archive (opt: .\make restore name.zip)
echo   .\make compress         - Package Zenodo academic dataset archive into outputs/backups/
echo   .\make test             - Run automated pytest suite
echo   .\make notebook         - Launch interactive JupyterLab server in the project environment
echo   .\make jupyter          - Alias for .\make notebook
echo   .\make notebook-classic - Launch classic Jupyter Notebook interface
echo   .\make live             - Launch real-time presence detection live monitor (model menu)
echo   .\make live-reduced     - Launch real-time presence detection with recommended light model (5 SCs)
echo   .\make live-light       - Alias for .\make live-reduced
echo   .\make live-svm-light   - Launch real-time presence detection with lightweight SVM (83 KB, 5 SCs)
echo   .\make live-mlp-light   - Launch real-time presence detection with lightweight MLP (3 us, 5 SCs)
echo   .\make live-rf-light    - Launch real-time presence detection with lightweight Random Forest (5 SCs)
echo   .\make live-gb-light    - Launch real-time presence detection with lightweight Gradient Boosting (5 SCs)
echo   .\make clean            - Clean Python bytecode caches and transient build files
exit /b 0

:install
uv sync --extra dev
exit /b %ERRORLEVEL%

:test
uv run pytest tests/ -v
exit /b %ERRORLEVEL%

:notebook
uv run jupyter lab
exit /b %ERRORLEVEL%

:notebook_classic
uv run jupyter notebook
exit /b %ERRORLEVEL%

:live
uv run python scripts/realtime_presence.py
exit /b %ERRORLEVEL%

:live_reduced
uv run python scripts/realtime_presence.py --reduced
exit /b %ERRORLEVEL%

:live_svm_light
uv run python scripts/realtime_presence.py --model svm_light
exit /b %ERRORLEVEL%

:live_mlp_light
uv run python scripts/realtime_presence.py --model mlp_light
exit /b %ERRORLEVEL%

:live_rf_light
uv run python scripts/realtime_presence.py --model random_forest_light
exit /b %ERRORLEVEL%

:live_gb_light
uv run python scripts/realtime_presence.py --model gradient_boosting_light
exit /b %ERRORLEVEL%

:compress
uv run python scripts/backup_data.py compress %ARCHIVE_ARG%
exit /b %ERRORLEVEL%

:restore
uv run python scripts/backup_data.py restore %ARCHIVE_ARG%
exit /b %ERRORLEVEL%

:download_zenodo
uv run python scripts/backup_data.py download %ARCHIVE_ARG%
exit /b %ERRORLEVEL%

:fetch_zenodo
uv run python scripts/backup_data.py fetch %ARCHIVE_ARG%
exit /b %ERRORLEVEL%

:clean
uv run python scripts/backup_data.py clean
exit /b %ERRORLEVEL%
