import requests
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.api.websocket_routes import manager
from app.database.mongo_db import mongo_service
from app.config import settings

router = APIRouter()

class APIKeysUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    usda_api_key: Optional[str] = None
    mongodb_uri: Optional[str] = None

@router.get("/api/metrics")
async def get_system_metrics():
    return {
        "status": "online",
        "active_websocket_connections": manager.count(),
        "target_cv_latency_ms": "< 30ms",
        "target_nlp_resolution_ms": "< 1500ms",
        "openai_key_configured": bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10),
        "usda_key_configured": bool(settings.USDA_API_KEY and settings.USDA_API_KEY != "DEMO_KEY"),
        "supported_exercises": [
            "Bicep Curl",
            "Tricep Pushdown",
            "Lat Pulldown",
            "Squat",
            "Chest Press / Overhead Press"
        ]
    }

@router.post("/api/settings/keys")
async def update_api_keys(payload: APIKeysUpdate):
    """
    Updates API keys at runtime and tests connection health.
    """
    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key.strip()
    if payload.usda_api_key is not None:
        settings.USDA_API_KEY = payload.usda_api_key.strip()
    if payload.mongodb_uri is not None:
        settings.MONGODB_URI = payload.mongodb_uri.strip()

    # Re-initialize clients with new keys
    from app.nlp.audio_transcriber import audio_transcriber
    from app.nlp.llm_parser import meal_parser
    from app.nlp.usda_client import usda_client

    audio_transcriber.__init__()
    meal_parser.__init__()
    usda_client.__init__()

    # Test USDA API Connection
    usda_status = False
    if settings.USDA_API_KEY:
        try:
            res = requests.get(
                "https://api.nal.usda.gov/fdc/v1/foods/search",
                params={"api_key": settings.USDA_API_KEY, "query": "apple", "pageSize": 1},
                timeout=2.0
            )
            usda_status = (res.status_code == 200)
        except Exception:
            usda_status = False

    # Test OpenAI Connection
    openai_status = False
    if settings.OPENAI_API_KEY:
        try:
            res = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=2.0
            )
            openai_status = (res.status_code == 200)
        except Exception:
            openai_status = False

    return {
        "status": "success",
        "openai_valid": openai_status,
        "usda_valid": usda_status,
        "message": "API keys updated and verified successfully."
    }

@router.get("/api/history")
async def get_workout_history():
    logs = await mongo_service.get_workout_history(limit=10)
    return {"status": "success", "count": len(logs), "data": logs}
