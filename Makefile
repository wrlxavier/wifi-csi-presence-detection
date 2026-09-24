.PHONY: help install test live clean

UV := uv

help:
	@echo "Available commands:"
	@echo "  make install    - Install project in editable mode via uv"
	@echo "  make test       - Run automated pytest suite"
	@echo "  make live       - Launch real-time presence detection live monitor"
	@echo "  make clean      - Clean cache and transient build files"

install:
	$(UV) pip install -e ".[dev]"

test:
	$(UV) run pytest tests/ -v

live:
	$(UV) run python scripts/realtime_presence.py


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache/
