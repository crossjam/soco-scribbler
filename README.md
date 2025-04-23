# Sonos to Last.fm Scrobbler

This script automatically scrobbles music playing on your Sonos speakers to Last.fm.

## Features

- Automatically detects Sonos speakers on your network
- Scrobbles tracks to Last.fm
- Prevents duplicate scrobbles
- Handles multiple speakers
- Error handling and logging

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get your Last.fm API credentials:
   - Go to https://www.last.fm/api/account/create
   - Create a new API account
   - Note down your API key and API secret

3. Configure the script:
   - Open `config.py`
   - Fill in your Last.fm credentials:
     - `LASTFM_USERNAME`: Your Last.fm username
     - `LASTFM_PASSWORD`: Your Last.fm password
     - `LASTFM_API_KEY`: Your Last.fm API key
     - `LASTFM_API_SECRET`: Your Last.fm API secret
   - Optionally adjust `SCROBBLE_INTERVAL` (default: 30 seconds)

## Usage

Run the script:
```bash
python sonos_lastfm.py
```

The script will:
1. Discover Sonos speakers on your network
2. Monitor currently playing tracks
3. Scrobble new tracks to Last.fm
4. Log all activities to the console

## Requirements

- Python 3.6+
- Sonos speakers on your network
- Last.fm account
- Last.fm API credentials 