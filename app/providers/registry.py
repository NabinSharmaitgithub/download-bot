from typing import type

from app.providers import BaseProvider
from app.providers.dropbox import DropboxProvider
from app.providers.google_drive import GoogleDriveProvider
from app.providers.terabox import TeraBoxProvider
from app.providers.youtube import YouTubeProvider


class ProviderRegistry:
    _providers: dict[str, type[BaseProvider]] = {}

    @classmethod
    def register(cls, provider_class: type[BaseProvider]) -> None:
        instance = provider_class()
        cls._providers[instance.name()] = provider_class

    @classmethod
    def get_provider(cls, name: str) -> BaseProvider | None:
        provider_class = cls._providers.get(name)
        if provider_class:
            return provider_class()
        return None

    @classmethod
    def detect_provider(cls, url: str) -> BaseProvider | None:
        for name, provider_class in cls._providers.items():
            instance = provider_class()
            if instance.supports_url(url):
                return instance
        return None

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())


ProviderRegistry.register(YouTubeProvider)
ProviderRegistry.register(GoogleDriveProvider)
ProviderRegistry.register(DropboxProvider)
ProviderRegistry.register(TeraBoxProvider)
