.PHONY: lint format typecheck test coverage build clean

lint:
	ruff check speechcortex/ tests/

format:
	ruff format speechcortex/ tests/

typecheck:
	mypy speechcortex/

test:
	pytest

coverage:
	pytest --cov=speechcortex --cov-report=term-missing

build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info speechcortex_sdk.egg-info/ .pytest_cache .mypy_cache .ruff_cache htmlcov/ .coverage coverage.xml
