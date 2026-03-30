# Development Guide

## Prerequisites

- Python 3.11 or later
- Git

## Setup

```bash
git clone https://github.com/chrislyonsKY/AbovePy.git
cd AbovePy
pip install -e ".[dev,docs]"
```

This installs the package in editable mode with all development and
documentation dependencies.

## Running Tests

```bash
# Unit tests (no network required)
pytest tests/ -v

# Integration tests (hits live KyFromAbove STAC API)
pytest tests/ -m integration -v

# Full suite with coverage
pytest tests/ --cov=abovepy --cov-report=term-missing
```

## Linting and Formatting

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and
formatting:

```bash
ruff check src/ tests/
ruff format --check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Auto-format
ruff format src/ tests/
```

## Type Checking

[mypy](https://mypy-lang.org/) runs in strict mode:

```bash
mypy --strict src/abovepy/
```

All public functions must have complete type annotations.

## Documentation

Documentation is built with [MkDocs Material](https://squidfunnel.github.io/mkdocs-material/):

```bash
mkdocs serve        # Local preview at http://127.0.0.1:8000
mkdocs build        # Build static site
```

## Branch Strategy

- `main` is the stable branch; all releases are tagged from `main`
- Create feature branches from `main` using the naming conventions:
  - `feature/description` -- new functionality
  - `fix/description` -- bug fixes
  - `docs/description` -- documentation changes
  - `refactor/description` -- code improvements without behavior changes

## Commit Conventions

- Write clear, concise commit messages describing **what** and **why**
- Reference issue numbers where applicable (e.g., `Fixes #42`)
- Keep commits focused; avoid mixing unrelated changes

## CI Pipeline

GitHub Actions runs on every push and pull request:

- **Lint:** `ruff check` and `ruff format --check`
- **Type check:** `mypy --strict`
- **Tests:** pytest matrix across ubuntu, macos, and windows on Python 3.11--3.13

All checks must pass before merging.

## Optional Extras

Install specific feature groups as needed:

```bash
pip install -e ".[lidar]"      # laspy, pdal for point cloud work
pip install -e ".[viz]"        # matplotlib, folium for visualization
pip install -e ".[s3]"         # boto3 for direct S3 access
pip install -e ".[analysis]"   # scipy, scikit-image for terrain analysis
pip install -e ".[all]"        # Everything above
```
