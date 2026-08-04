import re
from typing import Any

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.providers import BaseProvider, ProviderMetadata

logger = get_logger(__name__)


class YouTubeProvider(BaseProvider):
    def name(self) -> str:
        return "youtube"

    def supports_url(self, url: str) -> bool:
        patterns = [
            r"https?://(www\.)?youtube\.com/watch\?v=[\w-]+",
            r"https?://(www\.)?youtube\.com/shorts/[\w-]+",
            r"https?://(www\.)?youtube\.com/playlist\?list=[\w-]+",
            r"https?://(www\.)?youtube\.com/channel/[\w-]+",
            r"https?://youtu\.be/[\w-]+",
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    async def validate_url(self, url: str) -> bool:
        return self.supports_url(url)

    async def get_metadata(self, url: str) -> ProviderMetadata:
        try:
            import yt_dlp
        except ImportError:
            raise ProviderError("yt-dlp not installed", provider=self.name())

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise ProviderError("Failed to extract YouTube metadata", provider=self.name())

                return ProviderMetadata(
                    name=info.get("title", "Unknown"),
                    type="video",
                    size=info.get("filesize") or info.get("filesize_approx"),
                    mime_type=info.get("ext") or "video/mp4",
                    provider=self.name(),
                    thumbnail=info.get("thumbnail"),
                )
        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(
                f"YouTube metadata extraction failed: {str(e)}", provider=self.name()
            )

    async def list_files(self, url: str) -> list[ProviderMetadata]:
        try:
            import yt_dlp
        except ImportError:
            raise ProviderError("yt-dlp not installed", provider=self.name())

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return []

                results = []
                if "entries" in info:
                    for entry in info["entries"]:
                        if entry:
                            results.append(
                                ProviderMetadata(
                                    name=entry.get("title", "Unknown"),
                                    type="video",
                                    size=entry.get("filesize") or entry.get("filesize_approx"),
                                    mime_type=entry.get("ext") or "video/mp4",
                                    provider=self.name(),
                                    thumbnail=entry.get("thumbnail"),
                                )
                            )

                return results
        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(f"YouTube file listing failed: {str(e)}", provider=self.name())

    async def traverse_folder(self, url: str) -> list[ProviderMetadata]:
        return await self.list_files(url)

    async def prepare_download(self, url: str) -> str:
        return url

    def map_error(self, error: Exception) -> dict[str, Any]:
        error_lower = str(error).lower()
        if "not found" in error_lower or "404" in error_lower:
            return {"error": "file_not_found", "provider": self.name()}
        if "private" in error_lower or "unavailable" in error_lower:
            return {"error": "access_denied", "provider": self.name()}
        if "age" in error_lower or "restricted" in error_lower:
            return {"error": "age_restricted", "provider": self.name()}
        return {"error": str(error), "provider": self.name()}
