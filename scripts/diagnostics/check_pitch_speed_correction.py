
from pathlib import Path

import librosa
import numpy as np

from app.fingerprinting.fingerprinter import AudioFingerprint
from app.fingerprinting.database import FingerprintDB
from app.fingerprinting.matcher import FingerprintMatcher


# Actual sped-up edit recorded from YouTube
AUDIO_PATH = Path(
    "data/recordings/"
    "recorded_audio_20261014_142950_048429.wav"
)

SAMPLE_RATE = 22050

# Test plausible speed/pitch transformations
SPEED_FACTORS = [
    1.0,
    1.10,
    1.15,
    1.20,
    1.25,
    1.30,
    1.40,
    1.50,
]

if not AUDIO_PATH.exists():
    raise SystemExit(f"Audio file not found: {AUDIO_PATH}")


waveform, sample_rate = librosa.load(
    str(AUDIO_PATH),
    sr=SAMPLE_RATE,
    mono=True
)

fingerprinter = AudioFingerprint()
db = FingerprintDB()

try:
    matcher = FingerprintMatcher(db)

    print("\n--- Pitch + Speed Correction Test ---")

    for speed in SPEED_FACTORS:

        print(f"\nTesting assumed playback speed: {speed}x")

        if speed == 1.0:
            corrected = waveform
        else:
            # Slowing the waveform this way changes
            # both duration and pitch.
            corrected_length = round(len(waveform) * speed)

            corrected = librosa.resample(
                waveform,
                orig_sr=corrected_length,
                target_sr=len(waveform)
            )

        fingerprints = fingerprinter.create_fingerprints(
            corrected,
            sample_rate
        )

        result = matcher.match(fingerprints)

        if result:
            print("Song Found!")
            print("Song:", result["song"])
            print("Assumed speed:", speed)
            print("Start time:", result["start_time"])
            print("Aligned matches:", result["aligned_matches"])
            break

        print("No confident match")

finally:
    db.close()
