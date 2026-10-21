from fastapi import APIRouter, UploadFile, File
from app.services.song import SongService

router = APIRouter()

song_service = SongService()


@router.post("/identify")
async def identify_song(audio: UploadFile = File(...)):
    result = await song_service.identify_song(audio)
    return result