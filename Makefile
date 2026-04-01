.PHONY: lint format typecheck test test-all integration coverage docs build clean

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy --strict src/abovepy/

test:
	pytest tests/

test-all:
	pytest tests/ -m ""

integration:
	pytest tests/ -m "integration" -v --timeout=120

coverage:
	pytest tests/ --cov=abovepy --cov-report=html
	@echo "Open htmlcov/index.html to view report"

docs:
	zensical build

docs-serve:
	zensical serve

build:
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage coverage.xml site/
