
import sqlite3


class FingerprintDB:
    def __init__(self, db_path="fingerprints.db"):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_name TEXT NOT NULL,
                hash TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fingerprint_hash
            ON fingerprints(hash)
        """)

        self.connection.commit()

    def insert_fingerprints(self, song_name, fingerprints):
        records = [
            (song_name, fp["hash"], fp["timestamp"])
            for fp in fingerprints
        ]

        self.cursor.executemany("""
            INSERT INTO fingerprints (song_name, hash, timestamp)
            VALUES (?, ?, ?)
        """, records)

        self.connection.commit()

    def close(self):
        self.connection.close()
