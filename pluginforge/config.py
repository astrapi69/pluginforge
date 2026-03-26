"""YAML configuration loading and merging."""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content, or empty dict if file is missing or empty.
    """
    path = Path(path)
    if not path.exists():
        logger.debug("Config file not found, using empty defaults: %s", path)
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError as e:
        logger.warning("Failed to parse YAML file %s: %s", path, e)
        return {}


def load_app_config(config_path: str | Path) -> dict[str, Any]:
    """Load the main application config.

    Args:
        config_path: Path to app.yaml.

    Returns:
        Application configuration dict.
    """
    return load_yaml(config_path)


def load_plugin_config(config_dir: str | Path, plugin_name: str) -> dict[str, Any]:
    """Load plugin-specific configuration from config/plugins/{name}.yaml.

    Args:
        config_dir: Base config directory (parent of plugins/).
        plugin_name: Name of the plugin.

    Returns:
        Plugin configuration dict.
    """
    path = Path(config_dir) / "plugins" / f"{plugin_name}.yaml"
    return load_yaml(path)


def load_i18n(config_dir: str | Path, lang: str) -> dict[str, Any]:
    """Load i18n strings for a specific language.

    Args:
        config_dir: Base config directory (parent of i18n/).
        lang: Language code (e.g. "en", "de").

    Returns:
        i18n strings dict.
    """
    path = Path(config_dir) / "i18n" / f"{lang}.yaml"
    return load_yaml(path)
