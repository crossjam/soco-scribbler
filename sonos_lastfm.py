#!/usr/bin/env python3
"""
Sonos to Last.fm scrobbler using uv for dependency management.
"""

import logging
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

from soco import discover
from pylast import LastFMNetwork, md5

from config import (
    LASTFM_USERNAME,
    LASTFM_PASSWORD,
    LASTFM_API_KEY,
    LASTFM_API_SECRET,
    SCROBBLE_INTERVAL,
    SCROBBLE_THRESHOLD_PERCENT,
    SPEAKER_REDISCOVERY_INTERVAL,
)
from utils import update_all_progress_displays, custom_print

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,  # Ensure we reset any existing handlers
)
logger = logging.getLogger(__name__)

# Set SoCo logging to INFO
soco_logger = logging.getLogger("soco")
soco_logger.setLevel(logging.INFO)

# Completely suppress pylast HTTP request logging
pylast_logger = logging.getLogger("pylast")
pylast_logger.setLevel(logging.WARNING)  # Only show warnings and errors
pylast_logger.addHandler(logging.NullHandler())  # Add null handler
pylast_logger.propagate = False  # Prevent propagation to root logger completely

# Also suppress httpx logging which pylast uses internally
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)
httpx_logger.propagate = False

# Storage paths - using local data directory
DATA_DIR = Path("data")
LAST_SCROBBLED_FILE = DATA_DIR / "last_scrobbled.json"
CURRENTLY_PLAYING_FILE = DATA_DIR / "currently_playing.json"


