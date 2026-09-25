.PHONY: help install test live live-reduced live-light live-svm-light live-mlp-light live-rf-light live-gb-light clean compress backup restore decompress

UV := uv

# Optional target archive argument: make compress ARCHIVE=my_backup.zip or FILE=...
ARCHIVE_ARG := $(if $(ARCHIVE),--file "$(ARCHIVE)",$(if $(FILE),--file "$(FILE)",))

help:
	@echo "Available commands:"
	@echo "  make install       - Install project in editable mode via uv"
	@echo "  make test          - Run automated pytest suite"
	@echo "  make live          - Launch real-time presence detection live monitor (model menu)"
	@echo "  make live-reduced  - Launch real-time presence detection with recommended light model (5 SCs)"
	@echo "  make live-light    - Alias for live-reduced"
	@echo "  make live-svm-light- Launch real-time presence detection with lightweight SVM (83 KB, 5 SCs)"
	@echo "  make live-mlp-light- Launch real-time presence detection with lightweight MLP (3 us, 5 SCs)"
	@echo "  make live-rf-light - Launch real-time presence detection with lightweight Random Forest (5 SCs)"
	@echo "  make live-gb-light - Launch real-time presence detection with lightweight Gradient Boosting (5 SCs)"
	@echo "  make compress      - Compress untracked/ignored data into outputs/backups/ (opt: ARCHIVE=name.zip)"
	@echo "  make restore       - Restore data from compressed archive in outputs/backups/ (opt: ARCHIVE=name.zip)"
	@echo "  make clean         - Clean cache and transient build files"

install:
	$(UV) pip install -e ".[dev]"

test:
	$(UV) run pytest tests/ -v

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

restore:
	$(UV) run python scripts/backup_data.py restore $(ARCHIVE_ARG)

decompress: restore


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache/
