import librosa

from app.config import MIN_CLIP_SECONDS, SAMPLE_RATE

from app.fingerprinting.fingerprinter import AudioFingerprint
from app.fingerprinting.database import FingerprintDB
from app.fingerprinting.matcher import FingerprintMatcher


class SongRecognitionService:

    def __init__(self):
        self.fingerprinter = AudioFingerprint()

        # Playback speeds to investigate automatically.
        # 1.0x is tested first.
        self.playback_speeds = [
            1.0,
            1.25,
            0.75,
            1.10,
            0.90,
            1.50,
            0.50,
        ]

    def recognize(self, audio_path):

        waveform, sample_rate = librosa.load(
            audio_path,
            sr=SAMPLE_RATE,
            mono=True
        )

        duration = len(waveform) / sample_rate

        if duration < MIN_CLIP_SECONDS:
            return {
                "status": "invalid_audio",
                "message": f"Audio must be at least {MIN_CLIP_SECONDS} seconds long."
            }

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
                    # Compensate for the estimated playback speed.
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
                    return {
                        "status": "song_found",
                        "message": "Song Found",
                        "song": result["song"],
                        "start_time": result["start_time"],
                        "detected_playback_speed": playback_speed,
                        "aligned_matches": result["aligned_matches"]
                    }

        finally:
            db.close()

        return {
            "status": "song_not_found",
            "message": "No Song Found",
            "recommendations_available": True
        }
