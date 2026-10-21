# TuneFinder — System Architecture

## Overview

TuneFinder is a music recognition, recommendation, and discovery application developed using Python, FastAPI, Streamlit, and SQLite.

The application supports three main operations:

1. Song identification using audio fingerprinting and AudD.
2. Similar-song recommendations using Cyanite.
3. Natural-language music discovery using Groq and Tavily.

## High-Level Architecture

```text
                       USER
                         |
                   Streamlit UI
                         |
                User Selects Action
                         |
          +--------------+--------------+
          |              |              |
      Identify       Similar Songs   Discover Music
          |              |              |
      /recognize      /recommend      /discover
          |              |              |
          +--------------+--------------+
                         |
                    FastAPI Backend
                         |
          +--------------+--------------+
          |              |              |
    Recognition       Cyanite       Groq + Tavily
      Service         Service         Services
          |              |              |
    Fingerprinting    Audio Analysis   Search and
          |              |             Verification
      SQLite DB       Similar Tracks    Results
          |
     Match Found?
       /      \
      YES      NO
       |        |
   Local Match  AudD API
       |        |
       +--------+
            |
      Recognition Result
```

## Frontend Layer

The frontend is implemented using Streamlit.

Responsibilities include:

- Capturing microphone recordings.
- Validating the minimum recording duration.
- Sending HTTP requests to FastAPI.
- Displaying identified songs.
- Displaying similar-song recommendations.
- Accepting natural-language music preferences.
- Displaying verified and unverified music discovery results.

## Backend Layer

FastAPI manages communication between the frontend and the application's services.

The backend is responsible for receiving requests, validating inputs, coordinating services, and returning JSON responses.

### Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/recognize` | Identify a recorded song |
| POST | `/recommend` | Submit audio for similarity analysis |
| GET | `/recommend/{track_id}` | Retrieve analysis status |
| GET | `/recommend/{track_id}/similar` | Retrieve similar tracks |
| POST | `/discover` | Discover songs using text preferences |

## Local Recognition Layer

The local recognition system uses spectrogram-based audio fingerprinting.

The process involves:

1. Loading audio.
2. Generating a spectrogram.
3. Detecting significant frequency peaks.
4. Creating peak pairs.
5. Generating fingerprint hashes.
6. Searching matching hashes in SQLite.
7. Comparing timestamp offsets.
8. Selecting the strongest consistent match.

## External Recognition Layer

When local fingerprint matching does not identify a song, TuneFinder uses the AudD API as an online recognition fallback.

Recognition success depends on AudD's catalog coverage and recording quality.

## Recommendation Layer

Cyanite is used to analyze audio and retrieve similar-song recommendations.

TuneFinder displays up to five recommendations, including Spotify links when available.

## Music Discovery Layer

The natural-language discovery pipeline uses Groq and Tavily.

Its responsibilities include:

- Interpreting user preferences.
- Searching for relevant music information.
- Generating candidate recommendations.
- Verifying song identities and requested attributes.
- Separating verified recommendations from unverified candidates.

## Data Storage

SQLite stores local audio fingerprints and their associated song information.

The local database supports matching recorded audio against previously ingested songs.

Commercial audio files and generated local databases are excluded from the public repository.

## Communication

The Streamlit frontend communicates with FastAPI using HTTP requests.

FastAPI returns structured JSON responses that the frontend uses to update the interface.

## Architecture Benefits

- Modular service design.
- Local recognition without requiring an online lookup for every song.
- Online recognition fallback.
- Separation of recognition, recommendation, and discovery.
- REST API integration.
- Extensible architecture for future deployment and testing.

## Current Status

TuneFinder is a working local prototype. Its components can be extended with automated testing, monitoring, Docker, and cloud deployment.