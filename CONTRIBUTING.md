# Contributing to MetDataPy

Thank you for your interest in contributing! This guide explains how to set up your environment, propose changes, and follow project conventions.

## Getting started

- Fork the repo and create a feature branch from `main`.
- Use recent Python (>=3.9). Install in editable mode:
  ```bash
  python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
  python -m pip install -U pip
  python -m pip install -e .
  python -m pip install pytest mkdocs
  ```

## Running tests and docs

- Tests:
  ```bash
  python -m pytest -q
  ```
- Docs (MkDocs):
  ```bash
  mkdocs serve   # live preview
  mkdocs build   # static site in site/
  ```

## Coding standards

- Write clear, readable, and typed Python where reasonable.
- Prefer vectorized `pandas`/`numpy` operations; avoid unnecessary loops.
- Keep public APIs stable; add deprecations with care.
- Lint/formatting (to be enabled in CI): ruff, black; typing with mypy.
- Match existing code style and avoid unrelated reformatting.

## Pull requests

- Scope PRs narrowly; include tests and docs for new features.
- Update `README.md` and relevant pages in `docs/` when behavior changes.
- Add entries/checkmarks to `TO-DO.md` when features are implemented.
- Explain motivation, approach, and any trade-offs in the PR description.

## Issue reporting

- Include minimal reproducible examples, data snippets, versions, and OS.
- Label issues appropriately (bug, enhancement, docs, question).

## Security and conduct

- Please avoid sharing sensitive data in issues/PRs.
- Be respectful and professional. See `CODE_OF_CONDUCT.md`.

## Release process (outline)

- Ensure tests/docs pass on CI; bump version in `pyproject.toml`.
- Tag the release; publish wheels/sdist to PyPI; archive on Zenodo (planned).

Thanks again for contributing!
