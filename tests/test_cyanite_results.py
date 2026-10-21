
# tests/test_cyanite_results.py

import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("CYANITE_API_TOKEN")
API_URL = "https://api.cyanite.ai/graphql"
TRACK_ID = "52943530"

if not TOKEN:
    raise ValueError("CYANITE_API_TOKEN not found in .env")

QUERY = """
query GetTrack($id: ID!) {
  libraryTrack(id: $id) {
    __typename

    ... on LibraryTrack {
      id
      title

      audioAnalysisV7 {
        __typename

        ... on AudioAnalysisV7Finished {
          result {
            genreTags
            advancedGenreTags
            moodTags
            moodAdvancedTags
            instrumentTags
            advancedInstrumentTags
            voiceTags
            bpmRangeAdjusted
            valence
            arousal
            transformerCaption
          }
        }

        ... on AudioAnalysisV7Failed {
          error {
            message
          }
        }
      }
    }

    ... on LibraryTrackNotFoundError {
      message
    }
  }
}
"""


def get_cyanite_results():
    print("Connecting to Cyanite...")
    print("Track ID:", TRACK_ID)

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "query": QUERY,
                "variables": {"id": TRACK_ID},
            },
            timeout=30,
        )

        print("\nHTTP Status:", response.status_code)

        data = response.json()

        if response.status_code != 200 or data.get("errors"):
            print(json.dumps(data, indent=2))
            return

        track = data.get("data", {}).get("libraryTrack", {})

        if track.get("__typename") != "LibraryTrack":
            print(json.dumps(track, indent=2))
            return

        analysis = track.get("audioAnalysisV7", {})
        status = analysis.get("__typename")

        print("Song:", track.get("title"))
        print("Analysis Status:", status)

        if status == "AudioAnalysisV7Finished":
            result = analysis.get("result", {})

            print("\n===== CYANITE MUSIC ANALYSIS =====")
            print(json.dumps(result, indent=2))

            output_path = BASE_DIR / "data" / "cyanite_analysis.json"
            output_path.parent.mkdir(
                parents=True, exist_ok=True
            )

            with output_path.open("w", encoding="utf-8") as file:
                json.dump(result, file, indent=2)

            print("\nAnalysis saved to:", output_path)

        elif status == "AudioAnalysisV7Failed":
            print("Analysis failed:", analysis.get("error"))

        else:
            print("Analysis is not finished yet.")

    except requests.exceptions.RequestException as error:
        print("API error:", error)

    except ValueError as error:
        print("Invalid response:", error)


if __name__ == "__main__":
    get_cyanite_results()
