
from app.audio.microphone import MicrophoneRecorder
from app.services.recognition_service import SongRecognitionService


# Initialize microphone and recognition service
recorder = MicrophoneRecorder(duration=8)
recognition_service = SongRecognitionService()


print("\nTuneFinder - Music Recognition")
print("-----------------------------")

# Step 1: Record music from microphone
audio_path = recorder.record(
    "data/recordings/recorded_audio.wav"
)

# Step 2: Recognize recorded music
print("\nIdentifying song...")

result = recognition_service.recognize(audio_path)

# Step 3: Display result
if result["status"] == "song_found":
    print("\nSong Found!")
    print("Song:", result["song"])
    print("Start time:", result["start_time"], "seconds")

elif result["status"] == "song_not_found":
    print("\nNo Song Found")
    print("Would you like recommendations for similar songs?")

else:
    print(result["message"])
