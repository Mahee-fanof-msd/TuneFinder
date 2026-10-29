import numpy as np
import librosa


class AudioEmbedding:

    def create_embedding(self, waveform, sample_rate):

        mfcc = librosa.feature.mfcc(
            y=waveform,
            sr=sample_rate,
            n_mfcc=20
        )

        embedding = np.mean(mfcc, axis=1)

        return embedding