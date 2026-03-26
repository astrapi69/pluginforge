.PHONY: install test lint format build publish-test publish clean

install:
	poetry install --with dev

test:
	poetry run pytest

lint:
	poetry run ruff check pluginforge/ tests/

format:
	poetry run ruff format pluginforge/ tests/

build:
	poetry build

publish-test:
	poetry publish -r testpypi

publish:
	poetry publish

clean:
	rm -rf dist/ .pytest_cache/ .coverage
