import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from platformdirs import PlatformDirs

APP_NAME = "dev.pirateninja.soco-scribbler"
APP_AUTHOR = "SocoScribbler"
APP_DIRS = PlatformDirs(APP_NAME, APP_AUTHOR)

CONFIG_DIR = Path(APP_DIRS.user_config_dir)
DATA_DIR = Path(APP_DIRS.user_data_dir)
LOG_DIR = Path(APP_DIRS.user_log_dir)
CREDENTIALS_FILE = CONFIG_DIR / ".env"
OP_CREDENTIALS_FILE = CONFIG_DIR / ".op_env"
DEFAULT_LOG_FILE = LOG_DIR / "scribbles.jsonl"

# Load environment variables from default .env and user config directory
load_dotenv()
load_dotenv(CREDENTIALS_FILE)


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
        "DATA_DIR": DATA_DIR,
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
LAST_SCROBBLED_FILE = DATA_DIR / "last_scrobbled.json"
CURRENTLY_PLAYING_FILE = DATA_DIR / "currently_playing.json"


def ensure_user_dirs() -> dict[str, bool]:
    """Ensure user config/data/log directories exist.

    Returns:
        Mapping of directory type to whether it was created this call.
    """
    created: dict[str, bool] = {}
    for label, path in {
        "config": CONFIG_DIR,
        "data": DATA_DIR,
        "log": LOG_DIR,
    }.items():
        if path.exists():
            created[label] = False
        else:
            path.mkdir(parents=True, exist_ok=True)
            created[label] = True
    return created
