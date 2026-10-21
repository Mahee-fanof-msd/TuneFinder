# TuneFinder — Music Recommendations and Discovery

## Overview

TuneFinder provides two distinct music exploration features:

1. Audio-based similar-song recommendations.
2. Natural-language music discovery.

These features use different services and should not be confused with song identification.

## Audio-Based Recommendations

TuneFinder integrates the Cyanite API for music similarity analysis.

The user can submit recorded audio for analysis and request related music.

### Recommendation Flow

```text
User Audio
    |
    v
Streamlit
    |
    v
FastAPI
    |
    v
Cyanite API
    |
    v
Audio Analysis
    |
    v
Similar Track Search
    |
    v
Recommendation Results
    |
    v
Streamlit Display
```

### Recommendation Output

The application can display up to five similar-song recommendations.

Spotify listening links are included when available.

### API Operations

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/recommend` | Submit audio |
| GET | `/recommend/{track_id}` | Check analysis |
| GET | `/recommend/{track_id}/similar` | Retrieve similar songs |

### Limitations

- Recommendations depend on Cyanite's catalog.
- API access and usage limits may apply.
- Audio analysis may require processing time.
- Not every recommendation will have a Spotify link.

## Natural-Language Music Discovery

The discovery feature allows users to describe the music they want.

Example:

```text
Telugu romantic songs featuring Nani in 2026
```

The application uses Groq and Tavily to discover candidate songs and verify available information.

## Discovery Pipeline

```text
User Music Preference
         |
         v
Streamlit
         |
         v
FastAPI /discover
         |
         v
Tavily Web Search
         |
         v
Groq Candidate Analysis
         |
         v
Song Verification
         |
         v
Verified / Unverified Results
         |
         v
Streamlit Display
```

## Tavily

Tavily provides web search results relevant to the user's request.

Search results may include information about:

- Song titles.
- Artists.
- Film soundtracks.
- Release dates.
- Music platform listings.

## Groq

Groq provides access to language models used to interpret search information and propose candidate recommendations.

The language model is not treated as an authoritative music catalog.

Its suggestions must be verified.

## Recommendation Verification

The verification layer checks available evidence about proposed songs.

Relevant attributes can include:

- Song identity.
- Artist identity.
- Release year.
- Film association.
- Relevance to the requested preference.

Verification quality depends on the available source information.

## Verified and Unverified Results

TuneFinder separates results into two categories.

### Verified Recommendations

Candidates that satisfy the application's verification checks.

### Unverified Candidates

Possible matches that cannot be fully confirmed.

This separation reduces the risk of presenting unsupported music recommendations as established facts.

## Example User Requests

```text
Romantic Telugu songs from 2026

Songs similar to a recorded melody

Popular movie songs featuring Nani

Energetic workout music

Recent romantic songs by Anirudh
```

## Recognition vs. Recommendation vs. Discovery

| Feature | Main Technology | Purpose |
|---|---|---|
| Local recognition | Audio fingerprinting + SQLite | Identify indexed songs |
| Online recognition | AudD | Identify songs using an external service |
| Similar-song recommendations | Cyanite | Find musically similar tracks |
| Natural-language discovery | Groq + Tavily | Find songs matching text preferences |

## Limitations

- Recommendations are dependent on external APIs.
- Search results may contain inaccurate metadata.
- Language models can generate incorrect candidates.
- Verification may be incomplete.
- External services have quotas and rate limits.

## Future Improvements

- Improve music metadata verification.
- Support additional recommendation sources.
- Add recommendation feedback.
- Cache verified discovery results.
- Expand multilingual music discovery.
- Introduce recommendation quality benchmarks.