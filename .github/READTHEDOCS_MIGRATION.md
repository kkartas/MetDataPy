# Read the Docs Migration Summary

This document summarizes the migration from GitHub Pages to Read the Docs for MetDataPy documentation hosting.

## What Changed

### Files Added

1. **`.readthedocs.yml`** - Read the Docs build configuration
   - Specifies build environment (Ubuntu 22.04, Python 3.11)
   - Configures MkDocs as documentation tool
   - Sets up Python package installation
   - References `docs/requirements.txt` for dependencies

2. **`docs/requirements.txt`** - Documentation dependencies
   - `mkdocs>=1.5.0` - Static site generator
   - `mkdocs-material>=9.0.0` - Material theme
   - `mkdocstrings[python]>=0.24.0` - API documentation
   - `pymdown-extensions>=10.0` - Markdown extensions

3. **`.github/READTHEDOCS_SETUP.md`** - Comprehensive setup guide
   - Step-by-step instructions for Read the Docs setup
   - Configuration details
   - Troubleshooting guide
   - Best practices

4. **`.github/READTHEDOCS_MIGRATION.md`** - This file

### Files Modified

1. **`mkdocs.yml`** - Enhanced MkDocs configuration
   - Updated `site_url` to `https://metdatapy.readthedocs.io/`
   - Updated `repo_url` and `repo_name` to correct GitHub repository
   - Changed theme from basic `mkdocs` to `material` with:
     - Light/dark mode toggle
     - Navigation tabs and sections
     - Search suggestions and highlighting
     - Code copy buttons
     - Code annotations
   - Added comprehensive markdown extensions:
     - Syntax highlighting with line numbers
     - Tabbed content support
     - Math rendering (MathJax)
     - Admonitions and details
   - Added `mkdocstrings` plugin for API documentation
   - Added MathJax for rendering mathematical formulas

2. **`README.md`** - Updated documentation links
   - Changed Documentation badge from GitHub Actions to Read the Docs
   - Updated documentation section with Read the Docs URL
   - Added local build instructions using `docs/requirements.txt`

3. **`.github/workflows/ci.yml`** - Updated CI workflow
   - Changed docs job to use `docs/requirements.txt` instead of inline dependencies
   - Kept docs build check in CI (Read the Docs handles deployment)

4. **`.github/CI_SETUP.md`** - Updated CI documentation
   - Replaced GitHub Pages section with Read the Docs section
   - Added references to Read the Docs configuration files
   - Updated documentation URLs

5. **`TO-DO.md`** - Updated checklist
   - Added "Read the Docs setup with automatic builds" as completed
   - Changed "Build docs warning-free in CI; publish to Pages" to "deploy to Read the Docs"

### Files Removed

1. **`.github/workflows/docs.yml`** - GitHub Pages deployment workflow
   - No longer needed; Read the Docs handles deployment automatically

## Why Read the Docs?

### Advantages over GitHub Pages

1. **Automatic Versioning**
   - Read the Docs automatically builds docs for each release tag
   - Maintains separate documentation for `latest`, `stable`, and version tags
   - Users can switch between versions in the UI

2. **Better Search**
   - Built-in search indexing
   - Search across all versions
   - Better search relevance

3. **Pull Request Previews**
   - Automatic documentation builds for PRs
   - Preview changes before merging
   - Catch documentation issues early

4. **No GitHub Actions Minutes**
   - Read the Docs provides free builds for open source
   - Doesn't consume GitHub Actions minutes
   - Faster builds with dedicated infrastructure

5. **Better Analytics**
   - Built-in traffic analytics
   - Popular pages tracking
   - Search query analytics

6. **Custom Domains**
   - Easy custom domain setup
   - Automatic HTTPS with Let's Encrypt
   - Better branding

7. **Download Formats**
   - Automatic PDF/ePub generation
   - Downloadable documentation
   - Offline reading support

8. **Standard for Python Projects**
   - Most Python projects use Read the Docs
   - Familiar to Python community
   - Better discoverability

## How It Works

### Automatic Builds

Read the Docs automatically builds documentation when:
1. **Push to main/master** - Updates `latest` version
2. **New release tag** - Creates new version (e.g., `v0.1.0`)
3. **Pull request** - Creates preview build (if enabled)

### Build Process

1. Read the Docs webhook receives GitHub event
2. Clones repository at specified commit/tag
3. Creates Python 3.11 virtual environment
4. Installs package with `pip install -e .`
5. Installs documentation dependencies from `docs/requirements.txt`
6. Runs `mkdocs build` using `mkdocs.yml` configuration
7. Deploys built site to Read the Docs CDN
8. Updates documentation at `https://metdatapy.readthedocs.io/`

