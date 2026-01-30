# Release Guide for PyObfuscator

This guide explains how to build and publish the pyobfuscator package to PyPI.

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

### Option 1: Using the publish.py script (Recommended)

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
- `pyobfuscator-{version}-py3-none-any.whl` - Wheel distribution
- `pyobfuscator-{version}.tar.gz` - Source distribution

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
pip install --index-url https://test.pypi.org/simple/ pyobfuscator

# Test it works
pyobfuscator --version
python -c "import pyobfuscator; print(pyobfuscator.__version__)"
```

After uploading to PyPI:
```powershell
# Install from PyPI
pip install pyobfuscator

# Test it works
pyobfuscator --version
```

## Version Management

Update version in `pyproject.toml`:
```toml
[project]
name = "pyobfuscator"
version = "1.0.1"  # Update this
```

## Checklist Before Release

- [ ] All tests pass: `pytest`
- [ ] Version updated in `pyproject.toml`
- [ ] CHANGELOG updated (if you have one)
- [ ] README is up to date
- [ ] All changes committed to git
- [ ] Create a git tag: `git tag v1.0.0`
- [ ] Build succeeds: `python -m build`
- [ ] Package check passes: `python -m twine check dist/*`
- [ ] Test on TestPyPI first
- [ ] Push to PyPI
- [ ] Push git tag: `git push origin v1.0.0`

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

For issues, visit: https://github.com/esgaltur/pyobfuscator/issues
