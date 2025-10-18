# CI/CD Setup Documentation

This document describes the Continuous Integration and Continuous Deployment setup for MetDataPy.

## Overview

MetDataPy uses GitHub Actions for CI/CD with multiple workflows to ensure code quality, test coverage, and documentation integrity. Documentation is hosted on Read the Docs with automatic builds on every commit.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:** Push and PR to `main`, `master`, `develop` branches

**Jobs:**

#### Test Job
- **Matrix Testing:**
  - OS: Ubuntu, macOS, Windows
  - Python: 3.9, 3.10, 3.11, 3.12
  - Total: 12 test combinations
- **Coverage Reporting:**
  - Uses `pytest-cov` for coverage measurement
  - Uploads coverage to Codecov (Ubuntu + Python 3.11 only)
  - Generates XML and terminal reports
- **Dependencies:**
  - Core: pandas, numpy, click, pyyaml, pydantic
  - Optional: xarray, netCDF4, scikit-learn

#### Lint Job
- **Tools:**
  - `ruff`: Fast Python linter
  - `black`: Code formatter
  - `isort`: Import sorter
  - `mypy`: Static type checker
- **Configuration:** All tools configured in `pyproject.toml`
- **Behavior:** Continue on error (non-blocking)

#### Docs Job
- **Documentation Build:**
  - Uses MkDocs with Material theme
  - Builds with `--strict` flag (warnings as errors)
  - Checks for broken links with `linkchecker`
- **Output:** Static site in `site/` directory
- **Deployment:** Documentation is automatically built and deployed to Read the Docs on push to main/master

#### Integration Job
- **End-to-End Testing:**
  - Generates sample data
  - Runs complete workflow script
  - Runs NetCDF export example
  - Verifies output files exist
- **Purpose:** Ensures all components work together

#### Package Job
- **Package Validation:**
  - Checks MANIFEST.in with `check-manifest`
  - Builds source and wheel distributions
  - Validates with `twine check`
  - Uploads artifacts for inspection

### 2. Documentation Workflow (`.github/workflows/docs.yml`)

**Triggers:** Push to `main`/`master`, PR, manual dispatch

**Jobs:**

#### Build
- Builds MkDocs documentation
- Uploads as GitHub Pages artifact

#### Deploy
- Deploys to GitHub Pages (only on push to main/master)
- Requires GitHub Pages to be enabled in repository settings

## Configuration Files

### `pyproject.toml`
Contains configuration for:
- **pytest:** Test discovery, markers, strict mode
- **coverage:** Source paths, omit patterns, exclusion rules
- **ruff:** Line length, target version, select/ignore rules
- **black:** Line length, target Python versions
- **isort:** Profile (black-compatible), line length
- **mypy:** Python version, type checking strictness

### `.coveragerc`
Additional coverage configuration:
- Source paths and omit patterns
- Report precision and formatting
- HTML and XML output settings

### `MANIFEST.in`
Specifies files to include in source distribution:
- Source code, tests, docs
- License, README, CITATION.cff
- Configuration files
- Sample data

## Badges

The following badges are displayed in README.md:

```markdown
[![CI](https://github.com/kkartas/MetDataPy/actions/workflows/ci.yml/badge.svg)](https://github.com/kkartas/MetDataPy/actions/workflows/ci.yml)
[![Documentation](https://github.com/kkartas/MetDataPy/actions/workflows/docs.yml/badge.svg)](https://github.com/kkartas/MetDataPy/actions/workflows/docs.yml)
[![codecov](https://codecov.io/gh/kkartas/MetDataPy/branch/main/graph/badge.svg)](https://codecov.io/gh/kkartas/MetDataPy)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

## Local Development

### Running Tests with Coverage

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-xdist

# Run tests with coverage
python -m pytest --cov=metdatapy --cov-report=term --cov-report=html -v

# View HTML coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Running Linters

```bash
# Install linting tools
pip install ruff black isort mypy

# Run all linters
ruff check metdatapy tests
black --check metdatapy tests
isort --check-only metdatapy tests
mypy metdatapy --ignore-missing-imports

# Auto-fix issues
ruff check --fix metdatapy tests
black metdatapy tests
isort metdatapy tests
```

### Building Documentation

```bash
# Install docs dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve locally (with live reload)
mkdocs serve

# Build static site
mkdocs build --strict
```

### Building Package

```bash
# Install build tools
pip install build twine check-manifest

# Check manifest
check-manifest

# Build distributions
python -m build

# Check package
twine check dist/*
```

## Codecov Integration

### Setup

1. Sign up at [codecov.io](https://codecov.io) with GitHub account
2. Add MetDataPy repository
3. Get upload token from Codecov dashboard
4. Add token as GitHub secret: `CODECOV_TOKEN`

### Coverage Thresholds

Current coverage: **63%**

Target coverage for JOSS submission: **>70%**

Areas needing more tests:
- `metdatapy/core.py` (41.78% → target 80%)
- `metdatapy/mlprep.py` (0% → target 70%)
- `metdatapy/utils.py` (48.28% → target 70%)

## Read the Docs Setup

Documentation is hosted on Read the Docs with automatic builds.

### Configuration Files

- `.readthedocs.yml` - Read the Docs build configuration
- `docs/requirements.txt` - Documentation dependencies
- `mkdocs.yml` - MkDocs site configuration

### Setup Instructions

See `.github/READTHEDOCS_SETUP.md` for detailed setup instructions.

### Documentation URLs

- **Latest (main branch):** https://metdatapy.readthedocs.io/en/latest/
- **Stable (latest release):** https://metdatapy.readthedocs.io/en/stable/
- **Build Status:** Check Read the Docs dashboard

## Troubleshooting

### Coverage Not Uploading
- Check `CODECOV_TOKEN` secret is set
- Verify token has correct permissions
- Check Codecov dashboard for errors

### Docs Build Failing
- Run `mkdocs build --strict` locally
- Check for broken links in markdown
- Verify all referenced files exist

### Tests Failing on Windows
- Check for path separator issues (`/` vs `\`)
- Verify encoding (use UTF-8)
- Check for platform-specific dependencies

### Package Build Failing
- Run `check-manifest` to verify MANIFEST.in
- Ensure all required files are included
- Check for syntax errors in `pyproject.toml`

## Future Enhancements

- [ ] Add security scanning with `bandit`
- [ ] Add dependency vulnerability scanning with `safety`
- [ ] Add performance benchmarking in CI
- [ ] Add automatic release workflow
- [ ] Add changelog generation
- [ ] Add pre-commit hooks
- [ ] Add code quality metrics (SonarQube/Code Climate)

