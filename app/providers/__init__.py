from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderMetadata:
    name: str
    type: str
    size: int | None = None
    mime_type: str | None = None
    provider: str | None = None
    thumbnail: str | None = None
    parent_folder: str | None = None
    children: list["ProviderMetadata"] | None = None


class BaseProvider(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def supports_url(self, url: str) -> bool: ...

    @abstractmethod
    async def validate_url(self, url: str) -> bool: ...

    @abstractmethod
    async def get_metadata(self, url: str) -> ProviderMetadata: ...

    @abstractmethod
    async def list_files(self, url: str) -> list[ProviderMetadata]: ...

    @abstractmethod
    async def traverse_folder(self, url: str) -> list[ProviderMetadata]: ...

    @abstractmethod
    async def prepare_download(self, url: str) -> str: ...

    @abstractmethod
    def map_error(self, error: Exception) -> dict[str, Any]: ...