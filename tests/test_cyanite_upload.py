
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TOKEN = os.getenv("CYANITE_API_TOKEN")
API_URL = "https://api.cyanite.ai/graphql"

if not TOKEN:
    raise RuntimeError("CYANITE_API_TOKEN missing from .env")


def graphql(query, variables=None):
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "variables": variables or {},
        },
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("errors"):
        raise RuntimeError(result["errors"])

    return result["data"]


def upload_song(path):
    path = Path(path)

    if not path.is_file() or path.suffix.lower() != ".mp3":
        raise ValueError("Provide an existing MP3 file")

    # 1. Request a temporary upload URL
    data = graphql("""
        mutation {
            fileUploadRequest {
                id
                uploadUrl
            }
        }
    """)

    upload = data["fileUploadRequest"]
    print("Upload URL received")

    # 2. Upload MP3 to Cyanite's storage
    with path.open("rb") as audio:
        response = requests.put(
            upload["uploadUrl"],
            data=audio,
            headers={"Content-Type": "audio/mpeg"},
            timeout=180,
        )
    response.raise_for_status()
    print("MP3 uploaded successfully")

    # 3. Create library track and start analysis
    data = graphql("""
        mutation CreateTrack($input: LibraryTrackCreateInput!) {
            libraryTrackCreate(input: $input) {
                __typename
                ... on LibraryTrackCreateSuccess {
                    createdLibraryTrack {
                        id
                        title
                    }
                }
                ... on LibraryTrackCreateError {
                    code
                    message
                }
            }
        }
    """, {
        "input": {
            "uploadId": upload["id"],
            "title": path.stem[:150],
        }
    })

    result = data["libraryTrackCreate"]

    if result["__typename"] != "LibraryTrackCreateSuccess":
        print("Cyanite error:", result)
        return

    track = result["createdLibraryTrack"]
    print("Track created:", track)
    print("Analysis may now be processing.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tests/test_cyanite_upload.py song.mp3")
        sys.exit(1)

    upload_song(sys.argv[1])
