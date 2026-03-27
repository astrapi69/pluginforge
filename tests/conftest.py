"""Shared fixtures for PluginForge tests."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from pluginforge.base import BasePlugin


# --- Sample Plugin Classes ---


class SamplePlugin(BasePlugin):
    name = "sample"
    version = "1.0.0"
    description = "A sample plugin for testing"
    depends_on: list[str] = []


class AnotherPlugin(BasePlugin):
    name = "another"
    version = "0.2.0"
    description = "Another test plugin"
    depends_on: list[str] = []


class DependentPlugin(BasePlugin):
    name = "dependent"
    version = "1.0.0"
    description = "Depends on sample"
    depends_on = ["sample"]


class MissingDepPlugin(BasePlugin):
    name = "missing_dep"
    version = "1.0.0"
    depends_on = ["nonexistent"]


class CircularA(BasePlugin):
    name = "circular_a"
    depends_on = ["circular_b"]


class CircularB(BasePlugin):
    name = "circular_b"
    depends_on = ["circular_a"]


class FailingInitPlugin(BasePlugin):
    name = "failing_init"

    def init(self, app_config: dict[str, Any], plugin_config: dict[str, Any]) -> None:
        raise RuntimeError("Init failed")


class FailingActivatePlugin(BasePlugin):
    name = "failing_activate"

    def activate(self) -> None:
        raise RuntimeError("Activate failed")


class FailingDeactivatePlugin(BasePlugin):
    name = "failing_deactivate"

    def deactivate(self) -> None:
        raise RuntimeError("Deactivate failed")


class OldApiPlugin(BasePlugin):
    name = "old_api"
    api_version = "0"


# --- Fixtures ---


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory with app.yaml."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "plugins").mkdir()
    (config_dir / "i18n").mkdir()

    app_config = {
        "app": {
            "name": "TestApp",
            "version": "1.0.0",
            "default_language": "en",
        },
        "plugins": {
            "entry_point_group": "testapp.plugins",
            "enabled": ["sample", "another", "dependent"],
            "disabled": [],
        },
    }
    with open(config_dir / "app.yaml", "w", encoding="utf-8") as f:
        yaml.dump(app_config, f)

    sample_config = {"greeting": "Hello", "max_retries": 3}
    with open(config_dir / "plugins" / "sample.yaml", "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)

    en_strings = {
        "app": {"title": "Test App"},
        "common": {"save": "Save", "cancel": "Cancel"},
        "plugins": {"sample": {"label": "Sample Plugin"}},
    }
    with open(config_dir / "i18n" / "en.yaml", "w", encoding="utf-8") as f:
        yaml.dump(en_strings, f)

    de_strings = {
        "app": {"title": "Test-App"},
        "common": {"save": "Speichern", "cancel": "Abbrechen"},
        "plugins": {"sample": {"label": "Beispiel-Plugin"}},
    }
    with open(config_dir / "i18n" / "de.yaml", "w", encoding="utf-8") as f:
        yaml.dump(de_strings, f)

    return config_dir


@pytest.fixture
def app_yaml_path(tmp_config_dir: Path) -> Path:
    return tmp_config_dir / "app.yaml"
