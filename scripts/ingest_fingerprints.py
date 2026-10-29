from pathlib import Path

import librosa

from app.audio.chunker import AudioChunker
from app.config import SAMPLE_RATE, SONGS_DIR
from app.fingerprinting.fingerprinter import AudioFingerprint
from app.fingerprinting.database import FingerprintDB


SONGS_FOLDER = SONGS_DIR

chunker = AudioChunker(chunk_duration=8, step_size=4)
fingerprinter = AudioFingerprint()

song_files = sorted(SONGS_FOLDER.glob("*.mp3"))

print("Songs found:", len(song_files))

if not song_files:
    raise SystemExit("No MP3 files found in data/songs")

db = FingerprintDB()

try:
    for song_path in song_files:
        song_name = song_path.stem

        print("\n-----------------------------")
        print("Processing:", song_name)

        # Load and resample to 22050 Hz
        waveform, sample_rate = librosa.load(
            str(song_path),
            sr=SAMPLE_RATE,
            mono=True
        )

        # Create overlapping 8-second chunks
        chunk_samples = int(8 * sample_rate)
        step_samples = int(4 * sample_rate)

        total_fingerprints = 0

        for start in range(
            0,
            len(waveform) - chunk_samples + 1,
            step_samples
        ):
            end = start + chunk_samples

            chunk_waveform = waveform[start:end]
            chunk_start_time = start / sample_rate

            fingerprints = fingerprinter.create_fingerprints(
                chunk_waveform,
                sample_rate
            )

            # Convert timestamps to full-song positions
            for fp in fingerprints:
                fp["timestamp"] += chunk_start_time

            db.insert_fingerprints(
                song_name,
                fingerprints
            )

            total_fingerprints += len(fingerprints)

        print(
            "Stored fingerprints:",
            total_fingerprints
        )

        print(
            "Successfully processed:",
            song_name
        )

finally:
    db.close()

print("\nFingerprint ingestion completed!")
