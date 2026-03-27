.DEFAULT_GOAL := help
SHELL := /bin/bash

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

.PHONY: lock-install install install-dev update

lock-install: ## Lock and install project dependencies
	poetry lock
	poetry install

install: ## Install project with all dependencies
	poetry install

install-dev: ## Install with dev dependencies
	poetry install --with dev

update: ## Update dependencies
	poetry update

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

.PHONY: lint lint-fix format format-check fix

lint: ## Run ruff linter
	poetry run ruff check pluginforge/ tests/

lint-fix: ## Run ruff linter with auto-fix
	poetry run ruff check pluginforge/ tests/ --fix --unsafe-fixes

format: ## Format code with ruff
	poetry run ruff format pluginforge/ tests/

format-check: ## Check formatting without changes
	poetry run ruff format --check pluginforge/ tests/

fix: ## Run all auto-fixes (lint + format)
	poetry run ruff check pluginforge/ tests/ --fix --unsafe-fixes
	poetry run ruff format pluginforge/ tests/

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

.PHONY: test test-v test-fast test-cov test-xml

test: ## Run all tests
	poetry run pytest

test-v: ## Run all tests (verbose)
	poetry run pytest -v

test-fast: ## Run tests without coverage (faster)
	poetry run pytest -q --maxfail=1 --disable-warnings --no-cov

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=pluginforge --cov-report=term-missing

test-xml: ## Run tests with XML coverage (for CI)
	poetry run pytest -q --maxfail=1 --disable-warnings --cov=pluginforge --cov-report=xml

# ---------------------------------------------------------------------------
# CI
# ---------------------------------------------------------------------------

.PHONY: ci

ci: lint format-check test ## Full CI pipeline (lint + format-check + test)

# ---------------------------------------------------------------------------
# Version Management
# ---------------------------------------------------------------------------

.PHONY: bump-patch bump-minor bump-major

bump-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	poetry version patch

bump-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	poetry version minor

bump-major: ## Bump major version (0.1.0 -> 1.0.0)
	poetry version major

# ---------------------------------------------------------------------------
# Build & Publish
# ---------------------------------------------------------------------------

.PHONY: build publish publish-test

build: ## Build distribution package
	poetry build

publish: ci build ## Run CI, build and publish to PyPI
	poetry publish

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

.PHONY: clean clean-venv

clean: ## Remove build artifacts and caches
	rm -rf dist/ build/ .pytest_cache/ .ruff_cache/ .mypy_cache/ .coverage coverage.xml
	find pluginforge/ tests/ -type d -name __pycache__ -exec rm -rf {} +
	find . -name '*.pyc' -delete

clean-venv: ## Remove Poetry virtualenv
	poetry env remove --all || true

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
