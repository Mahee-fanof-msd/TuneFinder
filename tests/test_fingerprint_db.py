
import sqlite3

connection = sqlite3.connect("fingerprints.db")
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM fingerprints")
total = cursor.fetchone()[0]

print("Total fingerprints stored:", total)

cursor.execute("""
    SELECT song_name, COUNT(*)
    FROM fingerprints
    GROUP BY song_name
""")

for song_name, count in cursor.fetchall():
    print(f"Song: {song_name}")
    print(f"Fingerprints: {count}")

connection.close()



import sqlite3

connection = sqlite3.connect("fingerprints.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT COUNT(*)
    FROM fingerprints
""")
total = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT song_name, hash, timestamp
        FROM fingerprints
        GROUP BY song_name, hash, timestamp
    )
""")
unique = cursor.fetchone()[0]

print("Total stored fingerprints:", total)
print("Unique fingerprint records:", unique)
print("Duplicate records:", total - unique)

connection.close()
