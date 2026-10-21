
# 🎵 TuneFinder
### Intelligent Music Recognition and Recommendation System

TuneFinder is a Python-based music recognition and discovery application inspired by Shazam. It identifies songs from microphone recordings using a local audio fingerprint database, falls back to online recognition, recommends similar songs, and supports natural-language music discovery.

## Features

- Audio recognition using spectral fingerprinting
- Local SQLite fingerprint database
- AudD API fallback for songs not identified locally
- Cyanite API integration for similar-song recommendations
- Natural-language song discovery using Groq and Tavily
- Music recommendation verification
- Interactive Streamlit interface
- FastAPI backend
- Automatic microphone reset for recordings shorter than 10 seconds

## Technology Stack

| Component | Technology |
|-----------|------------|
| Programming Language | Python |
| Backend | FastAPI |
| Frontend | Streamlit |
| Local Database | SQLite |
| Audio Processing | Librosa, NumPy, SciPy |
| Music Recognition | Spectral Fingerprinting, AudD |
| Similarity Recommendations | Cyanite API |
| Music Discovery | Groq, Tavily |
| API Communication | REST, JSON |

## System Architecture

```text
                   USER
                     |
               Streamlit UI
                     |
              Microphone Audio
                     |
          Minimum 10-Second Check
                     |
                FastAPI
                     |
             Recognition Service
                     |
           Audio Fingerprinting
                     |
              SQLite Search
                     |
              Match Found?
                /       \
              YES        NO
               |          |
        Local Result    AudD API
               |          |
               +-----+----+
                     |
             Recognition Result
                     |
               User Options
                /    |    \
               /     |     \
         Similar   Discover   Exit
          Songs     Music
            |         |
         Cyanite   Groq + Tavily
            |         |
       Spotify     Verification
       Results       Results
```

## Audio Fingerprinting

TuneFinder uses spectrogram-based audio fingerprinting rather than relying solely on metadata.

### Ingestion Process

1. Load audio files from the local songs directory.
2. Divide songs into overlapping 8-second chunks with a 4-second step.
3. Generate spectrograms.
4. Detect significant frequency peaks.
5. Pair peaks using their frequencies and time differences.
6. Generate fingerprint hashes.
7. Store fingerprints and timestamps in SQLite.

### Recognition Process

1. Capture audio using the microphone.
2. Generate fingerprints from the recorded audio.
3. Search the local SQLite fingerprint database.
4. Match fingerprint hashes and compare time offsets.
5. Identify the song with the strongest consistent alignment.
6. If local recognition fails, attempt recognition using AudD.

Fingerprinting allows TuneFinder to identify matching segments from different positions within a song.

## Current Local Database

The development database has been tested with 30 locally ingested songs.

The downloaded songs and generated SQLite database are excluded from the public repository. Users can create their own local fingerprint database.

## Recording Validation

The application requires at least 10 seconds of recorded audio.

If a recording is shorter than 10 seconds:

- A warning is displayed.
- The application waits 3 seconds.
- The interface automatically returns to the home screen.
- The microphone recorder is reset.

Valid recordings proceed to song recognition.

## Music Recommendations

### Similar Songs — Cyanite

TuneFinder can submit recorded audio to Cyanite for music analysis and retrieve similar songs from its recommendation service.

The application displays up to five similar-song recommendations, with Spotify listening links when available.

### Natural-Language Music Discovery

Users can search using descriptions such as:

"Telugu romantic songs featuring Nani in 2026"

The discovery pipeline uses Groq and Tavily to propose and verify relevant songs.

Results are separated into verified recommendations and possible matches when verification is incomplete.

## API Endpoints

The Streamlit frontend uses the following FastAPI routes:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /recognize | Identify a recorded song |
| POST | /recommend | Submit audio for similarity analysis |
| GET | /recommend/{track_id} | Check Cyanite analysis |
| GET | /recommend/{track_id}/similar | Retrieve similar songs |
| POST | /discover | Discover songs from text preferences |

## Local Setup

### Prerequisites

- Python
- Git
- Internet connection for external APIs
- Microphone access
- API credentials for enabled external services

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/TuneFinder.git
cd TuneFinder
```

### Create Virtual Environment

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Install Dependencies

```powershell
pip install -r requirements.txt
```

### Configure API Credentials

Create a local `.env` file and configure the API credentials expected by the backend.

Never commit real API keys to GitHub.

### Ingest Local Songs

Place audio files in the project's configured songs directory.

Run:

```powershell
python -m scripts.ingest_fingerprints
```

### Start FastAPI

```powershell
uvicorn app.main:app --reload
```

### Start Streamlit

In a separate terminal:

```powershell
streamlit run streamlit_app.py
```

The Streamlit interface normally opens at:

http://localhost:8501

FastAPI documentation is available at:

http://127.0.0.1:8000/docs

## Testing

To test the recognition system:

1. Start the backend and frontend.
2. Play a song already indexed in SQLite.
3. Record at least 10 seconds through the microphone.
4. Click Identify Song.
5. Check the song identification and source.
6. Optionally explore recommendations or music discovery.

## Limitations

- Local recognition is limited to songs indexed in SQLite.
- Microphone noise and audio quality can affect recognition.
- Online recognition depends on AudD coverage.
- Similar-song recommendations depend on Cyanite availability.
- Natural-language discovery depends on external API availability and verification quality.
- API quotas and rate limits may apply.

## Future Improvements

- Expand the local song catalog.
- Improve recognition in noisy environments.
- Add automated fingerprint ingestion workflows.
- Add automated tests and CI.
- Containerize the application using Docker.
- Deploy the frontend and backend.

## Privacy and Copyright

Downloaded commercial music and local audio databases are not distributed with this repository.

Users are responsible for obtaining appropriate rights to any audio they process or distribute.

API credentials and local recordings should remain private.

## Technical Documentation

For detailed information about TuneFinder, refer to the following guides:

| Document | Description |
|---|---|
| [System Architecture](docs/architecture.md) | Application components, services, and data flow |
| [Audio Recognition](docs/audio_recognition.md) | Fingerprinting, chunking, peak matching, and recognition |
| [Recommendation System](docs/recommendation_system.md) | Cyanite recommendations and Groq/Tavily discovery |
| [API Documentation](docs/api_documentation.md) | FastAPI endpoints and integration details |
| [Setup Guide](docs/setup_guide.md) | Installation, configuration, and running the application |

## Project Status

Working local prototype with song recognition, online fallback, audio-based recommendations, and natural-language music discovery.
