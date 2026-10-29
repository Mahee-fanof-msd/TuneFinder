import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.recognition_service import SongRecognitionService

router = APIRouter(tags=["recognition"])

recognition_service = SongRecognitionService()

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg"}


@router.post("/recognize")
def recognize_song(audio: UploadFile = File(...)):

    extension = Path(audio.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format"
        )

    temporary_path = None

    try:
        with NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temporary_file:

            temporary_path = temporary_file.name

            while chunk := audio.file.read(1024 * 1024):
                temporary_file.write(chunk)

        return recognition_service.recognize(temporary_path)

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Audio recognition failed"
        )

    finally:
        audio.file.close()

        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
