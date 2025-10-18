# Read the Docs Setup - Changes Summary

This document summarizes all changes made to set up Read the Docs for MetDataPy documentation.

## Overview

MetDataPy documentation is now configured to be hosted on Read the Docs instead of GitHub Pages. This provides better versioning, automatic builds, and a more professional documentation experience.

## Files Created

### 1. `.readthedocs.yml`
**Purpose:** Read the Docs build configuration file

**Key Settings:**
- Build OS: Ubuntu 22.04
- Python version: 3.11
- Documentation tool: MkDocs
- Package installation: `pip install -e .`
- Requirements: `docs/requirements.txt`

### 2. `docs/requirements.txt`
**Purpose:** Documentation build dependencies

**Dependencies:**
- `mkdocs>=1.5.0` - Static site generator
- `mkdocs-material>=9.0.0` - Material theme
- `mkdocstrings[python]>=0.24.0` - API documentation from docstrings
- `pymdown-extensions>=10.0` - Markdown extensions

### 3. `.github/READTHEDOCS_SETUP.md`
**Purpose:** Comprehensive setup guide for Read the Docs

**Contents:**
- Initial setup instructions
- Configuration details
- Automatic build process
- Local development guide
- Troubleshooting tips
- Best practices
- Integration with CI

### 4. `.github/READTHEDOCS_MIGRATION.md`
**Purpose:** Migration documentation from GitHub Pages to Read the Docs

**Contents:**
- What changed and why
- Advantages of Read the Docs
- How automatic builds work
- Next steps for setup
- Configuration reference
- Troubleshooting guide

## Files Modified

### 1. `mkdocs.yml`
**Changes:**
- Updated `site_url` to `https://metdatapy.readthedocs.io/`
- Updated `repo_url` to `https://github.com/kkartas/MetDataPy`
- Added `repo_name: kkartas/MetDataPy`
- Added `edit_uri: edit/main/docs/`
- **Theme upgrade:** Changed from basic `mkdocs` to `material` theme with:
  - Light/dark mode toggle
  - Navigation tabs, sections, and top navigation
  - Search suggestions and highlighting
  - Code copy buttons and annotations
- **Added markdown extensions:**
  - `pymdownx.highlight` - Syntax highlighting with line numbers
  - `pymdownx.inlinehilite` - Inline code highlighting
  - `pymdownx.snippets` - Include external files
  - `pymdownx.superfences` - Advanced fenced code blocks
  - `pymdownx.details` - Collapsible details/summary
  - `pymdownx.tabbed` - Tabbed content
  - `pymdownx.arithmatex` - Math rendering (LaTeX)
  - `attr_list` - Add attributes to elements
  - `md_in_html` - Markdown in HTML blocks
- **Added plugins:**
  - `search` - Built-in search
  - `mkdocstrings` - API documentation with NumPy docstring style
- **Added MathJax:** For rendering mathematical formulas

### 2. `README.md`
**Changes:**
- **Badge:** Changed from GitHub Actions docs badge to Read the Docs badge:
  ```markdown
  [![Documentation Status](https://readthedocs.org/projects/metdatapy/badge/?version=latest)](https://metdatapy.readthedocs.io/en/latest/?badge=latest)
  ```
- **Documentation section:** Updated with:
  - Link to Read the Docs: https://metdatapy.readthedocs.io/
  - Local build instructions using `docs/requirements.txt`
  - Simplified commands

### 3. `.github/workflows/ci.yml`
**Changes:**
- **Docs job:** Updated to use `docs/requirements.txt`:
  ```yaml
  - name: Install dependencies
    run: |
      python -m pip install --upgrade pip
      pip install -e .
      pip install -r docs/requirements.txt
  ```
- Kept docs build check in CI (Read the Docs handles deployment)

### 4. `.github/CI_SETUP.md`
**Changes:**
- **Overview:** Added note about Read the Docs integration
- **Docs job description:** Updated to mention Read the Docs deployment
- **Removed GitHub Pages section**
- **Added Read the Docs section** with:
  - Configuration files reference
  - Setup instructions link
  - Documentation URLs

### 5. `TO-DO.md`
**Changes:**
- Added "Read the Docs setup with automatic builds" as completed ✅
- Changed "Build docs warning-free in CI; publish to Pages" to "deploy to Read the Docs" ✅

## Files Removed

### 1. `.github/workflows/docs.yml`
**Reason:** No longer needed; Read the Docs handles documentation deployment automatically

## Testing

### Local Build Test
```bash
pip install -r docs/requirements.txt
python -m mkdocs build --strict
```

**Result:** ✅ Documentation builds successfully without errors

