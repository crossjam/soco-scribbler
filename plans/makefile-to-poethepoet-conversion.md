# Makefile to PoeThePoet Conversion Plan

**Timestamp:** 2025-12-14T23:25:26.793Z  
**Issue:** Rewrite makefile into poethepoet tasks  
**Repository:** crossjam/soco-scribbler

## Overview

This plan outlines the conversion of existing Makefile tasks to PoeThePoet (poe) tasks. PoeThePoet is a task runner for Python projects that integrates seamlessly with pyproject.toml and provides a more modern, cross-platform alternative to Make.

## Analysis of Current Makefile

The existing Makefile contains the following categories of tasks:

### 1. Environment Setup Tasks
- `setup` - Create uv virtual environment
- `install` - Install project dependencies
- `install-dev` - Install development dependencies

### 2. Code Quality Tasks
- `check-types` - Run mypy type checker
- `check-ruff` - Run ruff linter
- `check-all` - Run all checks (types + ruff)

### 3. Utility Tasks
- `clean` - Remove cache directories and build artifacts
- `run` - Run the Sonos Last.fm scrobbler
- `versions` - Show available Python versions
- `version` - Show current Python version
- `help` - Display help message

### 4. Release Management Tasks
- `update-version` - Update version in pyproject.toml and __init__.py
- `build-package` - Build Python package (wheel and sdist)
- `publish-package` - Publish package to PyPI
- `verify-package` - Verify package installation
- `release` - Full release process (orchestrates multiple tasks)

## Conversion Strategy

### Dependencies Required
- Add `poethepoet` as a development dependency

### Configuration Location
- Add `[tool.poe.tasks]` section to `pyproject.toml`

### Task Mapping

| Makefile Task | PoeThePoet Task | Notes |
|--------------|----------------|-------|
| `setup` | `setup` | Create uv venv |
| `install` | `install` | Install dependencies |
| `install-dev` | `install-dev` | Install dev dependencies |
| `check-types` | `check-types` | Run mypy |
| `check-ruff` | `check-ruff` | Run ruff |
| `check-all` | `check-all` | Sequence task |
| `clean` | `clean` | Remove artifacts |
| `run` | `run` | Run scrobbler |
| `versions` | `versions` | Show Python versions |
| `version` | `version` | Show current version |
| `help` | (built-in) | Poe provides this automatically |
| `update-version` | `update-version` | Update version numbers |
| `build-package` | `build-package` | Build distributions |
| `publish-package` | `publish-package` | Publish to PyPI |
| `verify-package` | `verify-package` | Verify installation |
| `release` | `release` | Sequence task |

### Environment Variables
- The Makefile includes .env file support
- PoeThePoet can handle environment variables via `envfile` or `env` settings
- Consider using dotenv support: `envfile = ".env"`

## Implementation Checklist

- [x] Create plans subdirectory
- [x] Generate this conversion plan document
- [ ] Add PoeThePoet as a development dependency in pyproject.toml
- [ ] Create `[tool.poe.tasks]` section in pyproject.toml
- [ ] Convert environment setup tasks (setup, install, install-dev)
- [ ] Convert code quality tasks (check-types, check-ruff, check-all)
- [ ] Convert utility tasks (clean, run, versions, version)
- [ ] Convert release management tasks (update-version, build-package, publish-package, verify-package, release)
- [ ] Add environment variable support (.env file loading)
- [ ] Test all converted tasks to ensure they work as expected
- [ ] Update README.md to document poe commands
- [ ] Verify the Makefile can be deprecated (all functionality preserved)
- [ ] Run final checks and validation

## Testing Strategy

For each converted task, we will:
1. Run the poe task and verify it produces expected output
2. Compare behavior with original Makefile task
3. Ensure all arguments and options are properly handled
4. Test sequence tasks to ensure proper execution order

## Key Considerations

1. **Cross-platform compatibility**: PoeThePoet works on Windows, macOS, and Linux
2. **Shell commands**: Use `shell` task type for commands that need shell interpretation
3. **Sequence tasks**: Use `sequence` for tasks that run multiple commands
4. **Environment variables**: Handle .env file loading appropriately
5. **Error handling**: Ensure tasks fail appropriately when errors occur
6. **Interactive tasks**: The `release` task is interactive; handle with `shell` task
7. **Python version**: Tasks reference Python 3.11+ and 3.12

## Benefits of This Conversion

1. **Better integration**: Native Python tooling, defined in pyproject.toml
2. **Cross-platform**: No need for Make on Windows
3. **Type safety**: Better argument handling and validation
4. **Auto-completion**: Shell completion support
5. **Documentation**: Built-in help system
6. **Modern**: Aligned with modern Python project standards

## Post-Conversion

After successful conversion and testing:
- Consider adding deprecation notice to Makefile
- Update CI/CD pipelines if they reference make commands
- Ensure documentation reflects new task runner
