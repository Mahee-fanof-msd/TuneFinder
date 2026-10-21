# TuneFinder — Audio Recognition

## Overview

TuneFinder identifies songs using spectrogram-based audio fingerprinting.

The system compares the acoustic characteristics of a microphone recording against fingerprints stored in a local SQLite database.

If no suitable local match is found, the application attempts online recognition using AudD.

## Audio Ingestion

The ingestion pipeline processes songs before they can be recognized locally.

### Step 1: Load Audio

Audio files are loaded from the configured local songs directory.

### Step 2: Divide Audio Into Chunks

Each song is divided into overlapping segments.

Current ingestion parameters:

| Parameter | Value |
|---|---|
| Chunk duration | 8 seconds |
| Step size | 4 seconds |
| Overlap | 4 seconds |

Example:

```text
Chunk 1:  0–8 seconds
Chunk 2:  4–12 seconds
Chunk 3:  8–16 seconds
Chunk 4: 12–20 seconds
```

Overlapping chunks improve coverage across the full song.

## Spectrogram Generation

The audio waveform is transformed into a time-frequency representation.

A spectrogram describes how frequency energy changes over time.

The fingerprinting implementation uses spectral analysis to identify prominent frequency peaks.

## Peak Detection

Significant peaks are extracted from the spectrogram.

Each detected peak has information such as:

- Frequency.
- Time position.
- Spectral magnitude.

## Peak Pairing

Selected peaks are paired using an anchor-target approach.

Example:

```text
Anchor peak:
Frequency = 500 Hz
Time = 2 seconds

Target peak:
Frequency = 800 Hz
Time = 4 seconds

Time difference = 2 seconds
```

The frequency pair and time difference contribute to the fingerprint hash.

## Fingerprint Generation

Conceptually, a fingerprint is based on:

```text
Hash = H(frequency_1, frequency_2, time_difference)
```

The fingerprint is associated with a timestamp and a song identifier.

These values are stored in SQLite.

## Recognition Process

When a user records music:

1. Streamlit captures microphone audio.
2. The recording duration is validated.
3. FastAPI receives the audio.
4. The fingerprinting service extracts acoustic fingerprints.
5. Fingerprint hashes are searched in SQLite.
6. Matching timestamps are compared.
7. Consistent timestamp alignments are counted.
8. The strongest acceptable match is selected.

## Timestamp Offset Matching

A song can be recognized even when the recording begins in the middle of the original track.

For example:

```text
Database fingerprint timestamp: 72 seconds
Recording fingerprint timestamp:  2 seconds

Estimated recording start: 70 seconds
```

Many fingerprints agreeing on the same offset provide evidence of a match.

This is more reliable than comparing only the beginning of a song.

## Local Recognition Example

```text
Microphone Recording
         |
         v
Generate Fingerprints
         |
         v
Search SQLite
         |
         v
Find Matching Hashes
         |
         v
Calculate Time Offsets
         |
         v
Count Consistent Matches
         |
         v
Identify Song
```

## AudD Fallback

If the local database cannot identify the recording, TuneFinder attempts recognition using AudD.

AudD may recognize songs that are not present in the local SQLite catalog.

However, AudD recognition is not guaranteed.

## Recording Duration Validation

The Streamlit application requires a recording of at least 10 seconds.

For shorter recordings:

- A warning is displayed.
- The interface waits approximately three seconds.
- The application returns to its home state.
- The microphone input is reset.

## Current Database

The development version has been tested with 30 locally ingested songs.

The SQLite database and commercial audio files are not included in the public repository.

## Limitations

- Only ingested songs can be identified locally.
- Background noise can affect peak detection.
- Microphone quality affects recognition.
- Audio transformations may reduce fingerprint overlap.
- Online fallback depends on AudD's recognition coverage.
- Fingerprint thresholds affect false positives and missed matches.

## Future Improvements

- Improve noise tolerance.
- Expand the local catalog.
- Benchmark recognition accuracy.
- Add automated recognition tests.
- Improve ingestion performance.
- Add configurable recognition thresholds.
    