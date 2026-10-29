import numpy as np
import pytest

from app.fingerprinting.database import FingerprintDB

SAMPLE_RATE = 22050


@pytest.fixture
def song_waveform():
    """30 seconds of reproducible, peak-rich synthetic 'music'."""
    rng = np.random.default_rng(42)
    t = np.arange(int(30 * SAMPLE_RATE)) / SAMPLE_RATE
    signal = np.zeros_like(t)
    # A new random chord every quarter second gives plenty of spectral peaks
    step = SAMPLE_RATE // 4
    for start in range(0, len(t), step):
        segment = slice(start, start + step)
        for freq in rng.uniform(200, 4000, size=4):
            signal[segment] += np.sin(2 * np.pi * freq * t[segment])
    return (signal / np.max(np.abs(signal))).astype(np.float32)


@pytest.fixture
def temp_db(tmp_path):
    db = FingerprintDB(tmp_path / "test_fingerprints.db")
    yield db
    db.close()
