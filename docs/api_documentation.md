# TuneFinder — API Documentation

## Overview

TuneFinder uses FastAPI to expose REST endpoints for music recognition, recommendations, and discovery.

The Streamlit frontend communicates with these endpoints using HTTP.

## Base URL

For local development:

```text
http://127.0.0.1:8000
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
| POST | `/recognize` | Recognize recorded audio |
| POST | `/recommend` | Submit audio for Cyanite analysis |
| GET | `/recommend/{track_id}` | Retrieve analysis information |
| GET | `/recommend/{track_id}/similar` | Retrieve similar tracks |
| POST | `/discover` | Discover songs from natural-language preferences |

## 1. Recognize Song

**Endpoint:** `POST /recognize`

### Purpose

Identifies a song from uploaded audio.

### Processing

1. Receive audio.
2. Generate fingerprints.
3. Search the local SQLite database.
4. Return a local match when found.
5. Otherwise, attempt AudD recognition.
6. Return the recognition result.

### Example Request

```bash
curl -X POST \
  http://127.0.0.1:8000/recognize \
  -F "audio=@recording.wav"
```

The Streamlit application uploads recorded audio using multipart form data.

The exact response structure should be inspected in Swagger UI.

## 2. Submit Recommendation Audio

**Endpoint:** `POST /recommend`

### Purpose

Submits audio for Cyanite similarity analysis.

The request and response schemas depend on the current FastAPI implementation.

## 3. Retrieve Analysis

**Endpoint:** `GET /recommend/{track_id}`

### Purpose

Retrieves information about an audio track submitted for analysis.

The `track_id` path parameter identifies the submitted track.

## 4. Retrieve Similar Songs

**Endpoint:** `GET /recommend/{track_id}/similar`

### Purpose

Retrieves similar-song recommendations associated with an analyzed track.

Recommendations depend on Cyanite availability and analysis results.

## 5. Discover Music

**Endpoint:** `POST /discover`

### Purpose

Accepts a natural-language music preference and coordinates music discovery.

### Example Preference

```text
Telugu romantic songs featuring Nani in 2026
```

### Processing

1. Receive the preference.
2. Search for relevant information.
3. Analyze candidate songs.
4. Verify available song metadata.
5. Separate verified and unverified results.
6. Return structured discovery results.

The exact request body should be obtained from Swagger UI.

## HTTP Methods

### POST

Used when the client submits information for processing, such as audio or music preferences.

### GET

Used when the client retrieves previously created analysis results or recommendations.

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

- Store credentials in environment variables.
- Never hardcode API keys.
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
- Automated API tests.
- Rate limiting.
- API versioning.
- Authentication for deployed environments.