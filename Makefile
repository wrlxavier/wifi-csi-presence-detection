.PHONY: help install pipeline train evaluate figures test all clean live

UV := uv

help:
	@echo "Available commands:"
	@echo "  make install    - Install project in editable mode via uv"
	@echo "  make pipeline   - Run raw CSI parsing & feature extraction pipeline"
	@echo "  make train      - Train ML models and register bundled pipelines"
	@echo "  make evaluate   - Evaluate test set and compute robustness benchmarks"
	@echo "  make figures    - Generate all publication-ready figures & LaTeX tables"
	@echo "  make test       - Run automated pytest suite"
	@echo "  make live       - Launch real-time presence detection live monitor"
	@echo "  make all        - Execute pipeline -> train -> evaluate -> figures"
	@echo "  make clean      - Clean cache and transient build files"


install:
	$(UV) pip install -e ".[dev]"

pipeline:
	$(UV) run python scripts/run_pipeline.py --config configs/pipeline.yaml

train:
	$(UV) run python scripts/train_models.py --config configs/models.yaml

evaluate:
	$(UV) run python scripts/evaluate.py --config configs/models.yaml

figures:
	$(UV) run python scripts/export_thesis_assets.py --output reports/

test:
	$(UV) run pytest tests/ -v

live:
	$(UV) run python scripts/realtime_presence.py

all: pipeline train evaluate figures


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache/
