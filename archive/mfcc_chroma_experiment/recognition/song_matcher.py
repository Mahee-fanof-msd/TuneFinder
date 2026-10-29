from collections import Counter

from app.vectorstore.chroma_client import ChromaClient


class SongMatcher:

    def __init__(self):
        self.chroma = ChromaClient()

    def find_match(self, embedding):

        # Step 1: Find the 5 most similar chunks
        results = self.chroma.audio_collection.query(
            query_embeddings=[
                embedding.tolist()
            ],
            n_results=5
        )

        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Step 2: Get the song title from each matching chunk
        titles = [
            metadata["title"]
            for metadata in metadatas
        ]

        # Step 3: Count how many times each song appears
        song_counts = Counter(titles)

        # Step 4: Find the song with the most matching chunks
        best_song, match_count = song_counts.most_common(1)[0]

        # Step 5: Calculate a simple match ratio
        match_ratio = match_count / len(titles)

        # Step 6: Get the closest distance for the winning song
        winning_distances = [
            distance
            for metadata, distance in zip(metadatas, distances)
            if metadata["title"] == best_song
        ]

        best_distance = min(winning_distances)

        return {
            "song": best_song,
            "match_ratio": round(match_ratio, 2),
            "matched_chunks": match_count,
            "total_results": len(titles),
            "best_distance": round(best_distance, 2)
        }