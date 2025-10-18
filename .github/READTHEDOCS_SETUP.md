# Read the Docs Setup Guide

This guide explains how to set up Read the Docs for MetDataPy documentation hosting.

## Overview

MetDataPy uses [Read the Docs](https://readthedocs.org/) for documentation hosting. The documentation is built automatically from the repository using MkDocs with the Material theme.

## Configuration Files

### `.readthedocs.yml`

This is the main configuration file for Read the Docs. It specifies:
- Build environment (Ubuntu 22.04, Python 3.11)
- Documentation tool (MkDocs)
- Python dependencies installation
- Documentation requirements

### `docs/requirements.txt`

Contains all Python packages needed to build the documentation:
- `mkdocs` - Static site generator
- `mkdocs-material` - Material theme for MkDocs
- `mkdocstrings[python]` - API documentation from docstrings
- `pymdown-extensions` - Markdown extensions

### `mkdocs.yml`

MkDocs configuration file that defines:
- Site metadata (name, description, URL)
- Theme settings (Material theme with light/dark mode)
- Navigation structure
- Markdown extensions

## Initial Setup on Read the Docs

### 1. Create Read the Docs Account

1. Go to https://readthedocs.org/
2. Sign up with your GitHub account
3. Authorize Read the Docs to access your repositories

### 2. Import Your Project

1. Click "Import a Project" on your Read the Docs dashboard
2. Find `MetDataPy` in the list of repositories
3. Click the "+" button to import it

### 3. Configure Project Settings

#### Basic Settings
- **Name:** `metdatapy`
- **Repository URL:** `https://github.com/kkartas/MetDataPy`
- **Repository type:** Git
- **Default branch:** `main` (or `master`)
- **Default version:** `latest`

#### Advanced Settings
- **Documentation type:** MkDocs (auto-detected from `.readthedocs.yml`)
- **Python interpreter:** CPython 3.11 (specified in `.readthedocs.yml`)
- **Install Project:** Yes (to enable API documentation)
- **Requirements file:** `docs/requirements.txt` (specified in `.readthedocs.yml`)

#### Build Settings
- **Build on commit:** Enabled (builds on every push to main/master)
- **Build pull requests:** Enabled (preview docs for PRs)
- **Privacy level:** Public

### 4. Activate Versions

1. Go to "Versions" in your project settings
2. Activate the versions you want to build:
   - `latest` (tracks main/master branch)
   - `stable` (tracks latest release tag)
   - Individual version tags (e.g., `v0.1.0`, `v0.2.0`)

### 5. Set Default Version

1. Go to "Admin" → "Advanced Settings"
2. Set **Default version** to `latest` or `stable`
3. Save changes

## Automatic Builds

Read the Docs will automatically build your documentation when:
- You push commits to the main/master branch
- You create a new release tag
- Someone opens a pull request (if enabled)

## Build Process

When Read the Docs builds your documentation:

1. **Clone Repository:** Fetches the latest code from GitHub
2. **Setup Environment:** Creates a Python 3.11 virtual environment
3. **Install Package:** Runs `pip install -e .` to install MetDataPy
4. **Install Dependencies:** Installs packages from `docs/requirements.txt`
5. **Build Docs:** Runs `mkdocs build` using the configuration in `mkdocs.yml`
6. **Deploy:** Publishes the built site to `https://metdatapy.readthedocs.io/`

## Viewing Documentation

After successful build:
- **Latest version:** https://metdatapy.readthedocs.io/en/latest/
- **Stable version:** https://metdatapy.readthedocs.io/en/stable/
- **Specific version:** https://metdatapy.readthedocs.io/en/v0.1.0/

## Local Documentation Build

To build and preview documentation locally:

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Serve documentation locally (with live reload)
mkdocs serve

# Open http://localhost:8000 in your browser

# Build static site
mkdocs build

# Output will be in site/ directory
```

## Troubleshooting

### Build Fails

1. **Check Build Log:** Go to "Builds" in your Read the Docs project
2. **Common Issues:**
   - Missing dependencies: Add to `docs/requirements.txt`
   - Import errors: Ensure package installs correctly with `pip install -e .`
   - MkDocs errors: Test locally with `mkdocs build --strict`
   - Configuration errors: Validate `.readthedocs.yml` syntax

### Documentation Not Updating

1. **Check Build Status:** Verify the build succeeded in Read the Docs dashboard
2. **Clear Cache:** Go to "Admin" → "Advanced Settings" → "Wipe" to clear build cache
3. **Rebuild:** Manually trigger a rebuild from the "Builds" page

### API Documentation Missing

If `mkdocstrings` can't find your modules:
1. Ensure package is installed: Check `.readthedocs.yml` has `pip install -e .`
2. Check import paths in markdown files
3. Verify `__init__.py` files exist in all package directories

### Theme Not Loading

1. Ensure `mkdocs-material` is in `docs/requirements.txt`
2. Check `mkdocs.yml` has `theme: name: material`
3. Clear browser cache

## Badges

Add Read the Docs badge to your README:

```markdown
[![Documentation Status](https://readthedocs.org/projects/metdatapy/badge/?version=latest)](https://metdatapy.readthedocs.io/en/latest/?badge=latest)
```

## Webhooks

Read the Docs automatically sets up a webhook in your GitHub repository. This webhook triggers builds when you push commits. You can view/manage webhooks in:
- GitHub: Settings → Webhooks
- Read the Docs: Admin → Integrations

## Custom Domain (Optional)

To use a custom domain (e.g., `docs.metdatapy.org`):

1. Go to "Admin" → "Domains"
2. Add your custom domain
3. Configure DNS records as instructed
4. Enable HTTPS (automatic with Let's Encrypt)

## Versioning Strategy

Read the Docs supports multiple documentation versions:

- **latest:** Always tracks the main/master branch (development docs)
- **stable:** Points to the latest release tag (production docs)
- **Version tags:** Each release (v0.1.0, v0.2.0, etc.) gets its own docs

To create a new version:
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

Read the Docs will automatically build documentation for the new tag.

## Best Practices

1. **Test Locally:** Always run `mkdocs build --strict` before pushing
2. **Use Docstrings:** Write comprehensive docstrings for API documentation
3. **Keep Updated:** Update docs with every feature addition
4. **Version Docs:** Document version-specific features clearly
5. **Link Checking:** Use `linkchecker` to find broken links
6. **Examples:** Include code examples in documentation
7. **Search:** Material theme includes built-in search

## Integration with CI

The GitHub Actions CI workflow (`.github/workflows/ci.yml`) includes a docs job that:
- Builds documentation with `mkdocs build --strict`
- Checks for broken links
- Ensures documentation builds successfully before merging PRs

This provides early feedback on documentation issues.

## Support

- **Read the Docs Documentation:** https://docs.readthedocs.io/
- **MkDocs Documentation:** https://www.mkdocs.org/
- **Material Theme:** https://squidfunk.github.io/mkdocs-material/
- **Read the Docs Support:** https://readthedocs.org/support/

## Summary

MetDataPy uses a modern documentation stack:
- **Hosting:** Read the Docs (free for open source)
- **Generator:** MkDocs (fast, Python-friendly)
- **Theme:** Material (beautiful, feature-rich)
- **API Docs:** mkdocstrings (automatic from docstrings)
- **CI Integration:** Automated builds and checks

This setup provides professional, versioned documentation with minimal maintenance.