class SonosScrobbler:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.last_scrobbled_file = LAST_SCROBBLED_FILE
        self.currently_playing_file = CURRENTLY_PLAYING_FILE

        # Create data directory if it doesn't exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize Last.fm network
        self.network = LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_API_SECRET,
            username=LASTFM_USERNAME,
            password_hash=md5(LASTFM_PASSWORD),
        )

        # Load or initialize tracking data
        self.last_scrobbled = self.load_json(LAST_SCROBBLED_FILE, {})
        self.currently_playing = self.load_json(CURRENTLY_PLAYING_FILE, {})
        self.previous_tracks = {}  # Track previous tracks for each speaker

        # Initialize Sonos discovery
        self.speakers = []
        self.discover_speakers()

    def load_json(self, file_path: Path, default_value: dict) -> dict:
        """Load JSON data from file or return default value if file doesn't exist."""
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        return default_value

    def save_json(self, file_path: Path, data: dict):
        """Save data to JSON file."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")

    def discover_speakers(self):
        """Discover Sonos speakers on the network."""
        try:
            new_speakers = list(discover())

            # Get sets of speaker IDs for comparison
            old_speaker_ids = {s.ip_address for s in self.speakers}
            new_speaker_ids = {s.ip_address for s in new_speakers}

            # Detect changes
            added_speakers = new_speaker_ids - old_speaker_ids
            removed_speakers = old_speaker_ids - new_speaker_ids

            # Only log if there are changes
            if added_speakers or removed_speakers:
                if added_speakers:
                    for speaker in new_speakers:
                        if speaker.ip_address in added_speakers:
                            custom_print(
                                f"New speaker found: {speaker.player_name} ({speaker.ip_address})"
                            )

                if removed_speakers:
                    for speaker in self.speakers:
                        if speaker.ip_address in removed_speakers:
                            custom_print(
                                f"Speaker removed: {speaker.player_name} ({speaker.ip_address})"
                            )

                custom_print(f"Updated speaker count: {len(new_speakers)}")

            # Update the speakers list
            self.speakers = new_speakers

            # Log warning only if we have no speakers at all
            if not self.speakers:
                custom_print("No Sonos speakers found", "WARNING")

        except Exception as e:
            custom_print(f"Error discovering speakers: {e}", "ERROR")
            self.speakers = []

    def should_scrobble(self, track_info: dict, speaker_id: str) -> bool:
        """
        Determine if a track should be scrobbled based on Last.fm rules and history.
        """
        if not track_info.get("artist") or not track_info.get("title"):
            return False

        track_id = f"{track_info['artist']}-{track_info['title']}"
        current_time = datetime.now()

        # Check if track was recently scrobbled
        if track_id in self.last_scrobbled:
            last_scrobble_time = datetime.fromisoformat(self.last_scrobbled[track_id])
            if (current_time - last_scrobble_time) < timedelta(minutes=30):
                return False

        # Check if track meets scrobbling criteria
        if speaker_id in self.currently_playing:
            current_track = self.currently_playing[speaker_id]
            position = current_track.get("position", 0)
            duration = current_track.get("duration", 0)

            threshold_decimal = SCROBBLE_THRESHOLD_PERCENT / 100.0
            return (position >= duration * threshold_decimal) or (
                position >= 240
            )  # configured percentage or 4 minutes

        return False

    def update_track_info(self, speaker) -> dict:
        """Get current track information from a speaker."""
        try:
            track_info = speaker.get_current_track_info()
            logger.debug(f"Raw track info from {speaker.player_name}: {track_info}")

            # Parse duration (format "0:04:32" or "4:32")
            duration_parts = track_info.get("duration", "0:00").split(":")
            if len(duration_parts) == 3:  # "H:MM:SS"
                duration = (
                    int(duration_parts[0]) * 3600
                    + int(duration_parts[1]) * 60
                    + int(duration_parts[2])
                )
            else:  # "MM:SS"
                duration = int(duration_parts[0]) * 60 + int(duration_parts[1])

            # Parse position (format "0:02:45" or "2:45")
            position_parts = track_info.get("position", "0:00").split(":")
            if len(position_parts) == 3:  # "H:MM:SS"
                position = (
                    int(position_parts[0]) * 3600
                    + int(position_parts[1]) * 60
                    + int(position_parts[2])
                )
            else:  # "MM:SS"
                position = int(position_parts[0]) * 60 + int(position_parts[1])

            logger.debug(
                f"Parsed times for {track_info.get('title')}: "
                f"position={track_info.get('position')}->({position}s), "
                f"duration={track_info.get('duration')}->({duration}s)"
            )

            return {
                "artist": track_info.get("artist"),
                "title": track_info.get("title"),
                "album": track_info.get("album"),
                "duration": duration,
                "position": position,
                "state": speaker.get_current_transport_info().get(
                    "current_transport_state"
                ),
            }
        except Exception as e:
            logger.error(f"Error getting track info from {speaker.player_name}: {e}")
            return {}

    def scrobble_track(self, track_info: dict):
        """Scrobble a track to Last.fm."""
        try:
            self.network.scrobble(
                artist=track_info["artist"],
                title=track_info["title"],
                timestamp=int(time.time()),
                album=track_info.get("album", ""),
            )

            # Update last scrobbled time
            track_id = f"{track_info['artist']}-{track_info['title']}"
            self.last_scrobbled[track_id] = datetime.now().isoformat()
            self.save_json(LAST_SCROBBLED_FILE, self.last_scrobbled)

            custom_print(f"Scrobbled: {track_info['artist']} - {track_info['title']}")
        except Exception as e:
            custom_print(f"Error scrobbling track: {e}", "ERROR")

    def monitor_speakers(self):
        """Main loop to monitor speakers and scrobble tracks."""
        custom_print("Starting Sonos Last.fm Scrobbler")
        display_info = {}
        last_discovery_time = 0
        try:
            while True:
                # Check if it's time to rediscover speakers
                current_time = time.time()
                if current_time - last_discovery_time >= SPEAKER_REDISCOVERY_INTERVAL:
                    self.discover_speakers()
                    last_discovery_time = current_time

                display_info.clear()  # Reset display info each iteration

                for speaker in self.speakers:
                    try:
                        speaker_id = speaker.ip_address
                        track_info = self.update_track_info(speaker)

                        if not track_info:
                            continue

                        # Check if this is a new track
                        prev_track = self.previous_tracks.get(speaker_id, {})
                        current_track_id = f"{track_info.get('artist', '')}-{track_info.get('title', '')}"
                        prev_track_id = f"{prev_track.get('artist', '')}-{prev_track.get('title', '')}"

                        if (
                            current_track_id != prev_track_id
                            and track_info.get("artist")
                            and track_info.get("title")
                            and track_info["state"] == "PLAYING"
                        ):
                            custom_print(
                                f"Now playing on {speaker.player_name}: "
                                f"{track_info['artist']} - {track_info['title']}"
                            )

                        # Update previous track info
                        self.previous_tracks[speaker_id] = track_info.copy()

                        # Update currently playing info
                        self.currently_playing[speaker_id] = track_info
                        self.save_json(CURRENTLY_PLAYING_FILE, self.currently_playing)

                        # Prepare display info for this speaker
                        threshold = int(
                            track_info["duration"] * SCROBBLE_THRESHOLD_PERCENT / 100
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
                            track_info, speaker_id
                        ):
                            self.scrobble_track(track_info)

                    except Exception as e:
                        custom_print(
                            f"Error monitoring {speaker.player_name}: {e}", "ERROR"
                        )

                # Update all progress displays together
                if display_info:
                    update_all_progress_displays(display_info)

                time.sleep(SCROBBLE_INTERVAL)
        except KeyboardInterrupt:
            custom_print("\nShutting down...")  # Add newline before shutdown message
        except Exception as e:
            custom_print(f"Unexpected error: {e}", "ERROR")

    def run(self):
        """Start the scrobbler."""
        self.monitor_speakers()


if __name__ == "__main__":
    scrobbler = SonosScrobbler()
    scrobbler.run()
