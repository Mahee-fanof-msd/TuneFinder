import os
import subprocess
import time
import logging

import requests
import imageio_ffmpeg

from dotenv import load_dotenv


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

CYANITE_API_URL = "https://api.cyanite.ai/graphql"

logger = logging.getLogger(__name__)


class CyaniteError(Exception):
    """Raised when Cyanite processing fails."""
    pass


# --------------------------------------------------
# CYANITE GRAPHQL REQUEST
# --------------------------------------------------

def graphql(query, variables=None):

    api_token = os.getenv("CYANITE_API_TOKEN")

    if not api_token:
        raise CyaniteError(
            "CYANITE_API_TOKEN is missing from the .env file."
        )

    try:
        response = requests.post(
            CYANITE_API_URL,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "variables": variables or {}
            },
            timeout=40
        )

        response.raise_for_status()
        result = response.json()

    except requests.exceptions.RequestException as error:
        raise CyaniteError(
            f"Cyanite API request failed: {error}"
        ) from error

    except ValueError as error:
        raise CyaniteError(
            "Cyanite returned an invalid JSON response."
        ) from error

    if result.get("errors"):
        raise CyaniteError(str(result["errors"]))

    if "data" not in result:
        raise CyaniteError(
            "Cyanite response does not contain data."
        )

    return result["data"]


# --------------------------------------------------
# CONVERT MICROPHONE WAV TO MP3
# WITHOUT SAVING AUDIO LOCALLY
# --------------------------------------------------

def wav_to_mp3(wav_bytes):

    if not wav_bytes:
        raise CyaniteError("Audio recording is empty.")

    try:
        ffmpeg_executable = imageio_ffmpeg.get_ffmpeg_exe()

        process = subprocess.run(
            [
                ffmpeg_executable,
                "-hide_banner",
                "-loglevel", "error",
                "-f", "wav",
                "-i", "pipe:0",
                "-codec:a", "libmp3lame",
                "-b:a", "192k",
                "-f", "mp3",
                "pipe:1"
            ],
            input=wav_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=40,
            check=False
        )

    except (FileNotFoundError, RuntimeError, OSError) as error:
        raise CyaniteError(
            "Unable to locate or run the imageio-ffmpeg executable."
        ) from error

    except subprocess.TimeoutExpired as error:
        raise CyaniteError(
            "Audio conversion timed out."
        ) from error

    if process.returncode != 0 or not process.stdout:

        error_message = process.stderr.decode(
            errors="replace"
        )

        raise CyaniteError(
            f"Audio conversion failed: {error_message[-500:]}"
        )

    return process.stdout


# --------------------------------------------------
# UPLOAD AUDIO TO CYANITE
# --------------------------------------------------

def submit_audio(wav_bytes):

    # Convert WAV to MP3 in memory.
    mp3_bytes = wav_to_mp3(wav_bytes)

    # Request upload URL.
    upload_query = """
    mutation {
        fileUploadRequest {
            id
            uploadUrl
        }
    }
    """

    upload_result = graphql(upload_query)

    upload = upload_result.get("fileUploadRequest")

    if not upload:
        raise CyaniteError(
            "Cyanite did not provide an upload URL."
        )

    upload_id = upload.get("id")
    upload_url = upload.get("uploadUrl")

    if not upload_id or not upload_url:
        raise CyaniteError(
            "Cyanite returned incomplete upload information."
        )

    # Upload MP3 from memory.
    try:
        upload_response = requests.put(
            upload_url,
            data=mp3_bytes,
            headers={
                "Content-Type": "audio/mpeg"
            },
            timeout=90
        )

        upload_response.raise_for_status()

    except requests.exceptions.RequestException as error:
        raise CyaniteError(
            f"Cyanite audio upload failed: {error}"
        ) from error

    # Create library track.
    create_track_query = """
    mutation CreateTrack(
        $input: LibraryTrackCreateInput!
    ) {
        libraryTrackCreate(input: $input) {
            __typename

            ... on LibraryTrackCreateSuccess {
                createdLibraryTrack {
                    id
                }
            }

            ... on LibraryTrackCreateError {
                code
                message
            }
        }
    }
    """

    variables = {
        "input": {
            "uploadId": upload_id,
            "title": "TuneFinder microphone clip"
        }
    }

    create_result = graphql(
        create_track_query,
        variables
    )

    created = create_result.get("libraryTrackCreate")

    if not created:
        raise CyaniteError(
            "Cyanite did not return a track creation result."
        )

    if created.get("__typename") != "LibraryTrackCreateSuccess":
        raise CyaniteError(
            created.get("message")
            or "Cyanite track creation failed."
        )

    track = created.get("createdLibraryTrack") or {}

    track_id = track.get("id")

    if not track_id:
        raise CyaniteError(
            "Cyanite did not return a track ID."
        )

    return track_id


