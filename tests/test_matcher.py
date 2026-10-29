import numpy as np

from app.fingerprinting.fingerprinter import AudioFingerprint
from app.fingerprinting.matcher import FingerprintMatcher
from tests.conftest import SAMPLE_RATE


def test_finds_song_and_start_time(song_waveform, temp_db):
    fingerprinter = AudioFingerprint()
    temp_db.insert_fingerprints(
        "Test Song",
        fingerprinter.create_fingerprints(song_waveform, SAMPLE_RATE),
    )

    # 10-second clip starting at 12 seconds into the song
    clip = song_waveform[12 * SAMPLE_RATE: 22 * SAMPLE_RATE]
    result = FingerprintMatcher(temp_db).match(
        fingerprinter.create_fingerprints(clip, SAMPLE_RATE)
    )

    assert result is not None
    assert result["song"] == "Test Song"
    assert abs(result["start_time"] - 12) <= 0.5


def test_unknown_audio_returns_none(song_waveform, temp_db):
    fingerprinter = AudioFingerprint()
    temp_db.insert_fingerprints(
        "Test Song",
        fingerprinter.create_fingerprints(song_waveform, SAMPLE_RATE),
    )

    noise = np.random.default_rng(7).normal(size=SAMPLE_RATE * 10).astype(np.float32)
    result = FingerprintMatcher(temp_db).match(
        fingerprinter.create_fingerprints(noise, SAMPLE_RATE)
    )

    assert result is None


def test_empty_fingerprints_returns_none(temp_db):
    assert FingerprintMatcher(temp_db).match([]) is None
