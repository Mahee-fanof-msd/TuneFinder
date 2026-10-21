
import re
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import urlparse

import requests

from app.services.tavily_service import (
    search_song_evidence,
    search_song_listening_links,
    TavilyError,
)


ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

ROMANTIC_TERMS = (
    "romantic",
    "romance",
    "love song",
    "love melody",
    "love track",
    "romantic melody",
    "ప్రేమ",
)

NON_ROMANTIC_TERMS = (
    "dance number",
    "party anthem",
    "mass anthem",
    "devotional",
    "bhakti",
)

SOURCE_PRIORITY = {
    "music.apple.com": 3,
    "itunes.apple.com": 3,
    "youtube.com": 1,
    "www.youtube.com": 1,
    "spotify.com": 2,
    "open.spotify.com": 2,
}

SOCIAL_HOSTS = {
    "facebook.com",
    "www.facebook.com",
    "instagram.com",
    "www.instagram.com",
    "tiktok.com",
    "www.tiktok.com",
}


class MusicVerificationError(Exception):
    pass


def normalize_text(value):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        str(value or "").casefold()
    ).strip()


def similarity(a, b):
    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio()


def contains_phrase(text, phrase):
    text = normalize_text(text)
    phrase = normalize_text(phrase)

    return bool(
        phrase
        and f" {phrase} " in f" {text} "
    )


def extract_requested_year(preference):
    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        preference or ""
    )

    return int(years[-1]) if years else None


def extract_requested_actor(preference):
    """
    Initial actor support for the current TuneFinder tests.
    Expand with structured entity extraction later.
    """
    known_actors = {
        "nani": "Nani",
        "ravi teja": "Ravi Teja",
        "raviteja": "Ravi Teja",
    }

    text = normalize_text(preference)

    for key, name in known_actors.items():
        if contains_phrase(text, key):
            return name

    return None


def extract_requested_mood(preference):
    text = (preference or "").casefold()

    if any(
        word in text
        for word in ("romantic", "romance", "love songs")
    ):
        return "romantic"

    if any(
        word in text
        for word in ("devotional", "bhakti")
    ):
        return "devotional"

    return None


def extract_requested_language(preference):
    text = normalize_text(preference)

    for language in ("telugu", "hindi", "tamil", "kannada", "malayalam"):
        if contains_phrase(text, language):
            return language

    return None


def parse_release_date(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).date()
    except (ValueError, TypeError):
        return None


def source_host(url):
    try:
        return (
            urlparse(url).hostname or ""
        ).lower()
    except ValueError:
        return ""


def search_apple_music(song):
    try:
        response = requests.get(
            ITUNES_SEARCH_URL,
            params={
                "term": song,
                "entity": "song",
                "limit": 50
            },
            timeout=15
        )

        response.raise_for_status()

        return response.json().get("results", [])

    except (requests.RequestException, ValueError):
        return []


def find_catalog_match(song, artist, movie=None):
    results = search_apple_music(song)

    candidates = []

    for item in results:
        track_name = item.get("trackName", "")

        title_score = similarity(song, track_name)

        if title_score < 0.88:
            continue

        catalog_artist = item.get("artistName", "")
        collection = item.get("collectionName", "")

        artist_score = (
            similarity(artist, catalog_artist)
            if artist and artist.lower() != "unknown"
            else 0
        )

        movie_score = (
            similarity(movie, collection)
            if movie
            else 0
        )

        score = (
            title_score * 0.7
            + artist_score * 0.15
            + movie_score * 0.15
        )

        candidates.append((score, item))

    if not candidates:
        return None

    candidates.sort(
        key=lambda value: value[0],
        reverse=True
    )

    # A close title alone is not enough if several
    # different catalog recordings could match.
    if len(candidates) > 1:
        top = candidates[0][0]
        second = candidates[1][0]

        if top - second < 0.02:
            return None

    return candidates[0][1]


def search_evidence(song, artist, year):
    response = search_song_evidence(
        song=song,
        artist=artist,
        year=year,
        max_results=10
    )

    return response.get("results", [])


def evidence_text(item):
    return " ".join([
        str(item.get("title") or ""),
        str(item.get("description") or "")
    ])


def relevant_evidence(song, evidence):
    return [
        item for item in evidence
        if contains_phrase(
            evidence_text(item),
            song
        )
    ]


def non_social_evidence(song, evidence):
    return [
        item
        for item in relevant_evidence(song, evidence)
        if source_host(item.get("url")) not in SOCIAL_HOSTS
    ]


def check_actor_association(
    song,
    movie,
    actor,
    evidence,
    catalog
):
    if not actor:
        return "not_required", []

    supporting = []

    for item in non_social_evidence(song, evidence):
        text = evidence_text(item)

        if contains_phrase(text, actor):
            supporting.append(item)

    # Movie names in a catalog are useful context,
    # but do not independently establish cast credits.
    if supporting:
        return "unverified", supporting[:3]

    return "unverified", []


