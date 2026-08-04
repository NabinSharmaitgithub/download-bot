import hashlib
import hmac
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse, Response

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.download import download_manager, queue_manager
from app.providers.registry import ProviderRegistry

logger = get_logger(__name__)
router = APIRouter(prefix="/downloads", tags=["downloads"])

settings = get_settings()


@router.post("/url")
async def process_url(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")

    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    provider = ProviderRegistry.detect_provider(url)
    if not provider:
        raise HTTPException(status_code=400, detail="Unsupported or invalid URL")

    try:
        await provider.validate_url(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"provider": provider.name(), "url": url, "status": "validated"}


@router.post("/queue")
async def queue_download(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")

    url = body.get("url")
    user_id = body.get("user_id")
    quality = body.get("quality")
    audio_format = body.get("audio_format")

    if not url or not user_id:
        raise HTTPException(status_code=400, detail="url and user_id are required")

    provider = ProviderRegistry.detect_provider(url)
    if not provider:
        raise HTTPException(status_code=400, detail="Unsupported URL")

    try:
        can_add = await queue_manager.can_add_to_queue(user_id)
        if not can_add:
            raise HTTPException(status_code=429, detail="Queue is full")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        result = await download_manager.start_download(
            user_id=user_id,
            url=url,
            provider=provider.name(),
            quality=quality,
            audio_format=audio_format,
        )
        return {"download_id": result.download_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{download_id}")
async def get_download_status(download_id: str) -> dict[str, Any]:
    return {"download_id": download_id, "status": "not_found"}


@router.get("/signed-url/{download_id}")
async def get_signed_url(
    download_id: str,
    token: str = Query(...),
) -> Response:
    expected_token = _generate_signed_token(download_id)
    if not hmac.compare_digest(token, expected_token):
        raise ForbiddenError("Invalid or expired download link")

    file_path = _get_file_path(download_id)
    if not file_path or not file_path.exists():
        raise NotFoundError("File not found")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.get("/stream/{download_id}")
async def stream_download(
    download_id: str,
    token: str = Query(...),
) -> Response:
    expected_token = _generate_signed_token(download_id)
    if not hmac.compare_digest(token, expected_token):
        raise ForbiddenError("Invalid or expired download link")

    file_path = _get_file_path(download_id)
    if not file_path or not file_path.exists():
        raise NotFoundError("File not found")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


def _generate_signed_token(download_id: str) -> str:
    timestamp = int(time.time())
    message = f"{download_id}:{timestamp}:{settings.download_link_expiration}"
    signature = hmac.new(
        settings.download_link_hmac_secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{timestamp}.{signature}"


def _get_file_path(download_id: str) -> Any | None:
    import os
    from pathlib import Path

    download_dir = Path(settings.download_directory)
    if not download_dir.exists():
        return None

    for file_path in download_dir.iterdir():
        if file_path.is_file() and download_id in file_path.name:
            return file_path

    return None


@router.get("/health")
async def download_health() -> dict[str, str]:
    return {"status": "healthy", "service": "download"}
