"""Command line interface for Sonos Last.fm scrobbler."""

import os
from pathlib import Path
from typing import Optional

import keyring
import rich
import typer
from rich.prompt import Confirm, Prompt

from .sonos_lastfm import SonosScrobbler

# Create Typer app instance
app = typer.Typer(
    name="sonos-lastfm",
    help="Scrobble your Sonos plays to Last.fm",
    add_completion=False,
)

# Constants
APP_NAME = "sonos-lastfm"
CONFIG_DIR = Path.home() / ".config" / APP_NAME

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_stored_credential(key: str) -> Optional[str]:
    """Get a credential from the system keyring.

    Args:
        key: The key to retrieve

    Returns:
        The stored credential or None if not found
    """
    return keyring.get_password(APP_NAME, key)


def store_credential(key: str, value: str) -> None:
    """Store a credential in the system keyring.

    Args:
        key: The key to store
        value: The value to store
    """
    keyring.set_password(APP_NAME, key, value)


def get_config_value(
    key: str,
    cli_value: Optional[str] = None,
    env_key: Optional[str] = None,
) -> Optional[str]:
    """Get a configuration value from CLI args, environment, or keyring.

    Args:
        key: The key to retrieve from keyring
        cli_value: Value provided via CLI
        env_key: Environment variable name to check

    Returns:
        The configuration value or None if not found
    """
    # CLI args take precedence
    if cli_value is not None:
        return cli_value

    # Then check environment
    if env_key and (env_value := os.getenv(env_key)):
        return env_value

    # Finally check keyring
    return get_stored_credential(key)


def interactive_setup() -> None:
    """Run interactive setup to configure credentials."""
    rich.print("\n[bold]Welcome to Sonos Last.fm Scrobbler Setup![/bold]\n")
    rich.print("Please enter your Last.fm credentials:")

    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    api_key = Prompt.ask("API Key")
    api_secret = Prompt.ask("API Secret", password=True)

    # Store credentials
    store_credential("username", username)
    store_credential("password", password)
    store_credential("api_key", api_key)
    store_credential("api_secret", api_secret)

    rich.print("\n[green]✓[/green] Credentials stored securely!")


@app.command()
def run(
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
        help="Run interactive setup",
    ),
) -> None:
    """Run the Sonos Last.fm scrobbler."""
    if setup:
        interactive_setup()
        return

    # Get credentials from various sources
    final_username = get_config_value("username", username, "LASTFM_USERNAME")
    final_password = get_config_value("password", password, "LASTFM_PASSWORD")
    final_api_key = get_config_value("api_key", api_key, "LASTFM_API_KEY")
    final_api_secret = get_config_value("api_secret", api_secret, "LASTFM_API_SECRET")

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

    # Run the scrobbler
    scrobbler = SonosScrobbler()
    scrobbler.run()


def main() -> None:
    """Entry point for the CLI."""
    app()
