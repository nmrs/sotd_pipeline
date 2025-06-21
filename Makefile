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

test-fast:
	PYTHONPATH=. pytest tests/ -n 4 -q

test-parallel:
	PYTHONPATH=. pytest tests/ -n auto -q

test-slow:
	PYTHONPATH=. pytest tests/ --durations=10 -v

coverage:
	pytest --cov=sotd --cov-report=term-missing tests/

# Individual phase targets (with --force flag as per development rules)
fetch:
	python sotd/fetch/run.py --month 2025-05 --force

extract:
	python sotd/extract/run.py --month 2025-05 --force

match:
	python sotd/match/run.py --month 2025-05 --force

enrich:
	python sotd/enrich/run.py --month 2025-05 --force

aggregate:
	python sotd/aggregate/run.py --month 2025-05 --force

# Pipeline targets (using unified run.py orchestration)
pipeline:
	python run.py pipeline --month 2025-05 --force

pipeline-debug:
	python run.py pipeline --month 2025-05 --force --debug

# Performance testing
performance-test:
	python run.py aggregate --month 2025-01 --force --debug
	python run.py aggregate --month 2025-02 --force --debug

# Install dependencies
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt