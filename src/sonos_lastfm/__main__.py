"""Main entry point for the sonos_lastfm package."""

from .sonos_lastfm import SonosScrobbler


def main() -> None:
    """Run the Sonos Last.fm scrobbler."""
    scrobbler = SonosScrobbler()
    scrobbler.run()


if __name__ == "__main__":
    main()
