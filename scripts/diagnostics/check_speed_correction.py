
from pathlib import Path

import librosa
import soundfile as sf

from app.services.recognition_service import SongRecognitionService


# Recording captured from YouTube at 1.25x playback speed
audio_path = Path(
    "data/recordings/"
    "recorded_audio_20261014_135748_202691.wav"
)

if not audio_path.exists():
    raise SystemExit(f"Recording not found: {audio_path}")


# Load recording
waveform, sample_rate = librosa.load(
    str(audio_path),
    sr=22050,
    mono=True
)

print("\nOriginal recording duration:",
      round(len(waveform) / sample_rate, 2),
      "seconds")


# Slow the recording to compensate for 1.25x playback
corrected_waveform = librosa.effects.time_stretch(
    waveform,
    rate=1 / 1.25
)

corrected_path = Path(
    "data/test_clips/daylight_speed_corrected.wav"
)

sf.write(
    str(corrected_path),
    corrected_waveform,
    sample_rate
)

print(
    "Corrected duration:",
    round(len(corrected_waveform) / sample_rate, 2),
    "seconds"
)


# Test recognition
service = SongRecognitionService()

print("\nTesting original 1.25x recording...")
original_result = service.recognize(str(audio_path))
print("Original result:", original_result)

print("\nTesting speed-corrected recording...")
corrected_result = service.recognize(str(corrected_path))
print("Corrected result:", corrected_result)
