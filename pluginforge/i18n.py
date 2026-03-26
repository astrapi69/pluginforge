"""Internationalization support via YAML files."""

import logging
from pathlib import Path
from typing import Any

from pluginforge.config import load_i18n

logger = logging.getLogger(__name__)


class I18n:
    """Manages internationalized strings loaded from YAML files.

    Attributes:
        config_dir: Base config directory containing i18n/ folder.
        default_lang: Fallback language code.
    """

    def __init__(self, config_dir: str | Path, default_lang: str = "en") -> None:
        self.config_dir = Path(config_dir)
        self.default_lang = default_lang
        self._strings: dict[str, dict[str, Any]] = {}

    def load_language(self, lang: str) -> None:
        """Load strings for a language if not already loaded.

        Args:
            lang: Language code (e.g. "en", "de").
        """
        if lang not in self._strings:
            self._strings[lang] = load_i18n(self.config_dir, lang)

    def get_text(self, key: str, lang: str | None = None) -> str:
        """Get a translated string by dot-notation key.

        Falls back to default language if key is not found in requested language.
        Returns the key itself if not found in any language.

        Args:
            key: Dot-notation key (e.g. "common.save").
            lang: Language code, or None for default.

        Returns:
            Translated string, or the key if not found.
        """
        lang = lang or self.default_lang
        self.load_language(lang)

        value = self._resolve_key(key, lang)
        if value is not None:
            return value

        if lang != self.default_lang:
            self.load_language(self.default_lang)
            value = self._resolve_key(key, self.default_lang)
            if value is not None:
                return value

        logger.debug("i18n key not found: %s (lang=%s)", key, lang)
        return key

    def _resolve_key(self, key: str, lang: str) -> str | None:
        """Resolve a dot-notation key in a language's strings.

        Args:
            key: Dot-notation key.
            lang: Language code.

        Returns:
            The resolved string or None.
        """
        data = self._strings.get(lang, {})
        parts = key.split(".")
        for part in parts:
            if isinstance(data, dict):
                data = data.get(part)
            else:
                return None
            if data is None:
                return None
        return str(data) if not isinstance(data, dict) else None
