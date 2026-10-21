import io
import librosa


class AudioProcessor:

    def process(self, audio_bytes):
        audio_stream = io.BytesIO(audio_bytes)

        waveform, sample_rate = librosa.load(
            audio_stream,
            sr=22050,
            mono=True
        )

        return waveform, sample_rate