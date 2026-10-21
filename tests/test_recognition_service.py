
from app.services.song_recognition_service import SongRecognitionService

# Initialize recognition service
service = SongRecognitionService()

# Test known and unknown songs
test_clips = [
    "data/test_clips/daylight_test.mp3",
    "data/test_clips/fairytale_test.mp3",
    "data/test_clips/unknown_test.mp3"
]

for clip in test_clips:
    print("\n----------------------------")
    print("Testing:", clip)

    result = service.recognize(clip)

    if result["status"] == "song_found":
        print("Song Found!")
        print("Song:", result["song"])
        print("Start time:", result["start_time"])

    elif result["status"] == "song_not_found":
        print("No Song Found")
        print("Would you like similar song recommendations?")

    else:
        print(result["message"])
