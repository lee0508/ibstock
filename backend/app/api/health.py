from fastapi import APIRouter

from app.core.config import settings
from app.core.database import database_exists


router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "database_exists": database_exists(),
        "ollama_host": settings.ollama_host,
    }
