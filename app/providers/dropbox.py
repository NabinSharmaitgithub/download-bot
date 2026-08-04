import re
from typing import Any

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.providers import BaseProvider, ProviderMetadata

logger = get_logger(__name__)


class DropboxProvider(BaseProvider):
    def name(self) -> str:
        return "dropbox"

    def supports_url(self, url: str) -> bool:
        patterns = [
            r"https?://www\.dropbox\.com/s/[\w-]+/[\w-]+",
            r"https?://www\.dropbox\.com/s/[\w-]+/[\w-]+\?",
            r"https?://www\.dropbox\.com/sh/[\w-]+",
            r"https?://dropbox\.com/s/[\w-]+/[\w-]+",
            r"https?://dropbox\.com/sh/[\w-]+",
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    async def validate_url(self, url: str) -> bool:
        return self.supports_url(url)

    async def get_metadata(self, url: str) -> ProviderMetadata:
        dl_url = self._convert_to_direct_url(url)
        try:
            import httpx
        except ImportError:
            raise ProviderError("httpx not installed", provider=self.name())

        async with httpx.AsyncClient() as client:
            response = await client.head(dl_url, timeout=30, follow_redirects=True)
            file_name = self._extract_filename(response.headers.get("content-disposition", ""))
            file_size = int(response.headers.get("content-length", 0)) or None
            mime_type = response.headers.get("content-type", "application/octet-stream")

            return ProviderMetadata(
                name=file_name or "Unknown",
                type="file",
                size=file_size,
                mime_type=mime_type,
                provider=self.name(),
            )

    async def list_files(self, url: str) -> list[ProviderMetadata]:
        folder_id = self._extract_folder_id(url)
        if not folder_id:
            return []

        try:
            import httpx
        except ImportError:
            raise ProviderError("httpx not installed", provider=self.name())

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.dropboxapi.com/2/sharing/list_folder",
                json={"shared_folder_id": folder_id},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 403:
                raise ProviderError("Access denied", provider=self.name())
            if response.status_code == 404:
                raise ProviderError("Folder not found", provider=self.name())

            data = response.json()
            results = []
            for entry in data.get("entries", []):
                results.append(
                    ProviderMetadata(
                        name=entry.get("name", "Unknown"),
                        type="folder" if entry.get(".tag") == "folder" else "file",
                        size=entry.get("size"),
                        mime_type=entry.get("mime_type"),
                        provider=self.name(),
                    )
                )

            return results

    async def traverse_folder(self, url: str) -> list[ProviderMetadata]:
        return await self.list_files(url)

    async def prepare_download(self, url: str) -> str:
        return self._convert_to_direct_url(url)

    def _convert_to_direct_url(self, url: str) -> str:
        if "www.dropbox.com" in url and "?dl=0" in url:
            return url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
        if "www.dropbox.com" in url:
            return url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
        if "dropbox.com/s/" in url and "?dl=0" in url:
            return url.replace("?dl=0", "?dl=1")
        return url

    def _extract_filename(self, content_disposition: str) -> str | None:
        match = re.search(r'filename[^;=\n]*=((["\']).*?\2|[^;\n]*)', content_disposition)
        if match:
            filename = match.group(1).strip("\'")
            return filename
        return None

    def _extract_folder_id(self, url: str) -> str | None:
        match = re.search(r"https?://www\.dropbox\.com/sh/([\w-]+)", url)
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