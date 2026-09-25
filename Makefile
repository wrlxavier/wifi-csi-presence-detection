.PHONY: help install test live clean compress backup restore decompress

UV := uv

# Optional target archive argument: make compress ARCHIVE=my_backup.zip or FILE=...
ARCHIVE_ARG := $(if $(ARCHIVE),--file "$(ARCHIVE)",$(if $(FILE),--file "$(FILE)",))

help:
	@echo "Available commands:"
	@echo "  make install    - Install project in editable mode via uv"
	@echo "  make test       - Run automated pytest suite"
	@echo "  make live       - Launch real-time presence detection live monitor"
	@echo "  make compress   - Compress untracked/ignored data into outputs/backups/ (opt: ARCHIVE=name.zip)"
	@echo "  make restore    - Restore data from compressed archive in outputs/backups/ (opt: ARCHIVE=name.zip)"
	@echo "  make clean      - Clean cache and transient build files"

install:
	$(UV) pip install -e ".[dev]"

test:
	$(UV) run pytest tests/ -v

live:
	$(UV) run python scripts/realtime_presence.py

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
