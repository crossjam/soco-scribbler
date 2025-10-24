- [x] Rework the `scribble` CLI options in `src/soco_scribbler/soco_scribbler.py:18` to remove Last.fm credential flow, keep interval settings, and add logging parameters.
- [x] Convert `SocoScribbler` into a subclass of `SonosScrobbler` that sets placeholder Last.fm env vars, disables the Last.fm network, and accepts logging configuration.
- [x] Implement helpers to ensure log storage, format timestamped entries, append to file/console, and override `scrobble_track` to log locally while updating history.
- [x] Update the command body to use the new options, set interval env vars, drop credential/setup handling, and keep the monitoring loop via `run()`.
- [x] Validate the new CLI surface with `uv run python -m soco_scribbler.soco_scribbler --help` and manually confirm logging output without Last.fm submission.
- [x] Introduce `platformdirs` to resolve per-user config/data directories in an OS-aware way and refactor existing hardcoded paths.
- [x] Update documentation/help text to describe the new config directory behavior powered by `platformdirs`.

**Logging Update**
- Local logger now subclasses the Last.fm scrobbler, seeds placeholder credentials, and writes JSONL/text entries while preserving duplicate tracking.
- `scribble` CLI exposes log destination/format/console toggles while still wiring the Sonos polling controls and defaulting to the per-user log file.
- Added a new `init` subcommand to materialize and report platform-specific config/data/log directories on demand.
- Platform-aware directories replace hardcoded paths for config/data/log storage and the CLI consumes the shared constants.
- Speaker metadata now rides along with each scrobble so the logger can annotate entries with player names and IDs.
- Documentation and task tracking were refreshed to match the new behaviour, and the new dependency is declared.
- `uv run` validation of the CLI help output succeeds when pointing `HOME` to a writable sandbox directory.
