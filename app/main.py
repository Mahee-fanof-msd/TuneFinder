
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, Field

from app.services.song_recognition_service import SongRecognitionService
from app.services.cyanite_service import (
    submit_audio, get_analysis, get_similar_tracks, CyaniteError,
)
from app.services.groq_service import (
    interpret_music_request, recommend_music, GroqServiceError,
)
from app.services.tavily_service import search_music, TavilyError
from app.services.music_verification_service import (
    verify_recommendations, MusicVerificationError,
)


app = FastAPI(
    title="TuneFinder API",
    description=(
        "Music recognition using SQLite and AudD, "
        "Cyanite similar-song recommendations, and "
        "Groq/Tavily preference-based music discovery."
    ),
    version="1.4.0",
)
recognition_service = SongRecognitionService()


class MusicPreferenceRequest(BaseModel):
    preference: str = Field(min_length=1, max_length=500)


@app.get("/")
def home():
    return {"message": "Welcome to TuneFinder API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/recognize")
async def recognize_song(audio: UploadFile = File(...)):
    extension = Path(audio.filename or "").suffix.lower()
    if extension not in (".wav", ".mp3", ".m4a"):
        raise HTTPException(status_code=400, detail="Unsupported audio format.")

    temporary_path = None
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=extension
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(audio_bytes)

        return recognition_service.recognize(temporary_path)
    except HTTPException:
        raise
    except Exception as error:
        print(f"Song recognition error: {error}")
        raise HTTPException(
            status_code=500, detail="Song recognition failed."
        ) from error
    finally:
        await audio.close()
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


@app.post("/recommend")
async def recommend_song(audio: UploadFile = File(...)):
    extension = Path(audio.filename or "").suffix.lower()
    if extension != ".wav":
        raise HTTPException(
            status_code=400, detail="Please upload a WAV recording."
        )
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=400, detail="Audio recording is empty."
            )
        if len(audio_bytes) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Audio recording exceeds the 20 MB limit.",
            )
        track_id = submit_audio(audio_bytes)
        return {
            "status": "processing",
            "track_id": track_id,
            "message": (
                "Recording uploaded successfully. "
                "Cyanite is analyzing the audio."
            ),
        }
    except HTTPException:
        raise
    except CyaniteError as error:
        print(f"Cyanite upload error: {error}")
        raise HTTPException(status_code=502, detail=str(error)) from error
    finally:
        await audio.close()


@app.get("/recommend/{track_id}")
def get_recommendation_analysis(track_id: str):
    try:
        return get_analysis(track_id)
    except CyaniteError as error:
        print(f"Cyanite analysis error: {error}")
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/recommend/{track_id}/similar")
def get_recommendation_similar_tracks(track_id: str):
    try:
        analysis_result = get_analysis(track_id)
        if analysis_result["status"] == "processing":
            return {
                "status": "processing",
                "track_id": track_id,
                "message": "Cyanite analysis is still running. Please try again shortly.",
            }
        if analysis_result["status"] == "analysis_failed":
            return {
                "status": "analysis_failed",
                "track_id": track_id,
                "message": "Cyanite audio analysis failed.",
            }
        return get_similar_tracks(track_id, limit=5)
    except CyaniteError as error:
        print(f"Cyanite similarity error: {error}")
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/discover")
def discover_music(request: MusicPreferenceRequest):
    preference = request.preference.strip()
    if not preference:
        raise HTTPException(status_code=400, detail="Enter a music preference.")

    try:
        interpretation = interpret_music_request(preference)
        interpreted = interpretation["interpreted_request"]
        tavily_result = search_music(
            interpreted["search_query"], max_results=8
        )
        sources = tavily_result.get("results", [])
        if not sources:
            return {
                "status": "success",
                "interpretation": interpreted,
                "total": 0,
                "recommendations": [],
                "unverified": [],
                "rejected": [],
            }

        proposed = recommend_music(
            user_preference=preference,
            interpreted_request=interpreted,
            search_results=sources,
        ).get("recommendations", [])

        if not proposed:
            return {
                "status": "success",
                "interpretation": interpreted,
                "total": 0,
                "recommendations": [],
                "unverified": [],
                "rejected": [],
            }

        verified = verify_recommendations(preference, proposed)
        return {"interpretation": interpreted, **verified}
    except (GroqServiceError, TavilyError, MusicVerificationError) as error:
        print(f"Music discovery error: {error}")
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:
        print(f"Unexpected music discovery error: {error}")
        raise HTTPException(
            status_code=500, detail="Music discovery failed."
        ) from error


@app.post("/cyanite/webhook")
async def cyanite_webhook(payload: dict):
    print("Cyanite webhook received:", payload)
    return {"status": "received"}
