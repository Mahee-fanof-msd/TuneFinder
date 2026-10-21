
import librosa

from app.services.audio_fingerprint import AudioFingerprint
from app.services.fingerprint_db import FingerprintDB
from app.services.fingerprint_matcher import FingerprintMatcher


# Minimum audio duration in seconds
MIN_DURATION = 8

# Audio clips to test
test_clips = [
    "data/test_clips/daylight_test.mp3",
    "data/test_clips/fairytale_test.mp3",
    "data/test_clips/unknown_test.mp3"
]

# Initialize components
fingerprinter = AudioFingerprint()
db = FingerprintDB()

try:
    matcher = FingerprintMatcher(db)

    # Test each audio clip
    for clip_path in test_clips:
        print("\n----------------------------")
        print("Testing:", clip_path)

        # Step 1: Load the complete audio clip
        audio_clip, sample_rate = librosa.load(
            clip_path,
            sr=None,
            mono=True
        )

        # Step 2: Calculate audio duration
        clip_duration = len(audio_clip) / sample_rate

        print("Clip duration:", round(clip_duration, 2), "seconds")

        # Step 3: Reject clips shorter than 8 seconds
        if clip_duration < MIN_DURATION:
            print("Audio must be at least 8 seconds long.")
            continue

        # Step 4: Generate fingerprints for the entire clip
        fingerprints = fingerprinter.create_fingerprints(
            audio_clip,
            sample_rate
        )

        print("Fingerprints generated:", len(fingerprints))

        # Step 5: Match fingerprints against SQLite
        result = matcher.match(fingerprints)

        # Step 6: Display recognition result
        if result is None:
            print("Recognition result: Song not found")
        else:
            print("\nRecognition result:")
            print("Song:", result["song"])
            print("Start time:", result["start_time"], "seconds")
            print("Aligned matches:", result["aligned_matches"])
            print(
                "Unique matching hashes:",
                result["unique_matching_hashes"]
            )

finally:
    # Close database connection
    db.close()
