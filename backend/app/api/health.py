from fastapi import APIRouter
import httpx

from app.core.config import settings
from app.core.database import database_exists


router = APIRouter()


@router.get("/health")
async def health():
    ollama = {
        "host": settings.ollama_host,
        "reachable": False,
        "model_count": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.ollama_host}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            ollama["reachable"] = True
            ollama["model_count"] = len(models)
    except Exception as exc:
        ollama["error"] = str(exc)

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "database_exists": database_exists(),
        "ollama": ollama,
    }
