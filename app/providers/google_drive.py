import re
from typing import Any

from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.providers import BaseProvider, ProviderMetadata

logger = get_logger(__name__)


class GoogleDriveProvider(BaseProvider):
    def name(self) -> str:
        return "google_drive"

    def supports_url(self, url: str) -> bool:
        patterns = [
            r"https?://drive\.google\.com/file/d/[\w-]+",
            r"https?://drive\.google\.com/drive/folders/[\w-]+",
            r"https?://drive\.google\.com/open\?id=[\w-]+",
            r"https?://drive\.google\.uc\.cn/uc\?export=download&id=[\w-]+",
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    async def validate_url(self, url: str) -> bool:
        return self.supports_url(url)

    async def get_metadata(self, url: str) -> ProviderMetadata:
        file_id = self._extract_file_id(url)
        if not file_id:
            raise ProviderError("Invalid Google Drive URL", provider=self.name())

        try:
            import httpx
        except ImportError:
            raise ProviderError("httpx not installed", provider=self.name())

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                params={"fields": "name,size,mimeType,thumbnailLink"},
                timeout=30,
            )

            if response.status_code == 404:
                raise ProviderError("File not found", provider=self.name())
            if response.status_code == 403:
                raise ProviderError("Access denied", provider=self.name())

            data = response.json()
            return ProviderMetadata(
                name=data.get("name", "Unknown"),
                type="file",
                size=data.get("size"),
                mime_type=data.get("mimeType"),
                provider=self.name(),
                thumbnail=data.get("thumbnailLink"),
            )

    async def list_files(self, url: str) -> list[ProviderMetadata]:
        folder_id = self._extract_folder_id(url)
        if not folder_id:
            return []

        try:
            import httpx
        except ImportError:
            raise ProviderError("httpx not installed", provider=self.name())

        results = []
        page_token = None

        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    "q": f"'{folder_id}' in parents and trashed=false",
                    "fields": "nextPageToken,files(id,name,size,mimeType,thumbnailLink)",
                    "pageSize": "1000",
                }
                if page_token:
                    params["pageToken"] = page_token

                response = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    params=params,
                    timeout=30,
                )

                if response.status_code == 403:
                    raise ProviderError("Access denied", provider=self.name())

                data = response.json()
                for file_info in data.get("files", []):
                    results.append(
                        ProviderMetadata(
                            name=file_info.get("name", "Unknown"),
                            type=(
                                "file"
                                if "mimeType" in file_info and "folder" not in file_info["mimeType"]
                                else "folder"
                            ),
                            size=file_info.get("size"),
                            mime_type=file_info.get("mimeType"),
                            provider=self.name(),
                            thumbnail=file_info.get("thumbnailLink"),
                        )
                    )

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        return results

    async def traverse_folder(self, url: str) -> list[ProviderMetadata]:
        return await self.list_files(url)

    async def prepare_download(self, url: str) -> str:
        file_id = self._extract_file_id(url)
        if not file_id:
            raise ProviderError("Invalid Google Drive URL", provider=self.name())
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    def _extract_file_id(self, url: str) -> str | None:
        patterns = [
            r"https?://drive\.google\.com/file/d/([\w-]+)",
            r"https?://drive\.google\.com/open\?id=([\w-]+)",
            r"https?://drive\.google\.uc\.cn/uc\?export=download&id=([\w-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _extract_folder_id(self, url: str) -> str | None:
        match = re.search(r"https?://drive\.google\.com/drive/folders/([\w-]+)", url)
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