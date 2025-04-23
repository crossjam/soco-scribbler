import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Last.fm credentials
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME", "your_username")
LASTFM_PASSWORD = os.getenv("LASTFM_PASSWORD", "your_password")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "your_api_key")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET", "your_api_secret")

# Scrobbling settings
SCROBBLE_INTERVAL = int(os.getenv("SCROBBLE_INTERVAL", "30"))  # seconds
