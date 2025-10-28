# Release Checklist for flowslice

## Pre-Release

### Code Quality
- [x] All tests passing (94 tests, 68% coverage)
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] No critical TODOs in code

### Version Management
- [x] Update version in `pyproject.toml` to 1.0.0
- [x] Update version in `src/flowslice/__init__.py` to 1.0.0
- [x] Update `CHANGELOG.md` with release notes
- [x] Ensure all changes are committed

### Documentation
- [x] README.md is up to date with features
- [x] Examples in README work correctly
- [x] CHANGELOG.md includes all notable changes
- [ ] API documentation is accurate

### PyPI Setup
- [x] `pyproject.toml` has correct metadata
- [x] `pyproject.toml` has correct author/maintainer info
- [x] Keywords and classifiers are appropriate
- [x] Project URLs are correct
- [x] GitHub Actions workflow for publishing exists

## Release Process

### 1. Final Testing
```bash
# Run full test suite
pytest tests/ -v

# Test CLI locally
flowslice examples/example.py:10:result backward tree
flowslice examples/cross_file_example.py:15:output forward json

# Build package locally to verify
python -m build
```

### 2. Create Git Tag
```bash
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag to GitHub
git push origin v1.0.0
```

### 3. Create GitHub Release
1. Go to https://github.com/pranlawate/flowslice/releases/new
2. Select tag: `v1.0.0`
3. Release title: `flowslice v1.0.0`
4. Copy content from CHANGELOG.md for v1.0.0
5. Click "Publish release"

### 4. PyPI Publishing

**Option A: Automatic (Recommended)**
- GitHub Actions will automatically publish when you create a GitHub release
- Monitor: https://github.com/pranlawate/flowslice/actions

**Option B: Manual**
```bash
# Build the package
python -m build

# Upload to TestPyPI first (optional)
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ flowslice

# Upload to PyPI
python -m twine upload dist/*
```

### 5. Verify Publication
```bash
# Install from PyPI
pip install flowslice

# Verify version
python -c "import flowslice; print(flowslice.__version__)"

# Test basic functionality
flowslice --version
flowslice --help
```

## Post-Release

### Announcement
- [ ] Update GitHub repository description
- [ ] Share on relevant forums/communities
- [ ] Update personal/organizational website

### Monitoring
- [ ] Monitor PyPI download stats
- [ ] Watch for issues on GitHub
- [ ] Respond to community feedback

## Next Release Planning

### v1.1.0 (Planned Features)
- Match/case statement support (Python 3.10+)
- F-string expression tracking
- Additional output formatters
- Performance improvements

### v2.0.0 (Future Features)
- Control flow tracking (if/else/loops)
- Class inheritance analysis
- Decorator tracking
- Type-based filtering

## Notes

### PyPI Trusted Publishing Setup
1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher:
   - PyPI Project Name: `flowslice`
   - Owner: `pranlawate`
   - Repository name: `flowslice`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

### TestPyPI Setup (Optional)
1. Go to https://test.pypi.org/manage/account/publishing/
2. Follow same steps as PyPI
3. Use environment name: `testpypi`

### Version Numbering
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backward compatible
- **PATCH**: Bug fixes, backward compatible

Current: `1.0.0` (first stable release)
