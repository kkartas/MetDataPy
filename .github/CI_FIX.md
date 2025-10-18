# CI Build Fix - Package Configuration

## Issue

The CI build was failing with two errors:

### 1. Deprecated License Format
```
SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated
```

**Cause:** Using `license = { file = "LICENSE" }` format which is deprecated in setuptools>=77.0.0

**Fix:** Changed to `license = { text = "MIT" }` format

### 2. Multiple Top-Level Packages
```
error: Multiple top-level packages discovered in a flat-layout: ['data', 'metdatapy'].
```

**Cause:** Both `data/` and `metdatapy/` directories were being discovered as packages by setuptools' automatic discovery

**Fix:** Explicitly specified packages in `pyproject.toml`:
```toml
[tool.setuptools]
packages = ["metdatapy"]
```

## Changes Made

### `pyproject.toml`

1. **Updated license format:**
   ```toml
   # Before
   license = { file = "LICENSE" }
   
   # After
   license = { text = "MIT" }
   ```

2. **Added explicit package configuration:**
   ```toml
   [tool.setuptools]
   packages = ["metdatapy"]
   
   [tool.setuptools.package-data]
   metdatapy = ["py.typed"]
   ```

### `MANIFEST.in`

Updated to explicitly exclude `data/` and `examples/` directories from the package distribution:

```
# Exclude data directory from package (used for examples only)
prune data
prune examples
```

## Verification

### Local Testing
```bash
# Install in editable mode
pip install -e .
# ✅ Success

# Run tests
python -m pytest -v
# ✅ 13 passed, 1 warning
```

### CI Testing
The changes should now allow the CI to:
- ✅ Install the package successfully
- ✅ Run tests across all platforms (Linux, macOS, Windows)
- ✅ Build documentation
- ✅ Create distribution packages

## Related Files

- `pyproject.toml` - Package configuration
- `MANIFEST.in` - Distribution manifest
- `.github/workflows/ci.yml` - CI workflow

## References

- [PEP 639 - License field standardization](https://peps.python.org/pep-0639/)
- [Setuptools package discovery](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html)
- [Setuptools deprecation timeline](https://setuptools.pypa.io/en/latest/deprecated/index.html)

