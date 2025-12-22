.PHONY: install install-dev test lint format clean build publish

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=zeus --cov-report=html --cov-report=term

lint:
	pylint zeus/
	mypy zeus/

format:
	black zeus/ tests/ examples/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

publish: build
	twine upload dist/*

dev-install:
	pip install -e .
