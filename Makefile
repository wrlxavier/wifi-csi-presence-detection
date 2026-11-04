.PHONY: help install test notebook jupyter notebook-classic live live-reduced live-light live-svm-light live-mlp-light live-rf-light live-gb-light clean compress backup restore decompress zenodo compress-zenodo restore-zenodo decompress-zenodo download-zenodo fetch-zenodo

UV := uv

# Optional target archive argument: make compress ARCHIVE=my_backup.zip or FILE=...
ARCHIVE_ARG := $(if $(ARCHIVE),--file "$(ARCHIVE)",$(if $(FILE),--file "$(FILE)",))

help:
	@echo "Available commands (Linux / macOS / Windows):"
	@echo "  make install         - Create .venv and install project + dev/notebook dependencies via uv"
	@echo "  make fetch-zenodo    - Download and restore official Zenodo dataset & models in one step"
	@echo "  make download-zenodo - Download official dataset archive from Zenodo (record 23960575)"
	@echo "  make restore         - Restore and validate Zenodo dataset archive (opt: ARCHIVE=name.zip)"
	@echo "  make compress        - Package Zenodo academic dataset archive into outputs/backups/ (opt: ARCHIVE=name.zip)"
	@echo "  make test            - Run automated pytest suite"
	@echo "  make notebook        - Launch interactive JupyterLab server in the project environment"
	@echo "  make jupyter         - Alias for make notebook"
	@echo "  make notebook-classic- Launch classic Jupyter Notebook interface"
	@echo "  make live            - Launch real-time presence detection live monitor (model menu)"
	@echo "  make live-reduced    - Launch real-time presence detection with recommended light model (5 SCs)"
	@echo "  make live-light      - Alias for live-reduced"
	@echo "  make live-svm-light  - Launch real-time presence detection with lightweight SVM (83 KB, 5 SCs)"
	@echo "  make live-mlp-light  - Launch real-time presence detection with lightweight MLP (3 us, 5 SCs)"
	@echo "  make live-rf-light   - Launch real-time presence detection with lightweight Random Forest (5 SCs)"
	@echo "  make live-gb-light   - Launch real-time presence detection with lightweight Gradient Boosting (5 SCs)"
	@echo "  make clean           - Clean Python bytecode caches and transient build files"

install:
	$(UV) sync --extra dev

test:
	$(UV) run pytest tests/ -v

notebook:
	$(UV) run jupyter lab

jupyter: notebook

notebook-classic:
	$(UV) run jupyter notebook

live:
	$(UV) run python scripts/realtime_presence.py

live-reduced:
	$(UV) run python scripts/realtime_presence.py --reduced

live-light: live-reduced

live-svm-light:
	$(UV) run python scripts/realtime_presence.py --model svm_light

live-mlp-light:
	$(UV) run python scripts/realtime_presence.py --model mlp_light

live-rf-light:
	$(UV) run python scripts/realtime_presence.py --model random_forest_light

live-gb-light:
	$(UV) run python scripts/realtime_presence.py --model gradient_boosting_light

compress:
	$(UV) run python scripts/backup_data.py compress $(ARCHIVE_ARG)

backup: compress

compress-zenodo: compress

zenodo: compress

restore:
	$(UV) run python scripts/backup_data.py restore $(ARCHIVE_ARG)

decompress: restore

restore-zenodo: restore

decompress-zenodo: restore

download-zenodo:
	$(UV) run python scripts/backup_data.py download $(ARCHIVE_ARG)

fetch-zenodo:
	$(UV) run python scripts/backup_data.py fetch $(ARCHIVE_ARG)

clean:
	$(UV) run python scripts/backup_data.py clean
