import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Localization:
    def __init__(self, default_locale: str = "en") -> None:
        self.default_locale = default_locale
        self._translations: dict[str, dict[str, Any]] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        locales_dir = Path(__file__).parent.parent / "locales"
        if not locales_dir.exists():
            logger.warning("locales_directory_not_found", path=str(locales_dir))
            return

        for locale_file in locales_dir.glob("*.json"):
            locale = locale_file.stem
            try:
                with open(locale_file, encoding="utf-8") as f:
                    self._translations[locale] = json.load(f)
                logger.info("locale_loaded", locale=locale, keys=len(self._translations[locale]))
            except Exception as e:
                logger.error("locale_load_failed", locale=locale, error=str(e))

    def get(self, key: str, locale: str | None = None, **params) -> str:
        locale = locale or self.default_locale
        translations = self._translations.get(
            locale, self._translations.get(self.default_locale, {})
        )

        keys = key.split(".")
        value: Any = translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
            if value is None:
                break

        if value is None:
            logger.warning("translation_missing", key=key, locale=locale)
            return key

        if isinstance(value, str):
            try:
                return value.format(**params)
            except KeyError as e:
                logger.warning("translation_param_missing", key=key, param=str(e))
                return value

        return str(value)

    def has(self, key: str, locale: str | None = None) -> bool:
        locale = locale or self.default_locale
        translations = self._translations.get(
            locale, self._translations.get(self.default_locale, {})
        )

        keys = key.split(".")
        value: Any = translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return False
        return value is not None

    @property
    def available_locales(self) -> list[str]:
        return list(self._translations.keys())


_localization: Localization | None = None


def get_localization() -> Localization:
    global _localization
    if _localization is None:
        settings = get_settings()
        _localization = Localization(default_locale="en")
    return _localization


def init_localization(default_locale: str = "en") -> Localization:
    global _localization
    _localization = Localization(default_locale=default_locale)
    return _localization