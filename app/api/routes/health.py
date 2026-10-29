from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def home():
    return {
        "application": "TuneFinder",
        "status": "running",
        "message": "Welcome to TuneFinder API"
    }


@router.get("/health")
def health():
    return {
        "status": "healthy"
    }
