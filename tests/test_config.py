"""Tests for pluginforge.config module."""

from pathlib import Path

import yaml

from pluginforge.config import load_app_config, load_i18n, load_plugin_config, load_yaml


class TestLoadYaml:
    def test_load_existing_file(self, tmp_path: Path) -> None:
        data = {"key": "value", "nested": {"a": 1}}
        path = tmp_path / "test.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        result = load_yaml(path)
        assert result == data

    def test_load_missing_file(self, tmp_path: Path) -> None:
        result = load_yaml(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_load_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        result = load_yaml(path)
        assert result == {}

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "invalid.yaml"
        path.write_text("{{invalid: yaml: content", encoding="utf-8")
        result = load_yaml(path)
        assert result == {}

    def test_load_non_dict_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "list.yaml"
        path.write_text("- item1\n- item2", encoding="utf-8")
        result = load_yaml(path)
        assert result == {}


class TestLoadAppConfig:
    def test_load_app_config(self, app_yaml_path: Path) -> None:
        config = load_app_config(app_yaml_path)
        assert config["app"]["name"] == "TestApp"

    def test_load_missing_app_config(self, tmp_path: Path) -> None:
        config = load_app_config(tmp_path / "missing.yaml")
        assert config == {}


class TestLoadPluginConfig:
    def test_load_existing_plugin_config(self, tmp_config_dir: Path) -> None:
        config = load_plugin_config(tmp_config_dir, "sample")
        assert config["greeting"] == "Hello"
        assert config["max_retries"] == 3

    def test_load_missing_plugin_config(self, tmp_config_dir: Path) -> None:
        config = load_plugin_config(tmp_config_dir, "nonexistent")
        assert config == {}


class TestLoadI18n:
    def test_load_existing_language(self, tmp_config_dir: Path) -> None:
        strings = load_i18n(tmp_config_dir, "en")
        assert strings["common"]["save"] == "Save"

    def test_load_missing_language(self, tmp_config_dir: Path) -> None:
        strings = load_i18n(tmp_config_dir, "fr")
        assert strings == {}
