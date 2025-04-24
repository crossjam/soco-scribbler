# Sonos to Last.fm Scrobbler

![sonos lastfm](https://github.com/user-attachments/assets/6c84174d-a927-4801-8800-e2343d1646d7)

This script automatically scrobbles music playing on your Sonos speakers to Last.fm.

## Features

- Automatic Sonos speaker discovery on your network
- Real-time track monitoring and scrobbling
- Smart duplicate scrobble prevention
- Multi-speaker support
- Local data persistence for tracking scrobble history
- Secure credential storage using system keyring
- Modern CLI interface with interactive setup

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install sonos-lastfm
```

### Option 2: Local Development Setup

1. Install `uv` (Python package installer):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Setup and run using Make commands:
   ```bash
   # Setup Python environment with uv
   make setup

   # Install dependencies
   make install

   # For development, install additional tools (optional)
   make install-dev
   ```

   Run `make help` to see all available commands.

## Usage

### Quick Start

1. Run the interactive setup to securely store your Last.fm credentials:
   ```bash
   sonos-lastfm --setup
   ```

2. Start scrobbling:
   ```bash
   sonos-lastfm
   ```

### Command Line Options

```bash
sonos-lastfm [OPTIONS]

Options:
  -u, --username TEXT            Last.fm username
  -p, --password TEXT           Last.fm password
  -k, --api-key TEXT           Last.fm API key
  -s, --api-secret TEXT        Last.fm API secret
  -i, --interval INTEGER       Scrobbling check interval in seconds [default: 1]
  -r, --rediscovery INTEGER    Speaker rediscovery interval in seconds [default: 10]
  -t, --threshold FLOAT        Scrobble threshold percentage [default: 25.0]
  --setup                      Run interactive setup
  --help                       Show this message and exit
```

### Configuration Methods

You can configure the scrobbler in three ways (in order of precedence):

1. Command line arguments:
   ```bash
   sonos-lastfm --username "your_username" --api-key "your_api_key"
   ```

2. Environment variables:
   ```bash
   export LASTFM_USERNAME=your_username
   export LASTFM_PASSWORD=your_password
   export LASTFM_API_KEY=your_api_key
   export LASTFM_API_SECRET=your_api_secret
   export SCROBBLE_INTERVAL=1
   export SPEAKER_REDISCOVERY_INTERVAL=10
   export SCROBBLE_THRESHOLD_PERCENT=25
   
   sonos-lastfm
   ```

3. Secure keyring storage (recommended):
   ```bash
   # Store credentials securely
   sonos-lastfm --setup
   
   # Run with stored credentials
   sonos-lastfm
   ```

### Docker Setup (Linux Only)

> Note: Docker setup is not recommended on macOS due to network mode limitations affecting Sonos discovery.

1. Create a `.env` file with your Last.fm credentials:
   ```bash
   LASTFM_USERNAME=your_username
   LASTFM_PASSWORD=your_password
   LASTFM_API_KEY=your_api_key
   LASTFM_API_SECRET=your_api_secret
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Scrobbling Rules

The script follows configurable scrobbling rules:
- A track is scrobbled when either:
  - Configured percentage of the track has been played (default: 25%, range: 0-100), OR
  - 4 minutes (240 seconds) of the track have been played
- For repeated plays of the same track:
  - Enforces a 30-minute minimum interval between scrobbles of the same track
  - Prevents duplicate scrobbles during continuous play

## Data Storage

- Credentials are stored securely in your system's keyring
- Scrobble history and currently playing information is stored in:
  - `~/.config/sonos-lastfm/last_scrobbled.json`
  - `~/.config/sonos-lastfm/currently_playing.json`

## Requirements

- Python 3.11+
- Sonos speakers on your network
- Last.fm account and API credentials
  - Get your API credentials at: https://www.last.fm/api/account/create

## Troubleshooting

Common issues and solutions:
- No speakers found: Ensure your computer is on the same network as your Sonos system
- Scrobbling not working: Check your Last.fm credentials with `sonos-lastfm --setup`
- Missing scrobbles: Verify that both artist and title information are available for the track
