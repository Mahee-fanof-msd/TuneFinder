
from app.audio.microphone import MicrophoneRecorder

recorder = MicrophoneRecorder(duration=8)

audio_path = recorder.record()

print("Microphone audio saved:", audio_path)
