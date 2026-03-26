"""Tests for pluginforge.i18n module."""

from pathlib import Path

from pluginforge.i18n import I18n


class TestI18n:
    def test_get_text_english(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        assert i18n.get_text("common.save") == "Save"
        assert i18n.get_text("common.cancel") == "Cancel"

    def test_get_text_german(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        assert i18n.get_text("common.save", "de") == "Speichern"
        assert i18n.get_text("common.cancel", "de") == "Abbrechen"

    def test_fallback_to_default_language(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        # French does not exist, should fall back to English
        assert i18n.get_text("common.save", "fr") == "Save"

    def test_missing_key_returns_key(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        assert i18n.get_text("nonexistent.key") == "nonexistent.key"

    def test_nested_key(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        assert i18n.get_text("plugins.sample.label") == "Sample Plugin"
        assert i18n.get_text("plugins.sample.label", "de") == "Beispiel-Plugin"

    def test_app_title(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        assert i18n.get_text("app.title") == "Test App"
        assert i18n.get_text("app.title", "de") == "Test-App"

    def test_default_lang_used_when_none(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="de")
        assert i18n.get_text("common.save") == "Speichern"

    def test_partial_key_returns_key(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        # "common" alone resolves to a dict, should return the key
        assert i18n.get_text("common") == "common"

    def test_language_caching(self, tmp_config_dir: Path) -> None:
        i18n = I18n(tmp_config_dir, default_lang="en")
        i18n.get_text("common.save", "en")
        # Second call should use cache
        assert "en" in i18n._strings
        i18n.get_text("common.save", "en")
        assert i18n.get_text("common.save", "en") == "Save"
