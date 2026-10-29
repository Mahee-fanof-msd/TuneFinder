from app.audio.processor import AudioProcessor
from app.embeddings.audio_embedding import AudioEmbedding
from app.recognition.song_matcher import SongMatcher


class SongService:

    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.audio_embedding = AudioEmbedding()
        self.song_matcher = SongMatcher()

    async def identify_song(self, audio):

        # Step 1: Read uploaded audio file
        audio_bytes = await audio.read()

        # Step 2: Convert audio into waveform
        waveform, sample_rate = self.audio_processor.process(
            audio_bytes
        )

        # Step 3: Convert waveform into MFCC embedding
        embedding = self.audio_embedding.create_embedding(
            waveform,
            sample_rate
        )

        # Step 4: Search ChromaDB for similar chunks
        results = self.song_matcher.find_match(
            embedding
        )

        # Step 5: Return the search results
        return {
            "status": "success",
            "matches": results
        }