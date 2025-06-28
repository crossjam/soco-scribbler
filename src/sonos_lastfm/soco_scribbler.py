import json

from typing import Any, Optional, Literal

import typer

from .sonos_lastfm import SonosScrobbler
from .cli import app


class SocoScribbler:

    def scrobble_track(self, track_info: dict[str, Any]) -> None:
        json.dump(track_info)


@app.command(name="scribble")
def scribble(
    username: Optional[str] = typer.Option(
        None,
        "--username",
        "-u",
        help="Last.fm username",
        envvar="LASTFM_USERNAME",
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        help="Last.fm password",
        envvar="LASTFM_PASSWORD",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Last.fm API key",
        envvar="LASTFM_API_KEY",
    ),
    api_secret: Optional[str] = typer.Option(
        None,
        "--api-secret",
        "-s",
        help="Last.fm API secret",
        envvar="LASTFM_API_SECRET",
    ),
    scrobble_interval: int = typer.Option(
        1,
        "--interval",
        "-i",
        help="Scrobbling check interval in seconds",
        envvar="SCROBBLE_INTERVAL",
    ),
    rediscovery_interval: int = typer.Option(
        10,
        "--rediscovery",
        "-r",
        help="Speaker rediscovery interval in seconds",
        envvar="SPEAKER_REDISCOVERY_INTERVAL",
    ),
    threshold: float = typer.Option(
        25.0,
        "--threshold",
        "-t",
        help="Scrobble threshold percentage",
        envvar="SCROBBLE_THRESHOLD_PERCENT",
        min=0,
        max=100,
    ),
    setup: bool = typer.Option(
        False,
        "--setup",
        help="Run interactive setup before starting",
    ),
) -> None:
    """Start the Sonos scrobbler (requires credentials).

    Monitors your Sonos speakers and scrobbles tracks to Last.fm. Can use stored
    credentials or accept them via command line options or environment variables.
    """
    if setup:
        interactive_setup()
        return

    # Get credentials from various sources
    final_username = get_stored_credential("username")
    final_password = get_stored_credential("password")
    final_api_key = get_stored_credential("api_key")
    final_api_secret = get_stored_credential("api_secret")

    # Check if we have all required credentials
    missing = []
    if not final_username:
        missing.append("username")
    if not final_password:
        missing.append("password")
    if not final_api_key:
        missing.append("API key")
    if not final_api_secret:
        missing.append("API secret")

    if missing:
        rich.print(
            f"\n[red]Error:[/red] Missing required credentials: {', '.join(missing)}"
        )
        if Confirm.ask("\nWould you like to run the setup now?"):
            interactive_setup()
            return
        raise typer.Exit(1)

    # Set environment variables for the scrobbler
    os.environ["LASTFM_USERNAME"] = final_username
    os.environ["LASTFM_PASSWORD"] = final_password
    os.environ["LASTFM_API_KEY"] = final_api_key
    os.environ["LASTFM_API_SECRET"] = final_api_secret
    os.environ["SCROBBLE_INTERVAL"] = str(scrobble_interval)
    os.environ["SPEAKER_REDISCOVERY_INTERVAL"] = str(rediscovery_interval)
    os.environ["SCROBBLE_THRESHOLD_PERCENT"] = str(threshold)

    # Import SonosScrobbler only when needed
    from .sonos_lastfm import SonosScrobbler

    # Run the scrobbler
    scribbler = SocoScribbler()
    scribbler.run()


def main() -> None:
    """Entry point for soco-scribbler CLI."""
    app()
