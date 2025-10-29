# Repository Guidelines

## Project Structure & Module Organization
The application code lives in `src/soco_scribbler/`. `cli.py` defines the Typer CLI entrypoints, `soco_scribbler.py` coordinates Sonos polling, logging, and destinations, and `sonos_lastfm.py` wraps the Last.fm client. Shared helpers sit in `config.py` and `utils.py`, while release metadata belongs in `pyproject.toml` and the top-level `Makefile`. Update `SOCO_SCRIBBLER_LOGGER.md` whenever logger behaviour or outputs change.

## Build, Test, and Development Commands
Run `make setup` once to create the uv virtual environment, then `make install` or `make install-dev` for runtime or dev dependencies. `make run` boots the scrobbler via `uv run -m sonos_lastfm`, and `uv run -m soco_scribbler.soco_scribbler scribble --stdout` exercises the local logger. Keep `make check-types`, `make check-ruff`, or `make check-all` green before pushing. Use `make clean` before rebuilding distributions.

## Coding Style & Naming Conventions
Target Python 3.11+, 4-space indentation, and 88-character lines. CLI command names stay kebab-case, module and function names snake_case, and classes PascalCase. Document new behaviour with Google-style docstrings and prefer explicit type hints so mypy and ruff succeed. Reuse platformdirs helpers when touching the filesystem.

## Testing Guidelines
Static checks are the minimum gate: run `make check-all` plus relevant CLI smoke tests (`uv run -m sonos_lastfm test`, `soco-scribbler scribble --no-stdout`) before PRs. If you add automated tests, place them under `tests/` with descriptive names (`test_logger.py`) and keep fixtures local; install `pytest` in the uv environment only when needed.

## Commit & Pull Request Guidelines
Write imperative, ≤72 character commit summaries (e.g., `Add Kafka logger exporter`) and scope each change set narrowly. Reference issues with `Refs #123` in the body. PRs should describe what changed, why, and how it was verified, and must include any doc updates plus proof that `make check-all` passed.

## Security & Configuration Tips
Never commit `.env`, `.op_env`, or log artefacts. Use `soco-scribbler init` to create platform-specific directories and prefer the system keyring to store secrets. Extend `config.py` validation when adding new credentials and mirror the changes in the README or logger memo.
