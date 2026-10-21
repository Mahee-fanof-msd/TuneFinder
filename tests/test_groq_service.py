import json

from app.services.groq_service import (
    interpret_music_request,
    GroqServiceError
)


def main():

    print("\n================================")
    print("TUNEFINDER - GROQ INTERPRETER")
    print("================================")

    user_request = input(
        "\nEnter your music preference: "
    ).strip()

    if not user_request:
        print("Please enter a music preference.")
        return

    try:
        print("\nInterpreting your request with Groq...")

        result = interpret_music_request(
            user_request
        )

        print("\n================================")
        print("INTERPRETED USER REQUEST")
        print("================================")

        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )

        print("\n================================")
        print("SEARCH QUERY FOR TAVILY")
        print("================================")

        print(
            result["interpreted_request"]["search_query"]
        )

    except GroqServiceError as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()