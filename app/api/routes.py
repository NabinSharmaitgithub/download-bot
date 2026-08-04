from fastapi import APIRouter

router = APIRouter()


@router.get("/info", tags=["info"])
async def api_info() -> dict[str, str]:
    return {
        "name": "Download Bot API",
        "version": "0.1.0",
        "description": "Telegram download bot with multi-provider support",
    }