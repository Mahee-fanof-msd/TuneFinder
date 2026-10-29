# Archive: MFCC + ChromaDB experiment

This was the first recognition approach. It averaged MFCC features per
8-second chunk and searched for the nearest chunks in ChromaDB.

It was replaced by acoustic fingerprinting (`app/fingerprinting/`), which is
far more accurate for exact song identification. The FastAPI app no longer
uses any of this code.

Kept for reference only. It may be useful later for the "Similar Songs"
feature, since embeddings capture overall sound rather than exact matches.

Known issue: `scripts/ingest_audio.py` calls `AudioChunker.create_chunks()`
with a waveform, but that method expects a file path.
