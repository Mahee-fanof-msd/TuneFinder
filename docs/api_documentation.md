# TuneFinder — API Documentation

## Overview

TuneFinder uses FastAPI to expose REST endpoints for music recognition, recommendations, and discovery.

The Streamlit frontend (`frontend/streamlit_app.py`) communicates with these endpoints using HTTP. All endpoints are defined in `app/main.py`.

## Base URL

For local development:

```text
http://127.0.0.1:8000
```

The frontend reads this address from `API_URL` in the `.env` file.

## Starting the Backend

From the project root, with the virtual environment activated:

```powershell
python -m uvicorn app.main:app --reload
```

## Interactive API Documentation

FastAPI automatically provides Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Open this URL while the backend is running to inspect the exact request and response schemas.

## API Endpoint Summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Basic API information |
| GET | `/health` | Check that the backend is running |
| POST | `/recognize` | Recognize recorded audio |
| POST | `/recommend` | Submit audio for Cyanite analysis |
| GET | `/recommend/{track_id}` | Retrieve analysis status |
| GET | `/recommend/{track_id}/similar` | Retrieve similar tracks |
| POST | `/discover` | Discover songs from natural-language preferences |
| POST | `/cyanite/webhook` | Receive Cyanite analysis notifications |

## 1. Health Check

**Endpoint:** `GET /health`

### Purpose

Confirms that the FastAPI backend is running. Useful as a first check before testing other endpoints.

## 2. Recognize Song

**Endpoint:** `POST /recognize`

### Purpose

Identifies a song from uploaded audio.

### Processing

1. Receive audio.
2. Reject recordings shorter than 10 seconds with an `invalid_audio` status.
3. Generate fingerprints.
4. Search the local SQLite database, including altered playback speeds.
5. Return a local match when found.
6. Otherwise, attempt AudD recognition.
7. Return the recognition result.

### Example Request

```bash
curl -X POST \
  http://127.0.0.1:8000/recognize \
  -F "audio=@recording.wav"
```

The Streamlit application uploads recorded audio using multipart form data.

The exact form field name and response structure should be confirmed in Swagger UI.

## 3. Submit Recommendation Audio

**Endpoint:** `POST /recommend`

### Purpose

Submits audio to Cyanite for similarity analysis and returns a `track_id` used by the next two endpoints.

## 4. Retrieve Analysis

**Endpoint:** `GET /recommend/{track_id}`

### Purpose

Retrieves the analysis status of a track submitted to Cyanite.

The `track_id` path parameter identifies the submitted track.

## 5. Retrieve Similar Songs

**Endpoint:** `GET /recommend/{track_id}/similar`

### Purpose

Retrieves up to five similar-song recommendations for an analyzed track, with Spotify links when available.

Recommendations depend on Cyanite availability and analysis results.

## 6. Cyanite Webhook

**Endpoint:** `POST /cyanite/webhook`

### Purpose

Receives notifications from Cyanite when an analysis is finished.

The Cyanite API does the analysis work, and this webhook only reports when the result is ready. If the Cyanite account has reached its plan limit, no analysis runs and the webhook is never called.

## 7. Discover Music

**Endpoint:** `POST /discover`

### Purpose

Accepts a natural-language music preference and coordinates music discovery using Tavily and Groq.

### Example Preference

```text
Telugu romantic songs featuring Nani in 2026
```

### Processing

1. Receive the preference.
2. Search for relevant information with Tavily.
3. Analyze candidate songs with Groq.
4. Verify available song metadata.
5. Separate verified results and possible matches.
6. Return structured discovery results, including sources when available.

The exact request body should be confirmed in Swagger UI.

## HTTP Methods

### POST

Used when the client submits information for processing, such as audio or music preferences.

### GET

Used when the client retrieves status, analysis results, or recommendations.

## Data Formats

TuneFinder uses:

- Multipart form data for audio uploads.
- JSON for structured API communication.

## API Errors

Potential errors include:

| HTTP Status | Meaning |
|---|---|
| 400 | Invalid request |
| 404 | Resource not found |
| 422 | Request validation failure |
| 429 | External API rate limit |
| 500 | Internal server error |
| 502 / 503 | Upstream service or availability failure |

These are general HTTP meanings. Actual status codes depend on the implementation.

## API Security

- Store credentials in the `.env` file, never in code.
- Exclude `.env` from Git.
- Validate uploaded files.
- Avoid exposing external service credentials to the frontend.
- Protect sensitive information in logs.

## Testing with Swagger UI

1. Start FastAPI.
2. Open `http://127.0.0.1:8000/docs`.
3. Select an endpoint.
4. Click **Try it out**.
5. Supply the required parameters.
6. Click **Execute**.
7. Inspect the response.

## Future API Improvements

- Standardized error responses.
- Request size limits.
- Automated API tests for each endpoint.
- Rate limiting.
- API versioning.
- Authentication for deployed environments.