# --------------------------------------------------
# GET CYANITE AUDIO ANALYSIS
# --------------------------------------------------

def get_analysis(track_id):

    analysis_query = """
    query Track($id: ID!) {

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
                }
            }
        }
    }
    """

    variables = {
        "id": str(track_id)
    }

    result = graphql(
        analysis_query,
        variables
    )

    track = result.get("libraryTrack")

    if not track:
        raise CyaniteError(
            "Cyanite track was not found."
        )

    if track.get("__typename") != "LibraryTrack":
        raise CyaniteError(
            "Cyanite returned an unexpected track type."
        )

    analysis = track.get("audioAnalysisV7") or {}

    analysis_status = analysis.get(
        "__typename",
        "Unknown"
    )

    if analysis_status == "AudioAnalysisV7Finished":

        return {
            "status": "analysis_ready",
            "track_id": str(track_id),
            "analysis": analysis.get("result") or {}
        }

    if (
        "Error" in analysis_status
        or "Failed" in analysis_status
    ):

        return {
            "status": "analysis_failed",
            "track_id": str(track_id),
            "state": analysis_status
        }

    return {
        "status": "processing",
        "track_id": str(track_id),
        "state": analysis_status
    }


# --------------------------------------------------
# FIND TOP 5 SIMILAR SONGS ON SPOTIFY
# --------------------------------------------------

