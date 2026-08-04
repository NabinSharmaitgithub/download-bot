from app.providers import BaseProvider
from app.providers.dropbox import DropboxProvider
from app.providers.google_drive import GoogleDriveProvider
from app.providers.terabox import TeraBoxProvider
from app.providers.youtube import YouTubeProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[BaseProvider]] = {}

    def register(self, name: str, provider_cls: type[BaseProvider]) -> None:
        self._providers[name] = provider_cls

    def get(self, name: str) -> type[BaseProvider] | None:
        return self._providers.get(name)

    def get_all(self) -> dict[str, type[BaseProvider]]:
        return dict(self._providers)

    @property
    def names(self) -> list[str]:
        return list(self._providers.keys())


def create_default_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("dropbox", DropboxProvider)
    registry.register("google_drive", GoogleDriveProvider)
    registry.register("terabox", TeraBoxProvider)
    registry.register("youtube", YouTubeProvider)
    return registry


registry = create_default_registry()
