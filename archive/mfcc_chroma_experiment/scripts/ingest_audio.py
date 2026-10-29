from pathlib import Path
import librosa

from app.audio.chunker import AudioChunker
from app.embeddings.audio_embedding import AudioEmbedding
from app.vectorstore.chroma_client import ChromaClient


# Location of reference songs
SONGS_FOLDER = Path("data/songs")


# Create objects
audio_embedding = AudioEmbedding()
audio_chunker = AudioChunker()
chroma = ChromaClient()


# Find all MP3 files
song_files = list(SONGS_FOLDER.glob("*.mp3"))

print("Songs found:", len(song_files))


# Process each song
for song in song_files:

    print("-------------------------")
    print("Processing:", song.name)

    # Step 1: Load the full song
    waveform, sample_rate = librosa.load(
        song,
        sr=22050,
        mono=True
    )

    # Step 2: Split song into 8-second chunks
    chunks = audio_chunker.create_chunks(
        waveform,
        sample_rate
    )

    print("Number of chunks:", len(chunks))

    # Step 3: Remove the OLD full-song embedding
    # if it exists from our previous version
    try:
        chroma.audio_collection.delete(
            ids=[song.stem]
        )
    except Exception:
        pass

    # Step 4: Process every chunk
    for chunk_index, chunk in enumerate(chunks):

        # Create MFCC embedding for this chunk
        embedding = audio_embedding.create_embedding(
            chunk,
            sample_rate
        )

        # Because chunks move every 4 seconds:
        # chunk 0 = 0-8
        # chunk 1 = 4-12
        # chunk 2 = 8-16
        start_time = chunk_index * 4
        end_time = start_time + 8

        # Unique ID for this chunk
        chunk_id = f"{song.stem}_chunk_{chunk_index}"

        # Store chunk embedding in ChromaDB
        chroma.audio_collection.upsert(
            ids=[
                chunk_id
            ],

            embeddings=[
                embedding.tolist()
            ],

            metadatas=[
                {
                    "title": song.stem,
                    "filename": song.name,
                    "chunk_index": chunk_index,
                    "start_time": start_time,
                    "end_time": end_time
                }
            ]
        )

    print(
        "Stored",
        len(chunks),
        "chunks in ChromaDB for:",
        song.name
    )


print("-------------------------")
print("Audio chunk ingestion completed successfully.")

count = chroma.audio_collection.count()

print("Total chunks stored in ChromaDB:", count)