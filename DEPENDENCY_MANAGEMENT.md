# Dependency Management

This project uses `uv` for Python environment and dependency management.

## Required Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Declares runtime and development dependencies |
| `uv.lock` | Locks resolved dependency versions for reproducible installs |
| `.python-version` | Pins the default Python version for local and CI use |

## Setup

```bash
uv sync --extra dev
```

This creates or updates `.venv` and installs the project with development tools.

## Run Commands

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
```

## Add Dependencies

Runtime dependency:

```bash
uv add <package>
```

Development dependency:

```bash
uv add --optional dev <package>
```

After changing dependencies, commit both `pyproject.toml` and `uv.lock`.

## Notes

- Do not use `pip install -e ".[dev]"` for normal project setup.
- GIS dependencies are kept in the optional `gis` extra because they may require system libraries.
- API keys belong in `.env`, copied from `.env.example`.