### Local Development

Developers can still build and preview documentation locally:

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Serve with live reload
python -m mkdocs serve

# Build static site
python -m mkdocs build --strict
```

### CI Integration

The GitHub Actions CI workflow still builds documentation to catch errors:
- Runs `mkdocs build --strict` on every PR
- Checks for broken links
- Ensures documentation builds successfully
- Provides early feedback before Read the Docs build

## Next Steps

### 1. Set Up Read the Docs Account

1. Go to https://readthedocs.org/
2. Sign in with GitHub account
3. Import MetDataPy repository
4. Configure project settings

See `.github/READTHEDOCS_SETUP.md` for detailed instructions.

### 2. Enable Build on Push

Read the Docs will automatically set up a webhook in GitHub to trigger builds.

### 3. Configure Versions

1. Activate `latest` version (tracks main/master)
2. Activate `stable` version (tracks latest release)
3. Set default version to `latest` or `stable`

### 4. Test First Build

1. Push a commit to main/master
2. Check Read the Docs dashboard for build status
3. Verify documentation at https://metdatapy.readthedocs.io/en/latest/

### 5. Create First Release

```bash
# Tag a release
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# Read the Docs will automatically build v0.1.0 docs
```

### 6. Update Badges

The README already includes the Read the Docs badge:

```markdown
[![Documentation Status](https://readthedocs.org/projects/metdatapy/badge/?version=latest)](https://metdatapy.readthedocs.io/en/latest/?badge=latest)
```

## Documentation URLs

After setup:

- **Latest (development):** https://metdatapy.readthedocs.io/en/latest/
- **Stable (production):** https://metdatapy.readthedocs.io/en/stable/
- **Specific version:** https://metdatapy.readthedocs.io/en/v0.1.0/
- **Dashboard:** https://readthedocs.org/projects/metdatapy/

## Configuration Files Reference

### `.readthedocs.yml`

```yaml
version: 2
mkdocs:
  configuration: mkdocs.yml
  fail_on_warning: false
build:
  os: ubuntu-22.04
  tools:
    python: "3.11"
  jobs:
    post_install:
      - pip install -e .
python:
  install:
    - requirements: docs/requirements.txt
```

### `docs/requirements.txt`

```
mkdocs>=1.5.0
mkdocs-material>=9.0.0
mkdocstrings[python]>=0.24.0
pymdown-extensions>=10.0
```

### `mkdocs.yml` (key sections)

```yaml
site_url: https://metdatapy.readthedocs.io/
theme:
  name: material
  # ... theme configuration
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: numpy
```

## Troubleshooting

### Build Fails

1. Check Read the Docs build log
2. Test locally: `python -m mkdocs build --strict`
3. Verify all dependencies in `docs/requirements.txt`
4. Check for import errors in docstrings

### Documentation Not Updating

1. Check build status in Read the Docs dashboard
2. Verify webhook is active in GitHub settings
3. Manually trigger rebuild in Read the Docs
4. Clear build cache if needed

### Missing API Documentation

1. Ensure package installs correctly
2. Check `mkdocstrings` configuration in `mkdocs.yml`
3. Verify docstrings use NumPy style
4. Check import paths in documentation files

## Benefits for JOSS Submission

1. **Professional Documentation** - Read the Docs is standard for academic software
2. **Versioned Documentation** - Shows project maturity and maintenance
3. **Easy Access** - Reviewers can easily access documentation
4. **Automatic Updates** - Documentation stays in sync with code
5. **PDF Export** - Reviewers can download documentation
6. **Search Functionality** - Easy to find specific features
7. **Mobile Friendly** - Material theme is responsive

## Maintenance

### Regular Tasks

- **Update dependencies:** Keep `docs/requirements.txt` up to date
- **Check builds:** Monitor Read the Docs dashboard for build failures
- **Update docs:** Keep documentation in sync with code changes
- **Version docs:** Document version-specific features clearly

### When Releasing

1. Update version in `metdatapy/__init__.py`
2. Update `CITATION.cff` with new version
3. Create git tag: `git tag -a v0.x.0 -m "Release v0.x.0"`
4. Push tag: `git push origin v0.x.0`
5. Read the Docs automatically builds new version
6. Activate new version in Read the Docs dashboard

## Summary

The migration to Read the Docs provides:
- ✅ Professional documentation hosting
- ✅ Automatic versioning
- ✅ Better search and navigation
- ✅ Pull request previews
- ✅ No GitHub Actions minutes used
- ✅ Standard for Python/scientific projects
- ✅ Better for JOSS submission

All configuration files are in place and tested. The documentation builds successfully locally. The next step is to set up the Read the Docs account and import the repository.

