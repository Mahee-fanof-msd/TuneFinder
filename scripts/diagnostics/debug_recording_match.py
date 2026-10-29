
from pathlib import Path
from collections import Counter, defaultdict

import librosa

from app.fingerprinting.fingerprinter import AudioFingerprint
from app.fingerprinting.database import FingerprintDB
from app.fingerprinting.matcher import FingerprintMatcher


# Step 1: Find the latest microphone recording
recordings = [
    Path("data/test_clips/daylight_speed_corrected.wav")
]

if not recordings:
    raise SystemExit("No microphone recordings found.")

audio_path = max(
    recordings,
    key=lambda path: path.stat().st_mtime
)

print("\n--------------------------------")
print("Testing recording:", audio_path.name)


# Step 2: Load audio at the database sample rate
waveform, sample_rate = librosa.load(
    str(audio_path),
    sr=22050,
    mono=True
)

duration = len(waveform) / sample_rate

print("Recording duration:", round(duration, 2), "seconds")
print("Sample rate:", sample_rate)


# Step 3: Generate fingerprints
fingerprinter = AudioFingerprint()

fingerprints = fingerprinter.create_fingerprints(
    waveform,
    sample_rate
)

print("Generated fingerprints:", len(fingerprints))


# Step 4: Connect to SQLite
db = FingerprintDB()

try:
    # Count query fingerprints whose hashes exist in SQLite
    matched_hashes = 0

    # Store votes for each song and time offset
    offset_votes = defaultdict(Counter)

    for fp in fingerprints:

        fingerprint_hash = fp["hash"]
        clip_time = fp["timestamp"]

        db.cursor.execute(
            """
            SELECT song_name, timestamp
            FROM fingerprints
            WHERE hash = ?
            """,
            (fingerprint_hash,)
        )

        matches = db.cursor.fetchall()

        if matches:
            matched_hashes += 1

        for song_name, song_time in matches:

            offset = round(
                song_time - clip_time,
                1
            )

            offset_votes[song_name][offset] += 1

    # Step 5: Display hash match statistics
    print("\n--- Fingerprint Statistics ---")

    print("Fingerprints found in SQLite:", matched_hashes)

    if fingerprints:
        match_percentage = (
            matched_hashes / len(fingerprints)
        ) * 100
    else:
        match_percentage = 0

    print(
        "Hash match percentage:",
        round(match_percentage, 2),
        "%"
    )

    # Step 6: Run existing production matcher
    matcher = FingerprintMatcher(db)

    result = matcher.match(fingerprints)

    print("\nRecognition result:", result)

    # Step 7: Display top exact offsets
    print("\n--- Top Matching Offsets (0.1 sec) ---")

    if not offset_votes:
        print("No matching fingerprints found.")

    for song_name, offsets in offset_votes.items():

        print("\nSong:", song_name)

        for offset, votes in offsets.most_common(5):
            print(
                f"Offset: {offset:.1f} seconds "
                f"| Aligned matches: {votes}"
            )

    # Step 8: Analyze broader offset tolerance
    print("\n--- Offset Tolerance Analysis (0.5 sec) ---")

    for song_name, offsets in offset_votes.items():

        grouped_votes = Counter()

        for offset, votes in offsets.items():

            # Group offsets into half-second buckets
            bucket = round(offset * 2) / 2

            grouped_votes[bucket] += votes

        print("\nSong:", song_name)

        for offset, votes in grouped_votes.most_common(5):

            print(
                f"Approximate offset: {offset:.1f} sec "
                f"| Grouped matches: {votes}"
            )

finally:
    db.close()
