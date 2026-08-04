from fastapi import APIRouter

from app.api.download_routes import router as download_router
from app.api.routes import router as info_router

router = APIRouter()
router.include_router(info_router)
router.include_router(download_router)