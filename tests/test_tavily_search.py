from app.services.tavily_service import (
    search_music,
    TavilyError
)


def main():

    query = input(
        "Enter your music preference: "
    ).strip()

    try:

        result = search_music(
            query,
            max_results=10
        )

        print("\nSearch results:\n")

        for index, item in enumerate(
            result["results"],
            start=1
        ):

            print(f"{index}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   Description: {item['description'][:200]}")
            print()

    except TavilyError as error:

        print(f"Error: {error}")


if __name__ == "__main__":
    main()