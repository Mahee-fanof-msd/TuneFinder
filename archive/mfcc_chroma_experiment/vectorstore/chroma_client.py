import chromadb


class ChromaClient:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.audio_collection = self.client.get_or_create_collection(
            name="audio_embeddings"
        )