"""CLI entrypoint for the local Soco Scribbler logger."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import rich
import typer

from .cli import app
from .config import (
    CONFIG_DIR,
    DATA_DIR,
    DEFAULT_LOG_FILE,
    LOG_DIR,
    ensure_user_dirs,
)
from .sonos_lastfm import SonosScrobbler
from .utils import custom_print


class LogFormat(str, Enum):
    """Available output formats for the local logger."""

    JSONL = "jsonl"
    TEXT = "text"


PLACEHOLDER_CREDENTIALS: dict[str, str] = {
    "LASTFM_USERNAME": "__soco_scribbler__",
    "LASTFM_PASSWORD": "__soco_scribbler__",
    "LASTFM_API_KEY": "__soco_scribbler__",
    "LASTFM_API_SECRET": "__soco_scribbler__",
}


class SocoScribbler(SonosScrobbler):
    """Sonos scrobbler that logs plays locally instead of calling Last.fm."""

    def __init__(self, log_file: Path, log_format: LogFormat, emit_stdout: bool) -> None:
        self.log_file = log_file
        self.log_format = log_format
        self.emit_stdout = emit_stdout
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Seed placeholder values so that the Last.fm-focused base class initialises.
        for env_key, placeholder in PLACEHOLDER_CREDENTIALS.items():
            os.environ.setdefault(env_key, placeholder)

        super().__init__()
        self.network = None  # Never talk to Last.fm in logging mode

    def _prepare_entry(
        self,
        track_info: dict[str, Any],
        timestamp: datetime,
    ) -> tuple[dict[str, Any], str]:
        duration = track_info.get("duration") or 0
        position = track_info.get("position") or 0
        threshold_seconds = int(duration * self.scrobble_threshold_percent / 100)

        entry: dict[str, Any] = {
            "timestamp": timestamp.isoformat(),
            "artist": track_info.get("artist"),
            "title": track_info.get("title"),
            "album": track_info.get("album"),
            "duration": duration,
            "position": position,
            "state": track_info.get("state"),
            "threshold_percent": self.scrobble_threshold_percent,
            "threshold_seconds": threshold_seconds,
            "speaker": track_info.get("speaker"),
            "speaker_id": track_info.get("speaker_id"),
        }

        artist = entry.get("artist") or "<unknown artist>"
        title = entry.get("title") or "<unknown title>"
        speaker = entry.get("speaker")
        location = f" [{speaker}]" if speaker else ""
        text_line = (
            f"{entry['timestamp']} | {artist} - {title}{location} "
            f"({position}/{duration}s, threshold at {threshold_seconds}s)"
        )

        return entry, text_line

    def _write_entry(self, entry: dict[str, Any], text_line: str) -> None:
        try:
            with self.log_file.open("a", encoding="utf-8") as handle:
                if self.log_format is LogFormat.JSONL:
                    handle.write(json.dumps(entry, ensure_ascii=False))
                else:
                    handle.write(text_line)
                handle.write("\n")
        except Exception:
            custom_print(f"Failed to write log entry to {self.log_file}", "ERROR")
        else:
            if self.emit_stdout:
                artist = entry.get("artist") or "<unknown artist>"
                title = entry.get("title") or "<unknown title>"
                custom_print(f"Logged: {artist} - {title}", "INFO")

    def scrobble_track(self, track_info: dict[str, Any]) -> None:  # noqa: D401
        """Log track information locally instead of sending it to Last.fm."""
        if not track_info.get("artist") or not track_info.get("title"):
            return

        timestamp = datetime.now(UTC)
        entry, text_line = self._prepare_entry(track_info, timestamp)
        self._write_entry(entry, text_line)

        track_id = f"{track_info['artist']}-{track_info['title']}"
        self.last_scrobbled[track_id] = timestamp.isoformat()
        self.save_json(self.last_scrobbled_file, self.last_scrobbled)


@app.command(name="init")
def init_directories() -> None:
    """Ensure Soco Scribbler user directories exist and report their locations."""
    created = ensure_user_dirs()
    rich.print("[bold]Soco Scribbler user directories[/bold]")
    for label, key, path in [
        ("Config", "config", CONFIG_DIR),
        ("Data", "data", DATA_DIR),
        ("Logs", "log", LOG_DIR),
    ]:
        status = "created" if created.get(key, False) else "exists"
        rich.print(f"  [cyan]{label}[/cyan]: {path} ({status})")

    rich.print(
        "\n[green]✓[/green] Directories are ready. "
        "Credentials, cached data, and logs will live in these locations."
    )


@app.command(name="scribble")
def scribble(  # noqa: D401
    log_file: Optional[Path] = typer.Option(
        None,
        "--log-file",
        "-f",
        help=f"Path to append scrobble logs (default: {DEFAULT_LOG_FILE})",
    ),
    log_format: LogFormat = typer.Option(
        LogFormat.JSONL,
        "--log-format",
        "-F",
        case_sensitive=False,
        help="Logging format: jsonl or text.",
    ),
    stdout: bool = typer.Option(
        True,
        "--stdout/--no-stdout",
        help="Print log entries to stdout as they are recorded.",
    ),
    scrobble_interval: int = typer.Option(
        1,
        "--interval",
        "-i",
        help="Polling interval in seconds while monitoring speakers.",
        envvar="SCROBBLE_INTERVAL",
    ),
    rediscovery_interval: int = typer.Option(
        10,
        "--rediscovery",
        "-r",
        help="Rediscover speakers every N seconds.",
        envvar="SPEAKER_REDISCOVERY_INTERVAL",
    ),
    threshold: float = typer.Option(
        25.0,
        "--threshold",
        "-t",
        min=0,
        max=100,
        help="Percentage of the track that must play before it is logged.",
        envvar="SCROBBLE_THRESHOLD_PERCENT",
    ),
) -> None:
    """Monitor Sonos speakers and log scrobbles locally."""
    resolved_log_file = (log_file or DEFAULT_LOG_FILE).expanduser()
    resolved_log_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the base class picks up the runtime settings.
    os.environ["SCROBBLE_INTERVAL"] = str(scrobble_interval)
    os.environ["SPEAKER_REDISCOVERY_INTERVAL"] = str(rediscovery_interval)
    os.environ["SCROBBLE_THRESHOLD_PERCENT"] = str(threshold)

    rich.print(
        f"[green]Soco Scribbler started.[/green] "
        f"Logging scrobbles to [cyan]{resolved_log_file}[/cyan] "
        f"({log_format.value} format)."
    )

    scribbler = SocoScribbler(
        log_file=resolved_log_file,
        log_format=log_format,
        emit_stdout=stdout,
    )
    scribbler.run()


def main() -> None:
    """Entry point for soco-scribbler CLI."""
    app()


if __name__ == "__main__":
    main()