def get_similar_tracks(track_id, limit=5):

    """
    Find similar Spotify tracks using Cyanite.
    """

    limit = max(1, min(int(limit), 5))

    similarity_query = """
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

    variables = {
        "trackId": str(track_id)
    }

    result = graphql(
        similarity_query,
        variables
    )

    track = result.get("libraryTrack")

    if not track:
        raise CyaniteError(
            "Cyanite track was not found."
        )

    if track.get("__typename") != "LibraryTrack":
        raise CyaniteError(
            "Cyanite returned an unexpected track type."
        )

    similar = track.get("similarTracks") or {}

    if similar.get("__typename") == "SimilarTracksError":
        raise CyaniteError(
            similar.get("message")
            or "Cyanite similarity search failed."
        )

    if similar.get("__typename") != "SimilarTracksConnection":
        raise CyaniteError(
            "Cyanite returned an unexpected similarity response."
        )

    edges = similar.get("edges") or []

    recommendations = []

    for edge in edges:

        song = (edge or {}).get("node") or {}

        spotify_id = song.get("id")
        title = song.get("title") or "Unknown Song"

        if not spotify_id:
            continue

        recommendations.append(
            {
                "rank": len(recommendations) + 1,
                "title": title,
                "spotify_id": spotify_id,
                "spotify_url": (
                    f"https://open.spotify.com/track/{spotify_id}"
                )
            }
        )

        if len(recommendations) >= limit:
            break

    return {
        "status": "recommendations_ready",
        "track_id": str(track_id),
        "total": len(recommendations),
        "recommendations": recommendations
    }


# --------------------------------------------------
# NEW: DELETE UPLOADED TRACK FROM CYANITE
# --------------------------------------------------

def delete_track(track_id):

    """
    Attempt to delete an uploaded Cyanite library track.

    NOTE:
    The libraryTrackDelete mutation and its arguments
    must be verified against Cyanite's GraphQL schema.
    """

    if not track_id:
        raise CyaniteError(
            "Cannot delete a track without its ID."
        )

    delete_query = """
    mutation DeleteTrack($id: ID!) {

        libraryTrackDelete(id: $id) {
            __typename
        }
    }
    """

    variables = {
        "id": str(track_id)
    }

    result = graphql(
        delete_query,
        variables
    )

    deletion = result.get("libraryTrackDelete")

    if deletion is None:
        raise CyaniteError(
            "Cyanite did not confirm track deletion."
        )

    deletion_type = deletion.get("__typename", "")

    if (
        "Error" in deletion_type
        or "Failure" in deletion_type
    ):
        raise CyaniteError(
            f"Cyanite deletion failed: {deletion_type}"
        )

    logger.info(
        "Cyanite track deletion returned: %s",
        deletion_type
    )

    return {
        "status": "deleted",
        "track_id": str(track_id)
    }


# --------------------------------------------------
# NEW: COMPLETE WORKFLOW WITH AUTOMATIC CLEANUP
# --------------------------------------------------

def analyze_recommend_and_cleanup(
    wav_bytes,
    limit=5,
    poll_seconds=5,
    max_wait_seconds=180
):

    """
    Complete Cyanite processing workflow.

    1. Upload microphone audio.
    2. Wait for audio analysis.
    3. Retrieve similar Spotify songs.
    4. Attempt to delete uploaded track.
    5. Return analysis and recommendations.

    Cleanup is attempted even if processing fails.
    """

    track_id = None
    result = None
    processing_error = None

    cleanup = {
        "status": "not_attempted"
    }

    try:

        # STEP 1: Upload audio.

        track_id = submit_audio(wav_bytes)

        logger.info(
            "Cyanite track created: %s",
            track_id
        )

        # STEP 2: Wait for analysis.

        deadline = time.monotonic() + max_wait_seconds

        while True:

            analysis_result = get_analysis(track_id)

            status = analysis_result.get("status")

            if status == "analysis_ready":
                break

            if status == "analysis_failed":
                raise CyaniteError(
                    "Cyanite analysis failed: "
                    f"{analysis_result.get('state')}"
                )

            if time.monotonic() >= deadline:
                raise CyaniteError(
                    "Timed out waiting for Cyanite analysis."
                )

            time.sleep(poll_seconds)

        # STEP 3: Retrieve similar songs.

        similarity_result = get_similar_tracks(
            track_id,
            limit=limit
        )

        # STEP 4: Preserve results before deletion.

        result = {
            "status": "complete",
            "track_id": str(track_id),
            "analysis": analysis_result.get("analysis", {}),
            "recommendations": similarity_result.get(
                "recommendations",
                []
            ),
            "total": similarity_result.get("total", 0)
        }

    except Exception as error:

        processing_error = error

        logger.exception(
            "Cyanite processing failed."
        )

    finally:

        # STEP 5: Always attempt cleanup if a track exists.

        if track_id:

            try:

                cleanup = delete_track(track_id)

                logger.info(
                    "Cyanite cleanup completed for track %s",
                    track_id
                )

            except Exception as cleanup_error:

                cleanup = {
                    "status": "failed",
                    "track_id": str(track_id),
                    "reason": str(cleanup_error)
                }

                logger.warning(
                    "Unable to delete Cyanite track %s: %s",
                    track_id,
                    cleanup_error
                )

    # Report processing errors after cleanup.

    if processing_error is not None:

        raise CyaniteError(
            f"{processing_error} | "
            f"Cleanup status: {cleanup['status']}"
        ) from processing_error

    # Include cleanup result.

    result["cleanup"] = cleanup

    return result