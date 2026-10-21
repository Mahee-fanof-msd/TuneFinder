
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()


class TavilyError(Exception):
    """Raised when Tavily music search fails."""
    pass


def get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise TavilyError(
            "TAVILY_API_KEY is missing from the .env file."
        )

    return TavilyClient(api_key=api_key)


def is_valid_source_url(url):
    """Check URL structure, not the truth of its content."""
    if not isinstance(url, str):
        return False

    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
    )


def run_tavily_search(query, max_results=10):
    """Execute one Tavily search and normalize its results."""

    if not isinstance(query, str) or not query.strip():
        raise TavilyError(
            "Please provide a music search request."
        )

    max_results = max(1, min(int(max_results), 20))

    client = get_tavily_client()

    try:
        response = client.search(
            query=query.strip(),
            search_depth="basic",
            topic="general",
            max_results=max_results,
            include_answer=False
        )
    except Exception as error:
        raise TavilyError(
            f"Tavily search failed: {error}"
        ) from error

    music_results = []

    for item in response.get("results") or []:
        title = item.get("title")
        url = item.get("url")

        if not title or not is_valid_source_url(url):
            continue

        music_results.append({
            "title": str(title),
            "url": url,
            "description": str(item.get("content") or ""),
            "score": item.get("score")
        })

    return music_results


def search_music(query, max_results=10):
    """
    Discover music-related webpages.

    Preserves the response structure used by
    the existing Gemini recommendation test.
    """

    results = run_tavily_search(
        query=query,
        max_results=max_results
    )

    return {
        "status": "success",
        "query": query,
        "total": len(results),
        "results": results
    }


def search_song_evidence(
    song,
    artist=None,
    year=None,
    max_results=5
):
    """
    Search for evidence about one candidate song.

    Returns webpages that may support:
    - Song identity
    - Artist or film association
    - Release date

    These results are NOT automatically verified facts.
    """

    if not isinstance(song, str) or not song.strip():
        raise TavilyError("Song title is required.")

    terms = [f'"{song.strip()}"']

    if artist and str(artist).strip().lower() != "unknown":
        terms.append(str(artist).strip())

    terms.append("song official release date soundtrack")

    if year is not None:
        terms.append(str(year))

    query = " ".join(terms)

    return {
        "query": query,
        "results": run_tavily_search(
            query,
            max_results=max_results
        )
    }


def search_song_listening_links(
    song,
    artist=None,
    max_results=5
):
    """
    Find possible individual-song listening pages.

    A returned YouTube or Spotify URL is still only
    a candidate until its song identity is checked.
    """

    terms = [f'"{song.strip()}"']

    if artist and str(artist).strip().lower() != "unknown":
        terms.append(str(artist).strip())

    terms.append(
        "(site:youtube.com/watch OR "
        "site:open.spotify.com/track) official song"
    )

    query = " ".join(terms)

    results = run_tavily_search(
        query,
        max_results=max_results
    )

    listening_results = []

    for item in results:
        parsed = urlparse(item["url"])
        hostname = (parsed.hostname or "").lower()
        path = parsed.path

        is_youtube_video = (
            hostname in ("youtube.com", "www.youtube.com")
            and path == "/watch"
        )

        is_spotify_track = (
            hostname == "open.spotify.com"
            and path.startswith("/track/")
        )

        if is_youtube_video or is_spotify_track:
            listening_results.append(item)

    return {
        "query": query,
        "results": listening_results
    }
