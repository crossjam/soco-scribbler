from soco import discover
from pylast import LastFMNetwork, md5
import time

# configure
username = "YOUR_LASTFM_USERNAME"
password_hash = md5("YOUR_LASTFM_PASSWORD")
network = LastFMNetwork(
    api_key="API_KEY",
    api_secret="API_SECRET",
    username=username,
    password_hash=password_hash,
)

while True:
    for spkr in discover():
        info = spkr.get_current_track_info()
        network.scrobble(
            artist=info["artist"], title=info["title"], timestamp=int(time.time())
        )
    time.sleep(30)
