"""Tests for pluginforge.manager module."""

from pathlib import Path

import pytest

from pluginforge.base import BasePlugin
from pluginforge.discovery import CircularDependencyError
from pluginforge.manager import PluginManager
from tests.conftest import (
    AnotherPlugin,
    CircularA,
    CircularB,
    DependentPlugin,
    FailingInitPlugin,
    MissingDepPlugin,
    SamplePlugin,
)


class TestPluginManager:
    def test_load_app_config(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        config = pm.get_app_config()
        assert config["app"]["name"] == "TestApp"

    def test_get_plugin_config(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        config = pm.get_plugin_config("sample")
        assert config["greeting"] == "Hello"

    def test_get_missing_plugin_config(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        config = pm.get_plugin_config("nonexistent")
        assert config == {}

    def test_register_plugins(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin, AnotherPlugin])
        assert len(pm.get_active_plugins()) == 2

    def test_register_with_dependency(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin, DependentPlugin])
        active_names = [p.name for p in pm.get_active_plugins()]
        assert "sample" in active_names
        assert "dependent" in active_names

    def test_missing_dependency_skipped(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        # Update config to enable missing_dep
        import yaml

        config = {
            "app": {"name": "TestApp", "version": "1.0.0"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["missing_dep"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([MissingDepPlugin])
        assert len(pm.get_active_plugins()) == 0

    def test_circular_dependency_raises(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["circular_a", "circular_b"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path))
        with pytest.raises(CircularDependencyError):
            pm.register_plugins([CircularA, CircularB])

    def test_deactivate_all(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin, AnotherPlugin])
        assert len(pm.get_active_plugins()) == 2
        pm.deactivate_all()
        assert len(pm.get_active_plugins()) == 0

    def test_get_plugin(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        plugin = pm.get_plugin("sample")
        assert plugin is not None
        assert plugin.name == "sample"

    def test_get_plugin_not_found(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        assert pm.get_plugin("nonexistent") is None

    def test_deactivate_plugin(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        pm.deactivate_plugin("sample")
        active_names = [p.name for p in pm.get_active_plugins()]
        assert "sample" not in active_names

    def test_activate_plugin(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        pm.deactivate_plugin("sample")
        pm.activate_plugin("sample")
        active_names = [p.name for p in pm.get_active_plugins()]
        assert "sample" in active_names

    def test_failing_init_skipped(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["failing_init"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([FailingInitPlugin])
        assert len(pm.get_active_plugins()) == 0

    def test_disabled_plugin_filtered(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["sample", "another"],
                "disabled": ["another"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin, AnotherPlugin])
        active_names = [p.name for p in pm.get_active_plugins()]
        assert "sample" in active_names
        assert "another" not in active_names

    def test_get_text(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        assert pm.get_text("common.save", "en") == "Save"
        assert pm.get_text("common.save", "de") == "Speichern"

    def test_get_text_fallback(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        # Key that does not exist returns the key itself
        assert pm.get_text("nonexistent.key", "en") == "nonexistent.key"

    def test_plugin_config_applied(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        plugin = pm.get_plugin("sample")
        assert plugin is not None
        assert plugin.config.get("greeting") == "Hello"

    def test_missing_config_path(self, tmp_path: Path) -> None:
        pm = PluginManager(str(tmp_path / "nonexistent" / "app.yaml"))
        assert pm.get_app_config() == {}

    def test_call_hook_not_found(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        result = pm.call_hook("nonexistent_hook")
        assert result == []

    def test_register_hookspecs(self, app_yaml_path: Path) -> None:
        import pluggy

        hookspec = pluggy.HookspecMarker("testapp.plugins")

        class MySpec:
            @hookspec
            def my_hook(self, value: int) -> int: ...

        pm = PluginManager(str(app_yaml_path))
        pm.register_hookspecs(MySpec)
        result = pm.call_hook("my_hook", value=42)
        assert result == []

    def test_call_hook_with_implementation(self, app_yaml_path: Path) -> None:
        import pluggy

        hookspec = pluggy.HookspecMarker("testapp.plugins")
        hookimpl = pluggy.HookimplMarker("testapp.plugins")

        class MySpec:
            @hookspec
            def my_hook(self) -> str: ...

        class HookPlugin(BasePlugin):
            name = "hook_plugin"

            @hookimpl
            def my_hook(self) -> str:
                return "hello"

        pm = PluginManager(str(app_yaml_path))
        pm.register_hookspecs(MySpec)

        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["hook_plugin"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path))
        pm.register_hookspecs(MySpec)
        pm.register_plugins([HookPlugin])
        result = pm.call_hook("my_hook")
        assert "hello" in result

    def test_collect_migrations(self, app_yaml_path: Path, tmp_path: Path) -> None:
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        class MigPlugin(BasePlugin):
            name = "sample"
            _dir = str(migrations_dir)

            def get_migrations_dir(self) -> str | None:
                return self._dir

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([MigPlugin])
        result = pm.collect_migrations()
        assert "sample" in result

    def test_activate_nonexistent_plugin(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.activate_plugin("nonexistent")  # should not raise

    def test_deactivate_nonexistent_plugin(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.deactivate_plugin("nonexistent")  # should not raise

    def test_discover_plugins_empty_group(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.discover_plugins()  # no entry points registered, should not fail
        assert len(pm.get_active_plugins()) == 0

    def test_failing_activate_skipped(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        import yaml

        from tests.conftest import FailingActivatePlugin

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["failing_activate"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([FailingActivatePlugin])
        assert len(pm.get_active_plugins()) == 0

    def test_default_entry_point_group(self, tmp_path: Path) -> None:
        import yaml

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config = {"app": {"name": "TestApp"}}
        with open(config_dir / "app.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(config_dir / "app.yaml"))
        assert pm._entry_point_group == "pluginforge.plugins"
