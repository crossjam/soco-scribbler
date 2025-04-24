import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def validate_config() -> Optional[List[str]]:
    """Validate required environment variables.

    Returns:
        List of missing variables if any, None if all required vars are present
    """
    required_vars = [
        "LASTFM_USERNAME",
        "LASTFM_PASSWORD",
        "LASTFM_API_KEY",
        "LASTFM_API_SECRET",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    return missing_vars if missing_vars else None


def get_config():
    """Get configuration values, validating them first.

    Raises:
        ValueError: If required environment variables are missing
    """
    if missing := validate_config():
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please set them in your .env file",
        )

    return {
        # Last.fm API credentials
        "LASTFM_USERNAME": os.getenv("LASTFM_USERNAME"),
        "LASTFM_PASSWORD": os.getenv("LASTFM_PASSWORD"),
        "LASTFM_API_KEY": os.getenv("LASTFM_API_KEY"),
        "LASTFM_API_SECRET": os.getenv("LASTFM_API_SECRET"),
        # Scrobbling settings
        "SCROBBLE_INTERVAL": int(os.getenv("SCROBBLE_INTERVAL", "1")),  # seconds
        "SPEAKER_REDISCOVERY_INTERVAL": int(
            os.getenv("SPEAKER_REDISCOVERY_INTERVAL", "10"),
        ),  # seconds
        # Get and validate scrobble threshold percentage
        "SCROBBLE_THRESHOLD_PERCENT": min(
            max(float(os.getenv("SCROBBLE_THRESHOLD_PERCENT") or "25"), 0), 100
        ),
        # Data storage paths
        "DATA_DIR": Path("./data"),
    }


# Export config values but don't validate at import time
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
LASTFM_PASSWORD = os.getenv("LASTFM_PASSWORD")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET")

# Scrobbling settings
SCROBBLE_INTERVAL = int(os.getenv("SCROBBLE_INTERVAL", "1"))  # seconds
SPEAKER_REDISCOVERY_INTERVAL = int(
    os.getenv("SPEAKER_REDISCOVERY_INTERVAL", "10"),
)  # seconds

# Get and validate scrobble threshold percentage
SCROBBLE_THRESHOLD_PERCENT = float(os.getenv("SCROBBLE_THRESHOLD_PERCENT") or "25")
if not 0 <= SCROBBLE_THRESHOLD_PERCENT <= 100:
    SCROBBLE_THRESHOLD_PERCENT = 25

# Data storage paths
DATA_DIR = Path("./data")
LAST_SCROBBLED_FILE = DATA_DIR / "last_scrobbled.json"
CURRENTLY_PLAYING_FILE = DATA_DIR / "currently_playing.json"
