import shutil
import time
from pathlib import Path

from fastapi import APIRouter

from app.config import settings
from app.llm import get_provider
from app.ocr import is_tesseract_available

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    provider = get_provider()
    return {
        "status": "ok",
        "provider": provider.name,
        "model": provider.model_id,
    }


@router.get("/health/detailed")
async def health_detailed():
    provider = get_provider()

    checks = {
        "llm_provider": {
            "name": provider.name,
            "model": provider.model_id,
            "status": "ok",
        },
        "tesseract_ocr": {
            "enabled": settings.use_ocr,
            "available": is_tesseract_available(),
        },
        "java": {
            "available": shutil.which("java") is not None,
        },
        "plantuml": {
            "available": Path("plantuml.jar").exists(),
        },
    }

    all_ok = checks["llm_provider"]["status"] == "ok"

    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
        "config": {
            "provider": settings.llm_provider.value,
            "fallback": settings.llm_fallback_provider.value if settings.llm_fallback_provider else None,
            "max_tokens": settings.max_tokens,
            "max_image_dimension": settings.max_image_dimension,
            "ocr_enabled": settings.use_ocr,
        },
    }
