# New Body — developer convenience targets
# Usage: make <target>

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

.PHONY: install install-dev test lint format format-check clean

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests examples
	$(PYTHON) -m black --check src tests examples

format:
	$(PYTHON) -m ruff check --fix src tests examples
	$(PYTHON) -m black src tests examples

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache build dist *.egg-info
