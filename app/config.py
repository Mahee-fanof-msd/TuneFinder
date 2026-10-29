"""Central settings for TuneFinder.

All paths are built from the project root, so the app works no matter
which folder you launch it from.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

# Data locations
DATA_DIR = PROJECT_ROOT / "data"
SONGS_DIR = DATA_DIR / "songs"
TEST_CLIPS_DIR = DATA_DIR / "test_clips"
RECORDINGS_DIR = DATA_DIR / "recordings"
FINGERPRINT_DB_PATH = Path(
    os.getenv("FINGERPRINT_DB_PATH", DATA_DIR / "db" / "fingerprints.db")
)

# Audio settings
SAMPLE_RATE = 22050
MIN_CLIP_SECONDS = 8

# Backend URL used by the Streamlit frontend
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# External API keys (used by app/integrations)
AUDD_API_KEY = os.getenv("AUDD_API_KEY", "")
CYANITE_API_KEY = os.getenv("CYANITE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
