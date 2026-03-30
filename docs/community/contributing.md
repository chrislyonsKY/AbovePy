# Contributing to abovepy

Thank you for your interest in contributing to abovepy! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/abovepy.git
   cd abovepy
   ```
3. **Install** in development mode:
   ```bash
   pip install -e ".[dev,docs]"
   ```

## Development Workflow

### Branch Naming

- `feature/description` — new functionality
- `fix/description` — bug fixes
- `docs/description` — documentation changes
- `refactor/description` — code improvements without behavior changes

### Running Tests

```bash
# Unit tests (no network required)
pytest tests/ -v

# Integration tests (hits live STAC API)
pytest tests/ -m integration -v

# Full suite with coverage
pytest tests/ --cov=abovepy --cov-report=term-missing
```

### Code Quality

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy-lang.org/) for type checking:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy --strict src/abovepy/
```

All three must pass before merging. CI runs these automatically.

### Code Style

- **Line length:** 100 characters
- **Target:** Python 3.10+
- **Type annotations:** Required on all public functions (`mypy --strict`)
- **Imports:** Use `httpx` (not `requests`). Lazy-import optional deps (`laspy`, `boto3`, `pdal`)
- **Docstrings:** NumPy style

## Architecture

- **One `search()` function** — product is a parameter, not a separate module
- **Product keys** map to STAC collection IDs internally (`dem_phase3` -> `dem-phase3`)
- **All bbox inputs** accept EPSG:4326; KyFromAbove native CRS is EPSG:3089
- **No credentials required** — the S3 bucket is public
- **Return types:** `search()` -> GeoDataFrame, `download()` -> list[Path], `read()` -> (ndarray, profile)

See [docs/architecture.md](docs/architecture.md) for the full design.

## Submitting Changes

1. Create a feature branch from `main`
2. Make your changes with clear, focused commits
3. Ensure all tests pass and linting is clean
4. Open a Pull Request with:
   - A clear title describing the change
   - A summary of what and why
   - Any relevant issue numbers

## Reporting Bugs

Open an [issue](https://github.com/chrislyonsKY/abovepy/issues) with:

- Python version and OS
- abovepy version (`python -c "import abovepy; print(abovepy.__version__)"`)
- Minimal code to reproduce the problem
- Full traceback if applicable

## Feature Requests

Open an [issue](https://github.com/chrislyonsKY/abovepy/issues) describing:

- The use case or problem you're trying to solve
- How you'd expect the API to work
- Any relevant KyFromAbove data products or workflows

## License

By contributing, you agree that your contributions will be licensed under the [GPL-3.0 License](LICENSE).
