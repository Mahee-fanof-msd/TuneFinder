from dotenv import load_dotenv

from app.services.cyanite_service import graphql


load_dotenv()


def main():

    track_id = input(
        "Enter your Cyanite track ID: "
    ).strip()

    if not track_id:
        print("A track ID is required.")
        return

    query = """
    query SimilarTracks($trackId: ID!) {
        libraryTrack(id: $trackId) {
            __typename

            ... on LibraryTrack {
                id
                title

                similarTracks(
                    target: { spotify: {} }
                    first: 5
                ) {
                    __typename

                    ... on SimilarTracksError {
                        code
                        message
                    }

                    ... on SimilarTracksConnection {
                        edges {
                            node {
                                __typename
                                id
                                title
                            }
                        }
                    }
                }
            }
        }
    }
    """

    try:
        data = graphql(
            query,
            {"trackId": track_id}
        )

        track = data.get("libraryTrack") or {}

        if track.get("__typename") != "LibraryTrack":
            print("Track not found or inaccessible.")
            print(track)
            return

        similar = track.get("similarTracks") or {}

        if similar.get("__typename") == "SimilarTracksError":
            print("Cyanite similarity search error:")
            print(similar)
            return

        if similar.get("__typename") != "SimilarTracksConnection":
            print("Unexpected similarity response:")
            print(similar)
            return

        edges = similar.get("edges") or []

        print("\nTop similar Spotify tracks:\n")

        if not edges:
            print("No similar tracks returned.")
            return

        for index, edge in enumerate(edges[:5], start=1):

            song = edge.get("node") or {}

            spotify_id = song.get("id")
            title = song.get("title") or "Unknown title"

            print(f"{index}. {title}")

            if spotify_id:
                print(
                    f"   https://open.spotify.com/track/{spotify_id}"
                )

    except Exception as error:
        print(f"Similarity search failed: {error}")


if __name__ == "__main__":
    main()