import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Last.fm API credentials
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
LASTFM_PASSWORD = os.getenv("LASTFM_PASSWORD")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET")

# Scrobbling settings
SCROBBLE_INTERVAL = int(os.getenv("SCROBBLE_INTERVAL", "1"))  # seconds

# Get and validate scrobble threshold percentage
SCROBBLE_THRESHOLD_PERCENT = float(os.getenv("SCROBBLE_THRESHOLD_PERCENT") or "25")
if not 0 <= SCROBBLE_THRESHOLD_PERCENT <= 100:
    SCROBBLE_THRESHOLD_PERCENT = 25

# Data storage paths
DATA_DIR = Path("./data")
LAST_SCROBBLED_FILE = DATA_DIR / "last_scrobbled.json"
CURRENTLY_PLAYING_FILE = DATA_DIR / "currently_playing.json"

# Validate required environment variables
required_vars = [
    "LASTFM_USERNAME",
    "LASTFM_PASSWORD",
    "LASTFM_API_KEY",
    "LASTFM_API_SECRET",
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}\n"
        "Please set them in your .env file"
    )
