
import librosa

song_path = "data/songs/David Kushner - Daylight (Official Music Video).mp3"
recording_path = "data/recordings/recorded_audio.wav"

for label, path in [
    ("Original song", song_path),
    ("Microphone recording", recording_path)
]:
    waveform, sample_rate = librosa.load(
        path,
        sr=None,
        mono=True
    )

    print(f"{label}:")
    print("Sample rate:", sample_rate)
    print("Duration:", round(len(waveform) / sample_rate, 2))
    print()

