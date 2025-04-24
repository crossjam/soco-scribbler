#!/usr/bin/env python3
"""
Sonos to Last.fm scrobbler using uv for dependency management.
"""

import logging
import time
import json
from typing import Dict, Optional
from pathlib import Path
import os
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
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO level
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set SoCo logging to INFO
soco_logger = logging.getLogger("soco")
soco_logger.setLevel(logging.INFO)

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
            self.speakers = list(discover())
            if self.speakers:
                logger.info(f"Found {len(self.speakers)} Sonos speaker(s)")
                for speaker in self.speakers:
                    logger.info(
                        f"Speaker found: {speaker.player_name} ({speaker.ip_address})"
                    )
            else:
                logger.warning("No Sonos speakers found")
        except Exception as e:
            logger.error(f"Error discovering speakers: {e}")
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
            return {
                "artist": track_info.get("artist"),
                "title": track_info.get("title"),
                "album": track_info.get("album"),
                "duration": int(track_info.get("duration", "0").split(":")[0]) * 60
                + int(track_info.get("duration", "0").split(":")[1]),
                "position": int(track_info.get("position", "0").split(":")[0]) * 60
                + int(track_info.get("position", "0").split(":")[1]),
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

            logger.info(f"Scrobbled: {track_info['artist']} - {track_info['title']}")
        except Exception as e:
            logger.error(f"Error scrobbling track: {e}")

    def monitor_speakers(self):
        """Main loop to monitor speakers and scrobble tracks."""
        logger.info("Starting Sonos Last.fm Scrobbler")
        try:
            while True:
                for speaker in self.speakers:
                    try:
                        speaker_id = speaker.ip_address
                        track_info = self.update_track_info(speaker)

                        if not track_info:
                            continue

                        # Update currently playing info
                        self.currently_playing[speaker_id] = track_info
                        self.save_json(CURRENTLY_PLAYING_FILE, self.currently_playing)

                        # Check if track should be scrobbled
                        if track_info["state"] == "PLAYING" and self.should_scrobble(
                            track_info, speaker_id
                        ):
                            self.scrobble_track(track_info)

                    except Exception as e:
                        logger.error(f"Error monitoring {speaker.player_name}: {e}")

                time.sleep(SCROBBLE_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def run(self):
        """Start the scrobbler."""
        self.monitor_speakers()


if __name__ == "__main__":
    scrobbler = SonosScrobbler()
    scrobbler.run()
