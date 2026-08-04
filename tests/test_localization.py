from unittest.mock import MagicMock, patch

import pytest

from app.core.localization import Localization, get_localization, init_localization


class TestLocalization:
    def test_localization_loads_translations(self):
        with patch("app.core.localization.Path") as mock_path:
            mock_locales_dir = MagicMock()
            mock_path.return_value.parent.parent.__truediv__.return_value = mock_locales_dir
            mock_locales_dir.exists.return_value = True
            mock_locales_dir.glob.return_value = []

            i18n = Localization(default_locale="en")
            assert i18n.default_locale == "en"

    def test_get_returns_key_when_missing(self):
        i18n = Localization(default_locale="en")
        i18n._translations = {"en": {"common": {"start": "Welcome!"}}}

        result = i18n.get("common.start")
        assert result == "Welcome!"

        result = i18n.get("nonexistent.key")
        assert result == "nonexistent.key"

    def test_get_with_params(self):
        i18n = Localization(default_locale="en")
        i18n._translations = {"en": {"download": {"downloading": "Progress: {progress}%"}}}

        result = i18n.get("download.downloading", progress=50)
        assert result == "Progress: 50%"

    def test_get_fallback_to_default_locale(self):
        i18n = Localization(default_locale="en")
        i18n._translations = {
            "en": {"common": {"start": "Welcome!"}},
            "ne": {"common": {"start": "\u0938\u094d\u0935\u093e\u0917\u0924 \u091b!"}},
        }

        result = i18n.get("common.start", locale="ne")
        assert result == "\u0938\u094d\u0935\u093e\u0917\u0924 \u091b!"

        result = i18n.get("common.start", locale="fr")
        assert result == "Welcome!"

    def test_has_returns_true_for_existing_key(self):
        i18n = Localization(default_locale="en")
        i18n._translations = {"en": {"common": {"start": "Welcome!"}}}

        assert i18n.has("common.start") is True
        assert i18n.has("common.nonexistent") is False
        assert i18n.has("nonexistent") is False

    def test_available_locales(self):
        i18n = Localization(default_locale="en")
        i18n._translations = {"en": {}, "ne": {}, "es": {}}

        assert set(i18n.available_locales) == {"en", "ne", "es"}

    def test_get_localization_singleton(self):
        i18n1 = get_localization()
        i18n2 = get_localization()
        assert i18n1 is i18n2

    def test_init_localization_creates_new(self):
        i18n = init_localization(default_locale="ne")
        assert i18n.default_locale == "ne"
        assert get_localization() is i18n