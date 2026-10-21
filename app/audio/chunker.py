import librosa


class AudioChunker:

    def __init__(self, chunk_duration=8, step_size=4):
        self.chunk_duration = chunk_duration
        self.step_size = step_size

    def create_chunks(self, file_path):

        waveform, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True
        )

        chunk_samples = int(self.chunk_duration * sample_rate)
        step_samples = int(self.step_size * sample_rate)

        chunks = []

        for start in range(
            0,
            len(waveform) - chunk_samples + 1,
            step_samples
        ):

            end = start + chunk_samples

            chunk = waveform[start:end]

            chunks.append({
                "waveform": chunk,
                "sample_rate": sample_rate,
                "start_time": start / sample_rate,
                "end_time": end / sample_rate
            })

        return chunks