### CI Integration
- Docs job in `.github/workflows/ci.yml` still builds documentation
- Catches documentation errors before merge
- Provides early feedback on PRs

## Next Steps for User

### 1. Set Up Read the Docs Account
1. Go to https://readthedocs.org/
2. Sign in with GitHub account
3. Authorize Read the Docs to access repositories

### 2. Import Project
1. Click "Import a Project"
2. Find `MetDataPy` in repository list
3. Click "+" to import

### 3. Configure Project
- **Name:** `metdatapy`
- **Repository:** `https://github.com/kkartas/MetDataPy`
- **Default branch:** `main`
- **Default version:** `latest`

### 4. Activate Versions
- Activate `latest` (tracks main branch)
- Activate `stable` (tracks latest release)
- Set default version

### 5. Test First Build
- Push a commit to trigger build
- Check Read the Docs dashboard
- Verify documentation at https://metdatapy.readthedocs.io/en/latest/

### 6. Create First Release
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

## Documentation URLs

After setup:
- **Latest:** https://metdatapy.readthedocs.io/en/latest/
- **Stable:** https://metdatapy.readthedocs.io/en/stable/
- **Specific version:** https://metdatapy.readthedocs.io/en/v0.1.0/
- **Dashboard:** https://readthedocs.org/projects/metdatapy/

## Benefits

### For Development
- ✅ Automatic builds on every commit
- ✅ Pull request previews
- ✅ Version-specific documentation
- ✅ No GitHub Actions minutes used

### For Users
- ✅ Professional documentation site
- ✅ Easy version switching
- ✅ Better search functionality
- ✅ Mobile-friendly design
- ✅ Downloadable PDF/ePub

### For JOSS Submission
- ✅ Standard for Python scientific software
- ✅ Shows project maturity
- ✅ Easy for reviewers to access
- ✅ Versioned documentation
- ✅ Professional appearance

## Configuration Summary

### Read the Docs Build Process
1. Webhook triggers on GitHub push
2. Clone repository
3. Create Python 3.11 environment
4. Install package: `pip install -e .`
5. Install docs dependencies: `pip install -r docs/requirements.txt`
6. Build docs: `mkdocs build`
7. Deploy to CDN

### Local Development
```bash
# Install dependencies
pip install -r docs/requirements.txt

# Serve with live reload
python -m mkdocs serve

# Build static site
python -m mkdocs build --strict
```

### CI Integration
- CI builds docs to catch errors
- Read the Docs handles deployment
- Best of both worlds

## Key Features Enabled

### Material Theme
- Modern, responsive design
- Light/dark mode
- Better navigation
- Code copy buttons
- Search suggestions

### MathJax Support
- Render LaTeX formulas
- Important for scientific documentation
- Used in derived metrics docs

### API Documentation
- `mkdocstrings` plugin
- Automatic from NumPy docstrings
- Links between documentation and code

### Markdown Extensions
- Syntax highlighting
- Tabbed content
- Collapsible sections
- Admonitions
- Tables

## Maintenance

### Regular Tasks
- Keep `docs/requirements.txt` updated
- Monitor Read the Docs dashboard
- Update docs with code changes
- Test builds locally before pushing

### When Releasing
1. Update version in code
2. Update `CITATION.cff`
3. Create and push git tag
4. Read the Docs builds automatically
5. Activate new version in dashboard

## Troubleshooting

### Build Fails
1. Check Read the Docs build log
2. Test locally: `python -m mkdocs build --strict`
3. Verify dependencies
4. Check for import errors

### Documentation Not Updating
1. Check build status
2. Verify webhook is active
3. Manually trigger rebuild
4. Clear build cache

### Missing API Documentation
1. Ensure package installs correctly
2. Check `mkdocstrings` configuration
3. Verify NumPy-style docstrings
4. Check import paths

## Summary

All configuration files are in place and tested. The documentation builds successfully locally. The repository is ready for Read the Docs integration. The next step is to set up the Read the Docs account and import the repository following the instructions in `.github/READTHEDOCS_SETUP.md`.

## Files Changed Summary

**Created (4 files):**
- `.readthedocs.yml`
- `docs/requirements.txt`
- `.github/READTHEDOCS_SETUP.md`
- `.github/READTHEDOCS_MIGRATION.md`

**Modified (5 files):**
- `mkdocs.yml` (major upgrade to Material theme)
- `README.md` (badge and docs section)
- `.github/workflows/ci.yml` (use docs/requirements.txt)
- `.github/CI_SETUP.md` (Read the Docs section)
- `TO-DO.md` (mark as complete)

**Removed (1 file):**
- `.github/workflows/docs.yml` (no longer needed)

**Total changes:** 10 files

