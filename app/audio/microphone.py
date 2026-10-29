import time
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from app.config import RECORDINGS_DIR


class MicrophoneRecorder:

    def __init__(
        self,
        duration=8,
        sample_rate=48000,
        device=9
    ):
        self.duration = duration
        self.sample_rate = sample_rate
        self.device = device

    def record(self, output_path=None):

        folder = RECORDINGS_DIR
        folder.mkdir(parents=True, exist_ok=True)

        # Generate a unique filename for each recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        audio_path = folder / f"recorded_audio_{timestamp}.wav"

        print("\nUsing microphone:")
        print(sd.query_devices(self.device)["name"])

        print("\nRecording starts in 3 seconds...")

        for seconds in range(3, 0, -1):
            print(seconds)
            time.sleep(1)

        print("\nRecording started!")

        recording = sd.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=2,
            dtype="float32",
            device=self.device
        )

        sd.wait()

        peak = float(np.max(np.abs(recording)))
        rms = float(np.sqrt(np.mean(recording ** 2)))

        print("Peak amplitude:", round(peak, 4))
        print("RMS volume:", round(rms, 4))

        sf.write(
            str(audio_path),
            recording,
            self.sample_rate
        )

        print("Recording completed!")
        print("Saved to:", audio_path)

        return str(audio_path)
