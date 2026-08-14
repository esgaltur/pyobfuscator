# Release Guide for Skjol

This guide explains how to publish a GitHub release from Skjol's current
version and how to publish the package to PyPI as a separate operation.

## GitHub release from the current version

The supported local entry point is `scripts\release.ps1`. It reads the version
from `pyobfuscator\_version.py`; the version is never entered separately on the
command line.

Prerequisites:

```powershell
python -m pip install build twine
gh auth login
```

The checkout must be clean and attached to a branch. Draft and public modes
also require local `HEAD` to match the same branch on GitHub and to use a
version whose `v<version>` tag does not already exist.

Start with the non-mutating commands:

```powershell
# Show the derived version, tag, and mode only
.\scripts\release.ps1 -PlanOnly

# Run all tests, build from committed HEAD, and validate both distributions
.\scripts\release.ps1
```

Create a draft release for review:

```powershell
.\scripts\release.ps1 -Mode Draft
```

Create a public GitHub release:

```powershell
.\scripts\release.ps1 -Mode Publish
```

`Draft` and `Publish` require typing the expected tag as confirmation. Use
`-Yes` only in deliberate automation. By default, the script waits for the
GitHub release workflow and returns a failure code if the workflow fails;
`-NoWait` returns after dispatch.

The script performs these steps:

1. derives `v<version>` from the single version source;
2. verifies the clean and synchronized Git checkout;
3. rejects an existing local/remote tag or GitHub release;
4. runs the complete test suite;
5. exports committed `HEAD` into an isolated temporary directory;
6. builds the wheel and source distribution;
7. validates both with Twine and prints SHA-256 hashes; and
8. dispatches `.github\workflows\release.yml` only for explicit draft or
   public modes.

Temporary source and build files are removed on success or failure. GitHub
publication and PyPI publication are intentionally separate: creating a GitHub
release does not dispatch the PyPI workflow.

## Prerequisites

1. **Install build tools** (already done):
   ```powershell
   pip install --upgrade pip build twine
   ```

2. **PyPI Account**:
   - Create an account at [https://pypi.org/account/register/](https://pypi.org/account/register/)
   - For testing: [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)

3. **API Token** (Recommended):
   - Go to [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
   - Create a new API token
   - Use `__token__` as username and the token as password

## Quick Release

### Option 1: Using the legacy PyPI script

```powershell
# Test on TestPyPI first
python publish.py --test

# Publish to PyPI
python publish.py
```

### Option 2: Manual steps

```powershell
# 1. Clean previous builds
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path *.egg-info) { Remove-Item -Recurse -Force *.egg-info }

# 2. Build the package
python -m build

# 3. Check the package
python -m twine check dist/*

# 4. Upload to TestPyPI (test first!)
python -m twine upload --repository testpypi dist/*

# 5. Upload to PyPI (production)
python -m twine upload dist/*
```

## Built Artifacts

After building, you'll find in the `dist/` folder:
- `skjol-{version}-py3-none-any.whl` - Wheel distribution
- `skjol-{version}.tar.gz` - Source distribution

## Configuration File (.pypirc)

Create `~/.pypirc` (Windows: `C:\Users\{Username}\.pypirc`) to store credentials:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_API_TOKEN_HERE
```

## Testing the Package

After uploading to TestPyPI:
```powershell
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ skjol

# Test it works
skjol --version
python -c "import skjol; print(skjol.__version__)"
```

After uploading to PyPI:
```powershell
# Install from PyPI
pip install skjol

# Test it works
skjol --version
```

## Version Management

Update the single version source in `pyobfuscator/_version.py`. The
`pyproject.toml` metadata reads it dynamically for both wheels and source
distributions.

## Checklist Before Release

- [ ] All tests pass: `pytest`
- [ ] Version updated in `pyobfuscator/_version.py`
- [ ] CHANGELOG updated (if you have one)
- [ ] README is up to date
- [ ] All changes committed to git
- [ ] Create a git tag: `git tag v2.0.0`
- [ ] Build succeeds: `python -m build`
- [ ] Package check passes: `python -m twine check dist/*`
- [ ] Test on TestPyPI first
- [ ] Push to PyPI
- [ ] Push git tag: `git push origin v2.0.0`

## Troubleshooting

### "File already exists" error
- You cannot re-upload the same version
- Increment the version number in `pyproject.toml`

### Authentication failed
- Make sure you're using the correct credentials
- Use API tokens instead of password
- Check `.pypirc` file format

### Package validation errors
- Run `python -m twine check dist/*` for details
- Check `README.md` formatting
- Ensure all metadata in `pyproject.toml` is valid

## GitHub Actions (Alternative)

The project also includes `.github/workflows/publish.yml` for automated releases via GitHub Actions.

To use it:
1. Create a release on GitHub
2. The action automatically builds and publishes to PyPI
3. Set `PYPI_API_TOKEN` in repository secrets

## Support

For issues, visit: https://github.com/esgaltur/skjol/issues
