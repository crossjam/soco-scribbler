#!/usr/bin/env python3
"""
Sonos to Last.fm scrobbler using uv for dependency management.
"""

import logging
import time
import json
from typing import Dict, Optional
from pathlib import Path

from soco import discover
from pylast import LastFMNetwork, md5

from config import (
    LASTFM_USERNAME,
    LASTFM_PASSWORD,
    LASTFM_API_KEY,
    LASTFM_API_SECRET,
    SCROBBLE_INTERVAL,
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


class SonosLastFMScrobbler:
    def __init__(self):
        self.network = LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_API_SECRET,
            username=LASTFM_USERNAME,
            password_hash=md5(LASTFM_PASSWORD),
        )

        # Create data directory if it doesn't exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Load persisted data
        self.last_scrobbled = self._load_json(LAST_SCROBBLED_FILE)
        self.currently_playing = self._load_json(CURRENTLY_PLAYING_FILE)

    def _load_json(self, file_path: Path) -> Dict:
        """Load data from JSON file, return empty dict if file doesn't exist."""
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        return {}

    def _save_json(self, data: Dict, file_path: Path):
        """Save data to JSON file."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")

    def parse_time_str(self, time_str: str) -> int:
        """Convert time string (HH:MM:SS or MM:SS) to seconds."""
        try:
            parts = time_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0
        except (ValueError, AttributeError):
            return 0

    def get_speaker_info(self, speaker) -> Optional[Dict]:
        try:
            # First check if the speaker is actually playing
            transport_info = speaker.get_current_transport_info()
            if transport_info["current_transport_state"] != "PLAYING":
                logger.info(
                    f"Speaker {speaker.player_name} is not playing (state: {transport_info['current_transport_state']})"
                )
                return None

            info = speaker.get_current_track_info()
            if not info or not info.get("title") or not info.get("artist"):
                return None

            # Add duration and position in seconds
            info["duration_seconds"] = self.parse_time_str(info.get("duration", "0:00"))
            info["position_seconds"] = self.parse_time_str(info.get("position", "0:00"))

            return info
        except Exception as e:
            logger.error(
                f"Error getting track info from speaker {speaker.player_name}: {e}"
            )
            return None

    def should_scrobble(self, speaker_name: str, track_info: Dict) -> bool:
        current_track = self.currently_playing.get(speaker_name)

        # If no track is currently being tracked, start tracking this one
        if not current_track:
            self.currently_playing[speaker_name] = {
                **track_info,
                "start_time": time.time(),
                "start_position": track_info["position_seconds"],
            }
            self._save_json(self.currently_playing, CURRENTLY_PLAYING_FILE)
            return False

        # Check if it's a different track
        if (
            current_track["title"] != track_info["title"]
            or current_track["artist"] != track_info["artist"]
        ):
            # New track - update currently playing and don't scrobble yet
            self.currently_playing[speaker_name] = {
                **track_info,
                "start_time": time.time(),
                "start_position": track_info["position_seconds"],
            }
            self._save_json(self.currently_playing, CURRENTLY_PLAYING_FILE)
            return False

        # Same track - check if we should scrobble based on playback progress
        position_diff = track_info["position_seconds"] - current_track["start_position"]

        # Calculate how much of the track has been played
        duration = track_info["duration_seconds"]
        if duration == 0:  # Avoid division by zero
            return False

        # Check if we've already scrobbled this track recently
        last_scrobbled = self.last_scrobbled.get(speaker_name)
        if (
            last_scrobbled
            and last_scrobbled["title"] == track_info["title"]
            and last_scrobbled["artist"] == track_info["artist"]
        ):
            # For repeat plays, enforce a minimum time between scrobbles
            # Last.fm guidelines suggest 30 minutes between scrobbles of the same track
            MIN_TIME_BETWEEN_SCROBBLES = 30 * 60  # 30 minutes in seconds
            time_since_last_scrobble = time.time() - last_scrobbled["timestamp"]
            if time_since_last_scrobble < MIN_TIME_BETWEEN_SCROBBLES:
                return False

        # Scrobble if:
        # 1. We've played 50% of the track, or
        # 2. We've played for 4 minutes (240 seconds)
        played_percentage = (position_diff / duration) * 100
        should_scrobble = played_percentage >= 50 or position_diff >= 240

        # If we're going to scrobble, reset the start position for the next potential scrobble
        if should_scrobble:
            self.currently_playing[speaker_name]["start_position"] = track_info[
                "position_seconds"
            ]
            self.currently_playing[speaker_name]["start_time"] = time.time()
            self._save_json(self.currently_playing, CURRENTLY_PLAYING_FILE)

        return should_scrobble

    def scrobble_track(self, speaker_name: str, track_info: Dict):
        try:
            self.network.scrobble(
                artist=track_info["artist"],
                title=track_info["title"],
                timestamp=int(time.time()),
            )
            self.last_scrobbled[speaker_name] = {**track_info, "timestamp": time.time()}
            self._save_json(self.last_scrobbled, LAST_SCROBBLED_FILE)
            logger.info(
                f"Scrobbled: {track_info['artist']} - {track_info['title']} "
                f"from {speaker_name} (Position: {track_info['position']} / {track_info['duration']})"
            )
        except Exception as e:
            logger.error(f"Error scrobbling track from {speaker_name}: {e}")

    def run(self):
        logger.info("Starting Sonos to Last.fm scrobbler...")

        while True:
            try:
                speakers = discover()
                if speakers:
                    logger.info(f"Found {len(list(speakers))} Sonos speakers")
                    for speaker in speakers:
                        logger.info(
                            f"Found speaker: {speaker.player_name} at {speaker.ip_address}"
                        )
                        track_info = self.get_speaker_info(speaker)
                        if track_info and self.should_scrobble(
                            speaker.player_name, track_info
                        ):
                            self.scrobble_track(speaker.player_name, track_info)
                else:
                    logger.warning("No Sonos speakers found")

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)

            time.sleep(SCROBBLE_INTERVAL)


if __name__ == "__main__":
    scrobbler = SonosLastFMScrobbler()
    scrobbler.run()
