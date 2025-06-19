.PHONY: all lint format typecheck test coverage fetch extract match enrich aggregate pipeline performance-test install install-dev

all: lint format typecheck test

# Lint with Ruff
lint:
	ruff check .

# Format code: Black first, then Ruff's auto-formatter (optional)
format: ruff-format
	black .

ruff-format:
	ruff format .

typecheck:
	pyright

test:
	PYTHONPATH=. pytest tests/

coverage:
	pytest --cov=sotd --cov-report=term-missing tests/

# Individual phase targets
fetch:
	python sotd/fetch/run.py --month 2025-05

extract:
	python sotd/extract/run.py --month 2025-05

match:
	python sotd/match/run.py --month 2025-05

enrich:
	python sotd/enrich/run.py --month 2025-05

aggregate:
	python sotd/aggregate/run.py --month 2025-05

# Pipeline targets
pipeline:
	python run.py pipeline --month 2025-05

pipeline-debug:
	python run.py pipeline --month 2025-05 --debug

# Performance testing
performance-test:
	python run.py aggregate --month 2025-01 --debug
	python run.py aggregate --month 2025-02 --debug

# Install dependencies
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt