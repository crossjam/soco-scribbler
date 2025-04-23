#!/usr/bin/env python3
"""
Sonos to Last.fm scrobbler using uv for dependency management.
"""

import logging
import time
import socket
from typing import Dict, Optional

from soco import discover, SoCo
import ifaddr
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
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logging
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Enable SoCo debug logging
soco_logger = logging.getLogger("soco")
soco_logger.setLevel(logging.DEBUG)


class SonosLastFMScrobbler:
    def __init__(self):
        self.network = LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_API_SECRET,
            username=LASTFM_USERNAME,
            password_hash=md5(LASTFM_PASSWORD),
        )
        self.last_scrobbled: Dict[str, Dict] = {}

    def get_network_interfaces(self):
        """Log information about all network interfaces."""
        logger.debug("Scanning network interfaces:")
        for adapter in ifaddr.get_adapters():
            logger.debug(f"Interface: {adapter.nice_name}")
            for ip in adapter.ips:
                logger.debug(f"  IP: {ip.ip}")
                if isinstance(ip.ip, tuple):  # IPv6
                    logger.debug(f"    IPv6 address")
                else:  # IPv4
                    logger.debug(f"    Network: {ip.network_prefix}")

    def try_direct_speaker_discovery(self):
        """Try to discover speakers by direct IP scanning."""
        logger.debug("Attempting direct speaker discovery...")
        # Common Sonos ports
        ports = [1400, 1443]

        for adapter in ifaddr.get_adapters():
            for ip in adapter.ips:
                if isinstance(ip.ip, tuple):  # Skip IPv6
                    continue

                # Get network prefix
                if not hasattr(ip, "network_prefix"):
                    continue

                network = ip.ip.rsplit(".", 1)[0]
                logger.debug(f"Scanning network: {network}.*")

                # Scan last octet
                for i in range(1, 255):
                    target_ip = f"{network}.{i}"
                    for port in ports:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(0.1)
                            result = sock.connect_ex((target_ip, port))
                            if result == 0:
                                logger.debug(
                                    f"Found potential Sonos device at {target_ip}:{port}"
                                )
                                # Try to create a SoCo instance
                                try:
                                    speaker = SoCo(target_ip)
                                    info = speaker.get_speaker_info()
                                    logger.info(
                                        f"Confirmed Sonos speaker: {info['zone_name']} at {target_ip}"
                                    )
                                except Exception as e:
                                    logger.debug(
                                        f"Not a Sonos speaker at {target_ip}: {e}"
                                    )
                            sock.close()
                        except Exception as e:
                            logger.debug(f"Error scanning {target_ip}:{port} - {e}")

    def get_speaker_info(self, speaker) -> Optional[Dict]:
        try:
            logger.debug(
                f"Getting info for speaker: {speaker.player_name} ({speaker.ip_address})"
            )
            info = speaker.get_current_track_info()
            logger.debug(f"Raw track info: {info}")
            if not info or not info.get("title") or not info.get("artist"):
                logger.debug("Missing required track info fields")
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
            logger.debug(f"No previous track for {speaker_name}, will scrobble")
            return True

        # Check if it's the same track
        if (
            last_track["title"] == track_info["title"]
            and last_track["artist"] == track_info["artist"]
        ):
            logger.debug(f"Same track still playing on {speaker_name}, won't scrobble")
            return False

        logger.debug(f"New track on {speaker_name}, will scrobble")
        return True

    def scrobble_track(self, speaker_name: str, track_info: Dict):
        try:
            logger.debug(
                f"Attempting to scrobble: {track_info['artist']} - {track_info['title']}"
            )
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

        # Log network interface information
        self.get_network_interfaces()

        while True:
            try:
                logger.debug("Starting Sonos discovery...")
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
                    logger.warning("No Sonos speakers found via normal discovery")
                    logger.info("Attempting direct discovery...")
                    self.try_direct_speaker_discovery()

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)

            logger.debug(f"Sleeping for {SCROBBLE_INTERVAL} seconds...")
            time.sleep(SCROBBLE_INTERVAL)


if __name__ == "__main__":
    scrobbler = SonosLastFMScrobbler()
    scrobbler.run()
