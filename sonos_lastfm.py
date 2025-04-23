import logging
import time
from typing import Dict, Optional

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
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SonosLastFMScrobbler:
    def __init__(self):
        self.network = LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_API_SECRET,
            username=LASTFM_USERNAME,
            password_hash=md5(LASTFM_PASSWORD),
        )
        self.last_scrobbled: Dict[str, Dict] = {}

    def get_speaker_info(self, speaker) -> Optional[Dict]:
        try:
            info = speaker.get_current_track_info()
            if not info or not info.get("title") or not info.get("artist"):
                return None
            return info
        except Exception as e:
            logger.error(
                f"Error getting track info from speaker {speaker.player_name}: {e}"
            )
            return None

    def should_scrobble(self, speaker_name: str, track_info: Dict) -> bool:
        last_track = self.last_scrobbled.get(speaker_name)
        if not last_track:
            return True

        # Check if it's the same track
        if (
            last_track["title"] == track_info["title"]
            and last_track["artist"] == track_info["artist"]
        ):
            return False

        return True

    def scrobble_track(self, speaker_name: str, track_info: Dict):
        try:
            self.network.scrobble(
                artist=track_info["artist"],
                title=track_info["title"],
                timestamp=int(time.time()),
            )
            self.last_scrobbled[speaker_name] = track_info
            logger.info(
                f"Scrobbled: {track_info['artist']} - {track_info['title']} from {speaker_name}"
            )
        except Exception as e:
            logger.error(f"Error scrobbling track from {speaker_name}: {e}")

    def run(self):
        logger.info("Starting Sonos to Last.fm scrobbler...")
        while True:
            try:
                speakers = discover()
                if not speakers:
                    logger.warning("No Sonos speakers found")
                    time.sleep(SCROBBLE_INTERVAL)
                    continue

                for speaker in speakers:
                    track_info = self.get_speaker_info(speaker)
                    if track_info and self.should_scrobble(
                        speaker.player_name, track_info
                    ):
                        self.scrobble_track(speaker.player_name, track_info)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")

            time.sleep(SCROBBLE_INTERVAL)


if __name__ == "__main__":
    scrobbler = SonosLastFMScrobbler()
    scrobbler.run()
