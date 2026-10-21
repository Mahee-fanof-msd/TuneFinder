
from collections import Counter, defaultdict


class FingerprintMatcher:
    def __init__(self, db):
        self.db = db

    def match(self, fingerprints):
        if not fingerprints:
            return None

        # Store matched fingerprint pairs for each song.
        matches_by_song = defaultdict(list)
        seen_matches = set()

        for fp in fingerprints:
            fingerprint_hash = fp["hash"]
            clip_time = float(fp["timestamp"])

            self.db.cursor.execute(
                """
                SELECT song_name, timestamp
                FROM fingerprints
                WHERE hash = ?
                """,
                (fingerprint_hash,)
            )

            for song_name, song_time in self.db.cursor.fetchall():
                song_time = float(song_time)

                match_key = (
                    song_name,
                    fingerprint_hash,
                    round(song_time, 3),
                    round(clip_time, 3),
                )

                if match_key in seen_matches:
                    continue

                seen_matches.add(match_key)

                matches_by_song[song_name].append(
                    (fingerprint_hash, clip_time, song_time)
                )

        if not matches_by_song:
            return None

        candidates = []

        for song_name, matches in matches_by_song.items():

            # Group matches by approximate time offset.
            # This allows a little tolerance for timing variation.
            offset_groups = defaultdict(list)

            for fingerprint_hash, clip_time, song_time in matches:
                offset = song_time - clip_time

                bucket = round(offset * 2) / 2

                offset_groups[bucket].append(
                    (fingerprint_hash, clip_time, song_time)
                )

            # Evaluate each offset bucket using unique hashes.
            for bucket, group in offset_groups.items():

                unique_hashes = {
                    item[0] for item in group
                }

                # Keep the strongest group for this song.
                candidates.append({
                    "song": song_name,
                    "start_time": float(bucket),
                    "aligned_matches": len(group),
                    "unique_matching_hashes": len(unique_hashes),
                })

        if not candidates:
            return None

        # Rank candidates by unique hashes, then total votes.
        candidates.sort(
            key=lambda candidate: (
                candidate["unique_matching_hashes"],
                candidate["aligned_matches"],
            ),
            reverse=True,
        )

        best = candidates[0]

        # Conservative starting thresholds.
        # These must be validated against unknown recordings.
        MIN_ALIGNED_MATCHES = 50
        MIN_UNIQUE_HASHES = 25

        if (
            best["aligned_matches"] < MIN_ALIGNED_MATCHES
            or best["unique_matching_hashes"] < MIN_UNIQUE_HASHES
        ):
            return None

        # Avoid accepting a weak winner when another song
        # has a similarly strong alignment.
        competing_songs = [
            candidate
            for candidate in candidates
            if candidate["song"] != best["song"]
        ]

        if competing_songs:
            runner_up = max(
                competing_songs,
                key=lambda candidate: (
                    candidate["unique_matching_hashes"],
                    candidate["aligned_matches"],
                ),
            )

            if (
                best["unique_matching_hashes"]
                < runner_up["unique_matching_hashes"] * 2
            ):
                return None

        return best
