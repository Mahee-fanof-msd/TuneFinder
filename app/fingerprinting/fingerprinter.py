
import hashlib

import librosa
import numpy as np
from scipy.ndimage import maximum_filter


class AudioFingerprint:

    def __init__(
        self,
        n_fft=2048,
        hop_length=256,
        peak_neighborhood=15,
        amplitude_threshold=-35,
        fan_value=10,
        min_time_delta=0.1,
        max_time_delta=2.0,
    ):
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.peak_neighborhood = peak_neighborhood
        self.amplitude_threshold = amplitude_threshold
        self.fan_value = fan_value
        self.min_time_delta = min_time_delta
        self.max_time_delta = max_time_delta

    def create_fingerprints(self, waveform, sample_rate):

        # Convert waveform to mono if necessary
        waveform = np.asarray(waveform, dtype=np.float32)

        if waveform.ndim > 1:
            waveform = np.mean(waveform, axis=1)

        # Skip empty or silent recordings
        if len(waveform) == 0:
            return []

        if np.max(np.abs(waveform)) < 1e-5:
            return []

        # Generate spectrogram
        stft = librosa.stft(
            waveform,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )

        magnitude = np.abs(stft)

        spectrogram_db = librosa.amplitude_to_db(
            magnitude,
            ref=np.max
        )

        # Detect local frequency/time peaks
        local_max = maximum_filter(
            spectrogram_db,
            size=self.peak_neighborhood
        )

        peak_mask = (
            (spectrogram_db == local_max)
            & (spectrogram_db > self.amplitude_threshold)
        )

        frequency_bins, time_bins = np.where(peak_mask)

        peaks = sorted(
            zip(time_bins, frequency_bins),
            key=lambda peak: peak[0]
        )

        fingerprints = []

        for i, (time1, freq1) in enumerate(peaks):

            pairs_created = 0

            for time2, freq2 in peaks[i + 1:]:

                delta_frames = time2 - time1

                delta_seconds = (
                    delta_frames * self.hop_length / sample_rate
                )

                if delta_seconds < self.min_time_delta:
                    continue

                if delta_seconds > self.max_time_delta:
                    break

                # Pair two frequency peaks and their time difference
                fingerprint_data = (
                    f"{freq1}|{freq2}|{delta_frames}"
                )

                fingerprint_hash = hashlib.sha1(
                    fingerprint_data.encode()
                ).hexdigest()[:20]

                timestamp = (
                    time1 * self.hop_length / sample_rate
                )

                fingerprints.append({
                    "hash": fingerprint_hash,
                    "timestamp": float(timestamp)
                })

                pairs_created += 1

                if pairs_created >= self.fan_value:
                    break

        return fingerprints
