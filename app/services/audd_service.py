
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AUDD_API_KEY = os.getenv("AudD_API_KEY")
AUDD_URL = "https://api.audd.io/"


def recognize_song_online(audio_path):
    """Identify a song using AudD's online recognition API."""

    if not AUDD_API_KEY:
        raise RuntimeError("AudD API key is missing.")

    with open(audio_path, "rb") as audio_file:
        response = requests.post(
            AUDD_URL,
            data={
                "api_token": AUDD_API_KEY,
                "return": "spotify,apple_music",
            },
            files={"file": audio_file},
            timeout=30,
        )

    response.raise_for_status()
    data = response.json()

    if data.get("status") != "success":
        raise RuntimeError(
            f"AudD recognition failed: {data.get('error')}"
        )

    result = data.get("result")

    if not result:
        return None

    return {
        "song": result.get("title"),
        "artist": result.get("artist"),
        "album": result.get("album"),
        "release_date": result.get("release_date"),
        "spotify": result.get("spotify"),
        "apple_music": result.get("apple_music"),
        "source": "AudD",
    }
