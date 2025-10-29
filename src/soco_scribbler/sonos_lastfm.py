#!/usr/bin/env python3
"""Sonos to Last.fm scrobbler using uv for dependency management."""

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final, cast, TypedDict

if True:  # type checking block
    from soco import SoCo  # type: ignore[import-untyped]

import pylast  # type: ignore[import-untyped]
import soco  # type: ignore[import-untyped]

from .config import get_config
from .utils import custom_print, logger, update_all_progress_displays

# Constants
SCROBBLE_MIN_TIME: Final[int] = 240  # 4 minutes in seconds
TIME_FORMAT_HMS: Final[int] = 3  # Number of parts in H:MM:SS format


def assert_not_none(value: str | None, name: str) -> str:
    """Assert that a value is not None and return it as a string.

    Args:
        value: The value to check
        name: The name of the value for error messages

    Returns:
        The value as a string

    Raises:
        ValueError: If the value is None
    """
    if value is None:
        msg = f"{name} must not be None"
        custom_print(msg, "ERROR")
        raise ValueError(msg)
    return value


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,  # Ensure we reset any existing handlers
)

# Set SoCo logging to INFO
soco_logger: Final[logging.Logger] = logging.getLogger("soco")
soco_logger.setLevel(logging.INFO)

# Completely suppress pylast HTTP request logging
pylast_logger: Final[logging.Logger] = logging.getLogger("pylast")
pylast_logger.setLevel(logging.WARNING)  # Only show warnings and errors
pylast_logger.addHandler(logging.NullHandler())  # Add null handler
pylast_logger.propagate = False  # Prevent propagation to root logger completely

# Also suppress httpx logging which pylast uses internally
httpx_logger: Final[logging.Logger] = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)
httpx_logger.propagate = False

# Storage paths - using local data directory
DATA_DIR: Final[Path] = Path("data")
LAST_SCROBBLED_FILE: Final[Path] = DATA_DIR / "last_scrobbled.json"
CURRENTLY_PLAYING_FILE: Final[Path] = DATA_DIR / "currently_playing.json"


class TransportInfo(TypedDict):
    current_transport_state: str
    current_transport_status: str
    current_speed: str


