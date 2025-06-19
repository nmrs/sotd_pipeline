.PHONY: all lint format typecheck test coverage fetch enrich aggregate

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

fetch:
	python sotd/fetch/run.py --month 2025-05

enrich:
	python sotd/enrich/run.py --month 2025-05

aggregate:
	python sotd/aggregate/run.py --month 2025-05