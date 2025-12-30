# Repository Guidelines

## Project Structure & Module Organization
The application code lives in `src/soco_scribbler/`. `cli.py` defines
the Typer CLI entrypoints, `soco_scribbler.py` coordinates Sonos
polling, logging, and destinations, and `sonos_lastfm.py` wraps the
Last.fm client. Shared helpers sit in `config.py` and `utils.py`,
while release metadata belongs in `pyproject.toml`. Update `SOCO_SCRIBBLER_LOGGER.md` whenever logger
behaviour or outputs change.

## Build, Test, and Development Commands
Install dependencies with `uv pip install -e ".[dev]"` which includes
all development tools (poethepoet, ty, ruff, pytest, build). Run
`soco-scribbler scribble --stdout` to exercise the local logger, or
`uv run -m sonos_lastfm test` to test Last.fm connectivity. Keep
`poe check-all` green before pushing (runs ty type checker and ruff linter).
Use `poe clean` before rebuilding distributions.

## Coding Style & Naming Conventions
Target Python 3.11+, 4-space indentation, and 88-character lines. CLI
command names stay kebab-case, module and function names snake_case,
and classes PascalCase. Document new behaviour with Google-style
docstrings and prefer explicit type hints so ty and ruff
succeed. Reuse platformdirs helpers when touching the filesystem.

## Testing Guidelines
Static checks are the minimum gate: run `poe check-all` (or `poe qa` for
comprehensive checks including formatting) plus relevant CLI smoke tests
(`uv run -m sonos_lastfm test`, `soco-scribbler scribble --no-stdout`)
before PRs. If you add automated tests, place them under `tests/` with
descriptive names (`test_logger.py`) and keep fixtures local; pytest is
already included in dev dependencies.

## Commit & Pull Request Guidelines
Write imperative, ≤72 character commit summaries (e.g., `Add Kafka
logger exporter`) and scope each change set narrowly. Reference issues
with `Refs #123` in the body. PRs should describe what changed, why,
and how it was verified, and must include any doc updates plus proof
that `poe check-all` passed.

## Security & Configuration Tips
Never commit `.env`, `.op_env`, or log artefacts. Use `soco-scribbler
init` to create platform-specific directories and prefer the system
keyring to store secrets. Extend `config.py` validation when adding
new credentials and mirror the changes in the README or logger memo.