def check_mood(song, mood, evidence):
    if not mood:
        return "not_required", []

    supporting = []

    for item in non_social_evidence(song, evidence):
        text = evidence_text(item).casefold()

        if mood == "romantic":
            positive = any(
                term in text
                for term in ROMANTIC_TERMS
            )

            negative = any(
                term in text
                for term in NON_ROMANTIC_TERMS
            )

            if positive and not negative:
                supporting.append(item)

        elif mood == "devotional":
            if any(
                term in text
                for term in ("devotional", "bhakti", "spiritual")
            ):
                supporting.append(item)

    # Search snippets alone are insufficient to
    # certify subjective mood or genre.
    return "unverified", supporting[:3]


def check_language(song, language, evidence, catalog):
    if not language:
        return "not_required", []

    supporting = []

    for item in non_social_evidence(song, evidence):
        if contains_phrase(
            evidence_text(item),
            language
        ):
            supporting.append(item)

    return "unverified", supporting[:3]


def check_release_year(catalog, requested_year):
    if requested_year is None:
        return "not_required", None

    if not catalog:
        return "unverified", None

    release_date = parse_release_date(
        catalog.get("releaseDate")
    )

    if not release_date:
        return "unverified", None

    if release_date.year != requested_year:
        # Catalog dates can represent reissues.
        # Treat the mismatch as a contradiction
        # requiring review, not absolute proof.
        return "rejected", str(release_date)

    return "verified", str(release_date)


def find_listening_link(song, catalog):
    if catalog and catalog.get("trackViewUrl"):
        return catalog["trackViewUrl"]

    try:
        response = search_song_listening_links(
            song=song,
            max_results=8
        )
    except TavilyError:
        return None

    for item in response.get("results", []):
        if contains_phrase(
            item.get("title", ""),
            song
        ):
            return item.get("url")

    return None


def verify_song(candidate, user_preference):
    song = str(candidate.get("song") or "").strip()
    artist = str(
        candidate.get("artist") or "Unknown"
    ).strip()

    movie = candidate.get("movie")

    if not song:
        return {
            "song": song,
            "verified": False,
            "status": "rejected",
            "reason": "Missing song title.",
            "checks": {}
        }

    requested_year = extract_requested_year(
        user_preference
    )

    requested_actor = extract_requested_actor(
        user_preference
    )

    requested_mood = extract_requested_mood(
        user_preference
    )

    requested_language = extract_requested_language(
        user_preference
    )

    catalog = find_catalog_match(
        song,
        artist,
        movie
    )

    try:
        evidence = search_evidence(
            song,
            artist,
            requested_year
        )
    except TavilyError as error:
        raise MusicVerificationError(
            f"Evidence search failed for {song}: {error}"
        ) from error

    checks = {}

    checks["song_identity"] = (
        "verified" if catalog else "unverified"
    )

    year_status, release_date = check_release_year(
        catalog,
        requested_year
    )

    checks["release_year"] = year_status

    actor_status, actor_sources = check_actor_association(
        song,
        movie,
        requested_actor,
        evidence,
        catalog
    )

    checks["actor_association"] = actor_status

    mood_status, mood_sources = check_mood(
        song,
        requested_mood,
        evidence
    )

    checks["mood"] = mood_status

    language_status, language_sources = check_language(
        song,
        requested_language,
        evidence,
        catalog
    )

    checks["language"] = language_status

    if "rejected" in checks.values():
        status = "rejected"
    elif all(
        value in ("verified", "not_required")
        for value in checks.values()
    ):
        status = "verified"
    else:
        status = "unverified"

    listening_url = find_listening_link(
        song,
        catalog
    )

    evidence_urls = list(dict.fromkeys(
        item.get("url")
        for item in (
            actor_sources
            + mood_sources
            + language_sources
        )
        if item.get("url")
    ))

    if catalog and catalog.get("trackViewUrl"):
        evidence_urls.insert(
            0,
            catalog["trackViewUrl"]
        )

    return {
        "verified": status == "verified",
        "status": status,
        "song": (
            catalog.get("trackName", song)
            if catalog
            else song
        ),
        "artist": (
            catalog.get("artistName", artist)
            if catalog
            else artist
        ),
        "movie": movie,
        "release_date": release_date,
        "checks": checks,
        "reason": (
            "All required checks passed."
            if status == "verified"
            else "One or more requested conditions "
                 "could not be reliably established."
        ),
        "listening_url": listening_url,
        "evidence_urls": evidence_urls[:5],
        "verification_level": (
            "catalog_and_web_evidence"
            if status == "verified"
            else "incomplete_verification"
        )
    }


def verify_recommendations(
    user_preference,
    recommendations
):
    accepted = []
    rejected = []
    unverified = []

    for candidate in recommendations[:5]:
        result = verify_song(
            candidate,
            user_preference
        )

        if result["status"] == "verified":
            result["rank"] = len(accepted) + 1
            accepted.append(result)

        elif result["status"] == "rejected":
            rejected.append(result)

        else:
            unverified.append(result)

    return {
        "status": "success",
        "total": len(accepted),
        "recommendations": accepted,
        "rejected": rejected,
        "unverified": unverified
    }
