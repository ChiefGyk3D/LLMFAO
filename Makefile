# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later

# Everything CI runs, runnable here.

PY ?= .venv/bin/python

.PHONY: help venv lint format typecheck test check clean

help:
	@echo "make venv      - .venv with the dev tools"
	@echo "make lint      - ruff check + ruff format --check"
	@echo "make typecheck - mypy --strict"
	@echo "make test      - pytest"
	@echo "make check     - all three. Run before pushing."

venv:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check src tests scripts
	$(PY) -m ruff format --check src tests scripts

format:
	$(PY) -m ruff format src tests scripts

typecheck:
	$(PY) -m mypy

test:
	$(PY) -m pytest -W error::DeprecationWarning

check: lint typecheck test
	@echo "all checks passed"

clean:
	rm -rf dist build .pytest_cache .ruff_cache .mypy_cache src/*.egg-info
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
