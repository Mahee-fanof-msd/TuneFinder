from app.services.groq_service import (
    interpret_music_request,
    recommend_music,
    GroqServiceError,
)

from app.services.tavily_service import (
    search_music,
    TavilyError,
)


def main():
    print("\n================================")
    print("TUNEFINDER - MUSIC RECOMMENDATIONS")
    print("================================")

    query = input("\nEnter your music preference: ").strip()

    if not query:
        print("Please enter a music preference.")
        return

    try:
        # Step 1: Groq interprets the request
        interpretation = interpret_music_request(query)
        interpreted = interpretation["interpreted_request"]

        # Step 2: Tavily searches the internet
        search_result = search_music(
            interpreted["search_query"],
            max_results=15,
        )

        sources = search_result.get("results", [])

        if not sources:
            print("\nNo songs found.")
            return

        # Step 3: Groq generates recommendations
        result = recommend_music(
            user_preference=query,
            interpreted_request=interpreted,
            search_results=sources,
        )

        # Display only song title and link
        print("\n🎵 Recommended Songs\n")

        recommendations = result.get("recommendations", [])

        if not recommendations:
            print("No matching songs found.")
            return

        for index, song in enumerate(recommendations, start=1):
            print(f"{index}. {song['song']}")

            links = song.get("source_urls", [])

            if links:
                print(f"   🔗 {links[0]}")
            else:
                print("   🔗 Link unavailable")

            print()

    except (GroqServiceError, TavilyError) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()