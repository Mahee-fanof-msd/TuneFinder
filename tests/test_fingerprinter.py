import numpy as np

from app.fingerprinting.fingerprinter import AudioFingerprint
from tests.conftest import SAMPLE_RATE


def test_creates_fingerprints_for_music(song_waveform):
    fingerprints = AudioFingerprint().create_fingerprints(song_waveform, SAMPLE_RATE)

    assert len(fingerprints) > 0
    assert {"hash", "timestamp"} <= fingerprints[0].keys()


def test_silence_produces_no_fingerprints():
    silence = np.zeros(SAMPLE_RATE * 8, dtype=np.float32)

    assert AudioFingerprint().create_fingerprints(silence, SAMPLE_RATE) == []


def test_same_audio_gives_same_hashes(song_waveform):
    fingerprinter = AudioFingerprint()
    first = fingerprinter.create_fingerprints(song_waveform, SAMPLE_RATE)
    second = fingerprinter.create_fingerprints(song_waveform, SAMPLE_RATE)

    assert first == second
