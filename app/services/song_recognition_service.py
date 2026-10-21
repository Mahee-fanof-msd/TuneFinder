import librosa

from app.services.audio_fingerprint import AudioFingerprint
from app.services.fingerprint_db import FingerprintDB
from app.services.fingerprint_matcher import FingerprintMatcher
from app.services.audd_service import recognize_song_online


class SongRecognitionService:

    def __init__(self):

        self.fingerprinter = AudioFingerprint()

        # Playback speeds to investigate automatically.
        # 1.0x is tested first.
        self.playback_speeds = [
            1.0,
            1.25,
            0.75,
            1.50,
            0.50,
        ]

    def recognize(self, audio_path):

        # STEP 1: Load the recorded audio.
        waveform, sample_rate = librosa.load(
            audio_path,
            sr=22050,
            mono=True
        )

        duration = len(waveform) / sample_rate

        if duration < 10:
            return {
                "status": "invalid_audio",
                "message": "Audio must be at least 10 seconds long."
            }

        # STEP 2: Search local SQLite fingerprints.
        db = FingerprintDB()

        try:
            matcher = FingerprintMatcher(db)

            for playback_speed in self.playback_speeds:

                print(
                    f"Checking playback speed: "
                    f"{playback_speed}x"
                )

                if playback_speed == 1.0:
                    corrected_waveform = waveform

                else:
                    corrected_waveform = (
                        librosa.effects.time_stretch(
                            waveform,
                            rate=1 / playback_speed
                        )
                    )

                fingerprints = (
                    self.fingerprinter.create_fingerprints(
                        corrected_waveform,
                        sample_rate
                    )
                )

                result = matcher.match(fingerprints)

                if result is not None:

                    print(
                        "Song identified using local SQLite."
                    )

                    return {
                        "status": "song_found",
                        "message": "Song Found",
                        "song": result["song"],
                        "start_time": result["start_time"],
                        "detected_playback_speed": playback_speed,
                        "aligned_matches": result["aligned_matches"],
                        "source": "SQLite"
                    }

        finally:
            db.close()

        # STEP 3: Local recognition failed.
        # Try AudD online recognition.
        print(
            "No local match. Checking AudD API..."
        )

        try:
            online_result = recognize_song_online(
                audio_path
            )

            if online_result:

                print(
                    "Song identified using AudD."
                )

                return {
                    "status": "song_found",
                    "message": "Song Found Online",
                    "song": online_result["song"],
                    "artist": online_result["artist"],
                    "album": online_result["album"],
                    "release_date": online_result["release_date"],
                    "spotify": online_result["spotify"],
                    "apple_music": online_result["apple_music"],
                    "source": "AudD"
                }

        except Exception as error:

            print(
                f"AudD recognition error: {error}"
            )

            return {
                "status": "online_recognition_error",
                "message": (
                    "Local recognition failed and online "
                    "recognition is currently unavailable."
                ),
                "recommendations_available": False
            }

        # STEP 4: Neither service identified the song.
        print(
            "No song identified locally or online."
        )

        return {
            "status": "song_not_found",
            "message": "No Song Found",
            "recommendations_available": True
        }