class SonosScrobbler:
    """A class to manage Sonos speaker discovery and Last.fm scrobbling."""

    def __init__(self) -> None:
        """Initialize the scrobbler with Last.fm credentials and speaker discovery."""
        # Get validated config
        config = get_config()

        self.data_dir: Final[Path] = config["DATA_DIR"]
        self.last_scrobbled_file: Final[Path] = self.data_dir / "last_scrobbled.json"
        self.currently_playing_file: Final[Path] = (
            self.data_dir / "currently_playing.json"
        )

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Last.fm network
        self.network: Final[pylast.LastFMNetwork] = pylast.LastFMNetwork(
            api_key=assert_not_none(config["LASTFM_API_KEY"], "LASTFM_API_KEY"),
            api_secret=assert_not_none(
                config["LASTFM_API_SECRET"], "LASTFM_API_SECRET"
            ),
            username=assert_not_none(config["LASTFM_USERNAME"], "LASTFM_USERNAME"),
            password_hash=pylast.md5(
                assert_not_none(config["LASTFM_PASSWORD"], "LASTFM_PASSWORD")
            ),
        )

        # Store config values we'll need later
        self.scrobble_interval = config["SCROBBLE_INTERVAL"]
        self.speaker_rediscovery_interval = config["SPEAKER_REDISCOVERY_INTERVAL"]
        self.scrobble_threshold_percent = config["SCROBBLE_THRESHOLD_PERCENT"]

        # Load or initialize tracking data
        self.last_scrobbled: dict[str, str] = self.load_json(
            self.last_scrobbled_file, {}
        )
        self.currently_playing: dict[str, dict[str, Any]] = self.load_json(
            self.currently_playing_file,
            {},
        )
        self.previous_tracks: dict[str, dict[str, Any]] = {}

        # Initialize Sonos discovery
        self.speakers: list[SoCo] = []
        self.discover_speakers()

    def load_json(
        self,
        file_path: Path,
        default_value: dict[str, Any],
    ) -> dict[str, Any]:
        """Load JSON data from file or return default value if file doesn't exist.

        Args:
            file_path: Path to the JSON file
            default_value: Value to return if file doesn't exist or is invalid

        Returns:
            The loaded JSON data or default value
        """
        try:
            if file_path.exists():
                with file_path.open() as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        logger.exception(
                            "Invalid JSON data in %s: not a dictionary",
                            file_path,
                        )
                        return default_value
                    return cast("dict[str, Any]", data)
        except Exception:
            logger.exception("Error loading %s", file_path)
        return default_value

    def save_json(self, file_path: Path, data: dict[str, Any]) -> None:
        """Save data to JSON file.

        Args:
            file_path: Path to save the JSON file
            data: Data to save
        """
        try:
            with file_path.open("w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            logger.exception("Error saving %s", file_path)

    def discover_speakers(self) -> None:
        """Discover Sonos speakers on the network."""
        try:
            new_speakers: list[SoCo] = list(soco.discover())

            # Get sets of speaker IDs for comparison
            old_speaker_ids: set[str] = {s.ip_address for s in self.speakers}
            new_speaker_ids: set[str] = {s.ip_address for s in new_speakers}

            # Detect changes
            added_speakers: set[str] = new_speaker_ids - old_speaker_ids
            removed_speakers: set[str] = old_speaker_ids - new_speaker_ids

            # Only log if there are changes
            if added_speakers or removed_speakers:
                if added_speakers:
                    for speaker in new_speakers:
                        if speaker.ip_address in added_speakers:
                            custom_print(
                                "New speaker found: "
                                f"{speaker.player_name} ({speaker.ip_address})",
                            )

                if removed_speakers:
                    for speaker in self.speakers:
                        if speaker.ip_address in removed_speakers:
                            custom_print(
                                "Speaker removed: "
                                f"{speaker.player_name} ({speaker.ip_address})",
                            )

                custom_print(f"Updated speaker count: {len(new_speakers)}")

            # Update the speakers list
            self.speakers = new_speakers

            # Log warning only if we have no speakers at all
            if not self.speakers:
                custom_print("No Sonos speakers found", "WARNING")

        except Exception:
            custom_print("Error discovering speakers", "ERROR")
            logger.exception("Error discovering speakers")
            self.speakers = []

    def should_scrobble(self, track_info: dict[str, Any], speaker_id: str) -> bool:
        """Determine if a track should be scrobbled based on Last.fm rules and history.

        Args:
            track_info: Information about the track
            speaker_id: ID of the speaker playing the track

        Returns:
            True if the track should be scrobbled, False otherwise
        """
        if not track_info.get("artist") or not track_info.get("title"):
            return False

        track_id: str = f"{track_info['artist']}-{track_info['title']}"
        current_time: datetime = datetime.now(UTC)

        # Check if track was recently scrobbled
        if track_id in self.last_scrobbled:
            last_scrobble_time: datetime = datetime.fromisoformat(
                self.last_scrobbled[track_id],
            )
            if (current_time - last_scrobble_time) < timedelta(minutes=30):
                return False

        # Check if track meets scrobbling criteria
        if speaker_id in self.currently_playing:
            current_track: dict[str, Any] = self.currently_playing[speaker_id]
            position: int = current_track.get("position", 0)
            duration: int = current_track.get("duration", 0)

            threshold_decimal: float = self.scrobble_threshold_percent / 100.0
            return (position >= duration * threshold_decimal) or (
                position >= SCROBBLE_MIN_TIME
            )

        return False

    def update_track_info(self, speaker: SoCo) -> dict[str, Any]:
        """Get current track information from a speaker.

        Args:
            speaker: The Sonos speaker to get information from

        Returns:
            Dictionary containing track information
        """
        try:
            track_info: dict[str, Any] = speaker.get_current_track_info()
            logger.debug(
                "Raw track info from %s: %s",
                speaker.player_name,
                track_info,
            )
            # Parse duration (format "0:04:32" or "4:32")
            duration_parts: list[str] = track_info.get("duration", "0:00").split(
                ":",
            )
            if duration_parts[0] == "NOT_IMPLEMENTED":
                duration_parts = [0, 0]
            
            logger.debug(
                "duration parts: %s: %s", track_info.get("duration", None), duration_parts
            )
            
            if len(duration_parts) == TIME_FORMAT_HMS:  # "H:MM:SS"
                duration: int = (
                    int(duration_parts[0]) * 3600
                    + int(duration_parts[1]) * 60
                    + int(duration_parts[2])
                )
            else:  # "MM:SS"
                duration = int(duration_parts[0]) * 60 + int(duration_parts[1])

            # Parse position (format "0:02:45" or "2:45")
            position_parts: list[str] = track_info.get("position", "0:00").split(
                ":",
            )

            if position_parts[0] == "NOT_IMPLEMENTED":
                position_parts = [0, 0]
            
            logger.debug(
                "position part: %s: %s", track_info.get("position", None), position_parts
            )
            if len(position_parts) == TIME_FORMAT_HMS:  # "H:MM:SS"
                position: int = (
                    int(position_parts[0]) * 3600
                    + int(position_parts[1]) * 60
                    + int(position_parts[2])
                )
            else:  # "MM:SS"
                position = int(position_parts[0]) * 60 + int(position_parts[1])

            logger.debug(
                "Parsed times for %s: position=%s->(%ds), duration=%s->(%ds)",
                track_info.get("title"),
                track_info.get("position"),
                position,
                track_info.get("duration"),
                duration,
            )

            transport_info: TransportInfo = speaker.get_current_transport_info()  # type: ignore[assignment]
            return {
                "artist": track_info.get("artist"),
                "title": track_info.get("title"),
                "album": track_info.get("album"),
                "duration": duration,
                "position": position,
                "state": transport_info.get("current_transport_state"),
            }
        except Exception:
            logger.exception("Error getting track info from %s", speaker.player_name)
            return {}

    def scrobble_track(self, track_info: dict[str, Any]) -> None:
        """Scrobble a track to Last.fm.

        Args:
            track_info: Information about the track to scrobble
        """
        try:
            self.network.scrobble(
                artist=track_info["artist"],
                title=track_info["title"],
                timestamp=int(time.time()),
                album=track_info.get("album", ""),
            )

            # Update last scrobbled time
            track_id: str = f"{track_info['artist']}-{track_info['title']}"
            self.last_scrobbled[track_id] = datetime.now(UTC).isoformat()
            self.save_json(self.last_scrobbled_file, self.last_scrobbled)

            custom_print(f"Scrobbled: {track_info['artist']} - {track_info['title']}")
        except Exception:
            logger.exception("Error scrobbling track")
            custom_print("Error scrobbling track", "ERROR")

    def monitor_speakers(self) -> None:
        """Main loop to monitor speakers and scrobble tracks."""
        custom_print("Starting Sonos Last.fm Scrobbler")
        display_info: dict[str, dict[str, Any]] = {}
        last_discovery_time: float = 0
        try:
            while True:
                # Check if it's time to rediscover speakers
                current_time: float = time.time()
                if (
                    current_time - last_discovery_time
                    >= self.speaker_rediscovery_interval
                ):
                    self.discover_speakers()
                    last_discovery_time = current_time

                display_info.clear()  # Reset display info each iteration

                for speaker in self.speakers:
                    try:
                        speaker_id: str = speaker.ip_address
                        track_info: dict[str, Any] = self.update_track_info(speaker)

                        if not track_info:
                            continue

                        # Check if this is a new track
                        prev_track: dict[str, Any] = self.previous_tracks.get(
                            speaker_id,
                            {},
                        )
                        current_track_id: str = (
                            f"{track_info.get('artist', '')}-"
                            f"{track_info.get('title', '')}"
                        )
                        prev_track_id: str = (
                            f"{prev_track.get('artist', '')}-"
                            f"{prev_track.get('title', '')}"
                        )

                        if (
                            current_track_id != prev_track_id
                            and track_info.get("artist")
                            and track_info.get("title")
                            and track_info["state"] == "PLAYING"
                        ):
                            custom_print(
                                "Now playing on "
                                f"{speaker.player_name}: "
                                f"{track_info['artist']} - "
                                f"{track_info['title']}",
                            )

                        # Update previous track info
                        self.previous_tracks[speaker_id] = track_info.copy()

                        # Update currently playing info
                        self.currently_playing[speaker_id] = track_info
                        self.save_json(
                            self.currently_playing_file, self.currently_playing
                        )

                        # Prepare display info for this speaker
                        threshold: int = int(
                            track_info["duration"]
                            * self.scrobble_threshold_percent
                            / 100,
                        )
                        display_info[speaker_id] = {
                            "speaker_name": speaker.player_name,
                            "artist": track_info["artist"],
                            "title": track_info["title"],
                            "position": track_info["position"],
                            "duration": track_info["duration"],
                            "threshold": threshold,
                            "state": track_info["state"],
                        }

                        # Check if track should be scrobbled (only log scrobble events)
                        if track_info["state"] == "PLAYING" and self.should_scrobble(
                            track_info,
                            speaker_id,
                        ):
                            track_info["speaker"] = speaker.player_name
                            track_info["speaker_id"] = speaker_id
                            self.scrobble_track(track_info)

                    except Exception:
                        logger.exception(
                            "Error monitoring %s",
                            speaker.player_name,
                        )

                # Update all progress displays together
                if display_info:
                    update_all_progress_displays(display_info)

                time.sleep(self.scrobble_interval)
        except KeyboardInterrupt:
            custom_print("\nShutting down...")  # Add newline before shutdown message
        except Exception:
            logger.exception("Unexpected error")
            custom_print("Unexpected error", "ERROR")

    def run(self) -> None:
        """Start the scrobbler."""
        self.monitor_speakers()


if __name__ == "__main__":
    scrobbler = SonosScrobbler()
    scrobbler.run()
