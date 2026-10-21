
from app.services.tavily_service import (
    search_music,
    TavilyError
)

from app.services.gemini_service import (
    recommend_music,
    GeminiError
)

from app.services.music_verification_service import (
    verify_recommendations,
    MusicVerificationError
)


def print_song(item):
    print(f"\nSong: {item.get('song')}")
    print(f"Artist: {item.get('artist', 'Unknown')}")
    print(f"Status: {item.get('status')}")

    if item.get("release_date"):
        print(
            f"Release date: {item['release_date']}"
        )

    if item.get("listening_url"):
        print(
            f"Listen: {item['listening_url']}"
        )

    print("Verification checks:")

    for name, status in item.get(
        "checks", {}
    ).items():
        print(f"  {name}: {status}")

    print(
        f"Explanation: {item.get('reason', '')}"
    )

    for url in item.get("evidence_urls", []):
        print(f"Evidence: {url}")


def main():
    query = input(
        "Enter your music preference: "
    ).strip()

    if not query:
        print("Please enter a music preference.")
        return

    try:
        print("\nSearching online with Tavily...")

        search_result = search_music(
            query,
            max_results=15
        )

        print(
            f"Found {search_result['total']} "
            "search results."
        )

        print("\nAnalyzing results with Gemini...")

        gemini_result = recommend_music(
            user_preference=query,
            search_results=search_result["results"]
        )

        print(
            f"Gemini proposed "
            f"{gemini_result['total']} songs."
        )

        print("\nVerifying recommendations...")

        result = verify_recommendations(
            user_preference=query,
            recommendations=gemini_result[
                "recommendations"
            ]
        )

        print("\n============================")
        print("VERIFIED RECOMMENDATIONS")
        print("============================")

        print(
            f"Total: {result['total']}"
        )

        for item in result["recommendations"]:
            print_song(item)

        print("\n============================")
        print("UNVERIFIED CANDIDATES")
        print("============================")

        print(
            f"Total: {len(result['unverified'])}"
        )

        for item in result["unverified"]:
            print_song(item)

        print("\n============================")
        print("REJECTED CANDIDATES")
        print("============================")

        print(
            f"Total: {len(result['rejected'])}"
        )

        for item in result["rejected"]:
            print_song(item)

    except (
        TavilyError,
        GeminiError,
        MusicVerificationError
    ) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()
