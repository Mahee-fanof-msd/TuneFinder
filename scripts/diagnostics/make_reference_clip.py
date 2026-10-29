
from pathlib import Path

import librosa
import soundfile as sf


song_path = (
    "data/songs/"
    "David Kushner - Daylight (Official Music Video).mp3"
)

start_time = 186
duration = 8

waveform, sample_rate = librosa.load(
    song_path,
    sr=22050,
    mono=True
)

start_sample = int(start_time * sample_rate)
end_sample = int((start_time + duration) * sample_rate)

reference_clip = waveform[start_sample:end_sample]

output_path = Path("data/test_clips/daylight_reference_186.wav")

sf.write(
    str(output_path),
    reference_clip,
    sample_rate
)

print("Reference clip saved:", output_path)
print("Start time:", start_time)
print("Duration:", len(reference_clip) / sample_rate)
