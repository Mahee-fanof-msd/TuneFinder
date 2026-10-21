from app.audio.chunker import AudioChunker
from app.services.audio_fingerprint import AudioFingerprint


chunker = AudioChunker(
    chunk_duration=8,
    step_size=4
)

fingerprinter = AudioFingerprint()

song_path = "data/songs/David Kushner - Daylight (Official Music Video).mp3"

chunks = chunker.create_chunks(song_path)

for index, chunk in enumerate(chunks):

    fingerprints = fingerprinter.create_fingerprints(
        chunk["waveform"],
        chunk["sample_rate"]
    )

    print(
        f"Chunk {index + 1}: "
        f"{chunk['start_time']:.0f}-{chunk['end_time']:.0f} sec | "
        f"Fingerprints: {len(fingerprints)}"
    )