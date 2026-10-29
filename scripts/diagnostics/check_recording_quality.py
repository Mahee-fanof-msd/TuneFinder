
import librosa
import numpy as np

audio_path = "data/recordings/recorded_audio.wav"

waveform, sample_rate = librosa.load(
    audio_path,
    sr=None,
    mono=True
)

duration = len(waveform) / sample_rate
peak = np.max(np.abs(waveform))
rms = np.sqrt(np.mean(waveform ** 2))

print("Recording duration:", round(duration, 2), "seconds")
print("Sample rate:", sample_rate)
print("Peak amplitude:", round(float(peak), 4))
print("RMS volume:", round(float(rms), 4))

if peak < 0.01:
    print("Warning: Recording is very quiet.")
elif peak >= 0.999:
    print("Warning: Recording may be clipping.")
else:
    print("Recording amplitude is within a reasonable range.")
