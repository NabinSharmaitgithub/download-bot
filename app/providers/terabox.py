import re
from typing import Any

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.providers import BaseProvider, ProviderMetadata

logger = get_logger(__name__)


class TeraBoxProvider(BaseProvider):
    def name(self) -> str:
        return "terabox"

    def supports_url(self, url: str) -> bool:
        patterns = [
            r"https?://terabox\.com/s/[\w-]+",
            r"https?://terabox\.com/s/[\w-]+\?",
            r"https?://1024\.terabox\.com/s/[\w-]+",
            r"https?://1024\.terabox\.com/s/[\w-]+\?",
            r"https?://483\.terabox\.com/s/[\w-]+",
            r"https?://terabox\.com/share/[\w-]+",
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    async def validate_url(self, url: str) -> bool:
        if not self.supports_url(url):
            return False
        try:
            import httpx
        except ImportError:
            return False

        async with httpx.AsyncClient() as client:
            response = await client.head(url, timeout=10, follow_redirects=False)
            return response.status_code in (200, 302, 301)

    async def get_metadata(self, url: str) -> ProviderMetadata:
        share_id = self._extract_share_id(url)
        if not share_id:
            raise ProviderError("Invalid TeraBox URL", provider=self.name())

        try:
            import httpx
        except ImportError:
            raise ProviderError("httpx not installed", provider=self.name())

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://terabox.com/api/shared/list",
                params={"shareid": share_id},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )

            if response.status_code == 403:
                raise ProviderError("Access denied", provider=self.name())
            if response.status_code == 404:
                raise ProviderError("Share not found", provider=self.name())

            data = response.json()
            if data.get("errno") != 0:
                raise ProviderError(
                    f"TeraBox API error: {data.get('message', 'Unknown error')}",
                    provider=self.name(),
                )

            return ProviderMetadata(
                name=data.get("name", "Unknown"),
                type="folder",
                provider=self.name(),
            )

    async def list_files(self, url: str) -> list[ProviderMetadata]:
        share_id = self._extract_share_id(url)
        if not share_id:
            return []

        try:
            import httpx
        except ImportError:
            raise ProviderError("httpx not installed", provider=self.name())

        results = []
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://terabox.com/api/shared/list",
                params={"shareid": share_id},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )

            if response.status_code != 200:
                raise ProviderError(f"HTTP {response.status_code}", provider=self.name())

            data = response.json()
            if data.get("errno") != 0:
                raise ProviderError(
                    f"TeraBox API error: {data.get('message', 'Unknown error')}",
                    provider=self.name(),
                )

            for entry in data.get("list", []):
                results.append(
                    ProviderMetadata(
                        name=entry.get("server_filename", "Unknown"),
                        type="folder" if entry.get("isdir") == 1 else "file",
                        size=entry.get("size"),
                        mime_type=entry.get("mime_type"),
                        provider=self.name(),
                    )
                )

        return results

    async def traverse_folder(self, url: str) -> list[ProviderMetadata]:
        return await self.list_files(url)

    async def prepare_download(self, url: str) -> str:
        return url

    def _extract_share_id(self, url: str) -> str | None:
        match = re.search(r"https?://(?:[\w-]+\.)?terabox\.com/s/([\w-]+)", url)
        if match:
            return match.group(1)
        return None

    def map_error(self, error: Exception) -> dict[str, Any]:
        error_lower = str(error).lower()
        if "not found" in error_lower or "404" in error_lower:
            return {"error": "file_not_found", "provider": self.name()}
        if "access denied" in error_lower or "403" in error_lower:
            return {"error": "access_denied", "provider": self.name()}
        return {"error": str(error), "provider": self.name()}
