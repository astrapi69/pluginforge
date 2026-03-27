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
    FailingActivatePlugin,
    FailingInitPlugin,
    MissingDepPlugin,
    OldApiPlugin,
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

    # --- #7 reload_config ---

    def test_reload_config(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        import yaml

        pm = PluginManager(str(app_yaml_path))
        assert pm.get_app_config()["app"]["name"] == "TestApp"

        new_config = {
            "app": {"name": "UpdatedApp", "default_language": "de"},
            "plugins": {"entry_point_group": "testapp.plugins"},
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(new_config, f)

        pm.reload_config()
        assert pm.get_app_config()["app"]["name"] == "UpdatedApp"

    # --- #6 pre_activate callback ---

    def test_pre_activate_allows(self, app_yaml_path: Path) -> None:
        def allow_all(plugin: BasePlugin, config: dict) -> bool:
            return True

        pm = PluginManager(str(app_yaml_path), pre_activate=allow_all)
        pm.register_plugins([SamplePlugin])
        assert len(pm.get_active_plugins()) == 1

    def test_pre_activate_rejects(self, app_yaml_path: Path) -> None:
        def reject_all(plugin: BasePlugin, config: dict) -> bool:
            return False

        pm = PluginManager(str(app_yaml_path), pre_activate=reject_all)
        pm.register_plugins([SamplePlugin])
        assert len(pm.get_active_plugins()) == 0

    def test_pre_activate_selective(self, app_yaml_path: Path) -> None:
        def only_sample(plugin: BasePlugin, config: dict) -> bool:
            return plugin.name == "sample"

        pm = PluginManager(str(app_yaml_path), pre_activate=only_sample)
        pm.register_plugins([SamplePlugin, AnotherPlugin])
        active_names = [p.name for p in pm.get_active_plugins()]
        assert "sample" in active_names
        assert "another" not in active_names

    # --- #8 register_plugin (single instance) ---

    def test_register_plugin_instance(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        plugin = SamplePlugin()
        pm.register_plugin(plugin)
        assert pm.get_plugin("sample") is plugin
        assert len(pm.get_active_plugins()) == 1

    def test_register_plugin_with_config(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        plugin = SamplePlugin()
        pm.register_plugin(plugin, plugin_config={"custom": "value"})
        assert plugin.config == {"custom": "value"}

    def test_register_plugin_failing_init(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        plugin = FailingInitPlugin()
        pm.register_plugin(plugin)
        assert len(pm.get_active_plugins()) == 0
        assert "failing_init" in pm.get_load_errors()

    def test_register_plugin_pre_activate_rejected(self, app_yaml_path: Path) -> None:
        def reject(plugin: BasePlugin, config: dict) -> bool:
            return False

        pm = PluginManager(str(app_yaml_path), pre_activate=reject)
        plugin = SamplePlugin()
        pm.register_plugin(plugin)
        assert len(pm.get_active_plugins()) == 0
        assert "sample" in pm.get_load_errors()

    def test_register_plugin_failing_activate(
        self, app_yaml_path: Path, tmp_config_dir: Path
    ) -> None:
        import yaml

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
        plugin = FailingActivatePlugin()
        pm.register_plugin(plugin)
        assert len(pm.get_active_plugins()) == 0
        assert "failing_activate" in pm.get_load_errors()

    # --- #9 get_load_errors ---

    def test_get_load_errors_empty(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        assert pm.get_load_errors() == {}

    def test_get_load_errors_failing_init(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
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
        errors = pm.get_load_errors()
        assert "failing_init" in errors
        assert "initialize" in errors["failing_init"].lower()

    def test_get_load_errors_missing_dep(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["missing_dep"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([MissingDepPlugin])
        errors = pm.get_load_errors()
        assert "missing_dep" in errors
        assert "dependencies" in errors["missing_dep"].lower()

    def test_get_load_errors_pre_activate_rejected(self, app_yaml_path: Path) -> None:
        def reject(plugin: BasePlugin, config: dict) -> bool:
            return False

        pm = PluginManager(str(app_yaml_path), pre_activate=reject)
        pm.register_plugins([SamplePlugin])
        errors = pm.get_load_errors()
        assert "sample" in errors
        assert "pre-activate" in errors["sample"].lower()

    # --- #10 api_version check ---

    def test_api_version_match_no_warning(
        self, app_yaml_path: Path, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["sample"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path), api_version="1")
        pm.register_plugins([SamplePlugin])
        assert "api_version" not in caplog.text

    def test_api_version_mismatch_warns(
        self, app_yaml_path: Path, tmp_config_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging
        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["old_api"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with caplog.at_level(logging.WARNING):
            pm = PluginManager(str(app_yaml_path), api_version="2")
            pm.register_plugins([OldApiPlugin])

        assert "old_api" in caplog.text
        assert "api_version" in caplog.text

    def test_api_version_mismatch_still_loads(
        self, app_yaml_path: Path, tmp_config_dir: Path
    ) -> None:
        import yaml

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["old_api"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        pm = PluginManager(str(app_yaml_path), api_version="2")
        pm.register_plugins([OldApiPlugin])
        assert len(pm.get_active_plugins()) == 1

    def test_api_version_check_on_register_plugin(
        self, app_yaml_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        with caplog.at_level(logging.WARNING):
            pm = PluginManager(str(app_yaml_path), api_version="2")
            plugin = OldApiPlugin()
            pm.register_plugin(plugin)

        assert "old_api" in caplog.text
        assert "api_version" in caplog.text
        assert len(pm.get_active_plugins()) == 1

    # --- #4 deactivate unregisters from pluggy ---

    def test_deactivate_unregisters_hooks(self, app_yaml_path: Path) -> None:
        import pluggy

        hookspec = pluggy.HookspecMarker("testapp.plugins")
        hookimpl = pluggy.HookimplMarker("testapp.plugins")

        class MySpec:
            @hookspec
            def my_hook(self) -> str: ...

        class HookPlugin(BasePlugin):
            name = "sample"

            @hookimpl
            def my_hook(self) -> str:
                return "hello"

        pm = PluginManager(str(app_yaml_path))
        pm.register_hookspecs(MySpec)
        pm.register_plugins([HookPlugin])
        assert pm.call_hook("my_hook") == ["hello"]

        pm.deactivate_plugin("sample")
        assert pm.call_hook("my_hook") == []

    def test_deactivate_all_unregisters_hooks(self, app_yaml_path: Path) -> None:
        import pluggy

        hookspec = pluggy.HookspecMarker("testapp.plugins")
        hookimpl = pluggy.HookimplMarker("testapp.plugins")

        class MySpec:
            @hookspec
            def my_hook(self) -> str: ...

        class HookPlugin(BasePlugin):
            name = "sample"

            @hookimpl
            def my_hook(self) -> str:
                return "hello"

        pm = PluginManager(str(app_yaml_path))
        pm.register_hookspecs(MySpec)
        pm.register_plugins([HookPlugin])
        assert pm.call_hook("my_hook") == ["hello"]

        pm.deactivate_all()
        assert pm.call_hook("my_hook") == []

    # --- #11 config schema validation ---

    def test_config_schema_valid(self, app_yaml_path: Path) -> None:
        class SchemaPlugin(BasePlugin):
            name = "sample"
            config_schema = {"greeting": str, "max_retries": int}

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SchemaPlugin])
        assert len(pm.get_active_plugins()) == 1

    def test_config_schema_invalid_type(self, app_yaml_path: Path, tmp_config_dir: Path) -> None:
        import yaml

        # Write config with wrong type (string instead of int)
        bad_config = {"greeting": "Hello", "max_retries": "not_a_number"}
        with open(tmp_config_dir / "plugins" / "sample.yaml", "w", encoding="utf-8") as f:
            yaml.dump(bad_config, f)

        class SchemaPlugin(BasePlugin):
            name = "sample"
            config_schema = {"greeting": str, "max_retries": int}

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SchemaPlugin])
        assert len(pm.get_active_plugins()) == 0
        errors = pm.get_load_errors()
        assert "sample" in errors

    def test_config_schema_missing_key_ok(self, app_yaml_path: Path) -> None:
        """Missing keys are not an error, only wrong types."""

        class SchemaPlugin(BasePlugin):
            name = "sample"
            config_schema = {"greeting": str, "optional_key": int}

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SchemaPlugin])
        assert len(pm.get_active_plugins()) == 1

    def test_config_schema_none_skips_validation(self, app_yaml_path: Path) -> None:
        class NoSchemaPlugin(BasePlugin):
            name = "sample"
            config_schema = None

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([NoSchemaPlugin])
        assert len(pm.get_active_plugins()) == 1

    def test_config_schema_on_register_plugin(
        self, app_yaml_path: Path, tmp_config_dir: Path
    ) -> None:
        class SchemaPlugin(BasePlugin):
            name = "sample"
            config_schema = {"greeting": str, "max_retries": int}

        pm = PluginManager(str(app_yaml_path))
        plugin = SchemaPlugin()
        pm.register_plugin(plugin, plugin_config={"greeting": "Hi", "max_retries": "bad"})
        assert len(pm.get_active_plugins()) == 0
        assert "sample" in pm.get_load_errors()

    # --- #12 health check ---

    def test_health_check_default(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        result = pm.health_check()
        assert result["sample"] == {"status": "ok"}

    def test_health_check_custom(self, app_yaml_path: Path) -> None:
        class HealthyPlugin(BasePlugin):
            name = "sample"

            def health(self) -> dict:
                return {"status": "ok", "connections": 5}

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([HealthyPlugin])
        result = pm.health_check()
        assert result["sample"]["status"] == "ok"
        assert result["sample"]["connections"] == 5

    def test_health_check_error(self, app_yaml_path: Path) -> None:
        class UnhealthyPlugin(BasePlugin):
            name = "sample"

            def health(self) -> dict:
                raise ConnectionError("API unreachable")

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([UnhealthyPlugin])
        result = pm.health_check()
        assert result["sample"]["status"] == "error"
        assert "API unreachable" in result["sample"]["error"]

    def test_health_check_multiple_plugins(self, app_yaml_path: Path) -> None:
        class OkPlugin(BasePlugin):
            name = "sample"

        class FailPlugin(BasePlugin):
            name = "another"

            def health(self) -> dict:
                raise RuntimeError("down")

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([OkPlugin, FailPlugin])
        result = pm.health_check()
        assert result["sample"]["status"] == "ok"
        assert result["another"]["status"] == "error"

    def test_health_check_empty(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        assert pm.health_check() == {}

    # --- #14 reload_plugin ---

    def test_reload_plugin(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        assert pm.get_plugin("sample") is not None

        result = pm.reload_plugin("sample")
        assert result is True
        plugin = pm.get_plugin("sample")
        assert plugin is not None
        assert plugin.name == "sample"
        assert len(pm.get_active_plugins()) == 1

    def test_reload_plugin_unknown(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        assert pm.reload_plugin("nonexistent") is False

    def test_reload_plugin_preserves_config(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])
        result = pm.reload_plugin("sample")
        assert result is True
        plugin = pm.get_plugin("sample")
        assert plugin is not None
        assert plugin.config.get("greeting") == "Hello"

    def test_reload_plugin_with_pre_activate(self, app_yaml_path: Path) -> None:
        calls: list[str] = []

        def track(plugin: BasePlugin, config: dict) -> bool:
            calls.append(plugin.name)
            return True

        pm = PluginManager(str(app_yaml_path), pre_activate=track)
        pm.register_plugins([SamplePlugin])
        calls.clear()

        pm.reload_plugin("sample")
        assert "sample" in calls

    def test_reload_plugin_pre_activate_rejects(self, app_yaml_path: Path) -> None:
        first_call = [True]

        def reject_second(plugin: BasePlugin, config: dict) -> bool:
            if first_call[0]:
                first_call[0] = False
                return True
            return False

        pm = PluginManager(str(app_yaml_path), pre_activate=reject_second)
        pm.register_plugins([SamplePlugin])
        assert len(pm.get_active_plugins()) == 1

        result = pm.reload_plugin("sample")
        assert result is False
        assert "sample" in pm.get_load_errors()

    # --- #15 security - path traversal ---

    def test_path_traversal_plugin_name_rejected(self, app_yaml_path: Path) -> None:
        from pluginforge.security import InvalidPluginNameError

        class EvilPlugin(BasePlugin):
            name = "../../etc/passwd"

        pm = PluginManager(str(app_yaml_path))
        with pytest.raises(InvalidPluginNameError):
            pm.register_plugin(EvilPlugin())

    def test_path_traversal_in_register_plugins(
        self, app_yaml_path: Path, tmp_config_dir: Path
    ) -> None:
        import yaml
        from pluginforge.security import InvalidPluginNameError

        config = {
            "app": {"name": "TestApp"},
            "plugins": {
                "entry_point_group": "testapp.plugins",
                "enabled": ["../evil"],
            },
        }
        with open(app_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        class EvilPlugin(BasePlugin):
            name = "../evil"

        pm = PluginManager(str(app_yaml_path))
        with pytest.raises(InvalidPluginNameError):
            pm.register_plugins([EvilPlugin])

    # --- #16 get_extensions ---

    def test_get_extensions_basic(self, app_yaml_path: Path) -> None:
        from abc import ABC, abstractmethod

        class Exportable(ABC):
            @abstractmethod
            def export(self) -> str: ...

        class ExportPlugin(BasePlugin, Exportable):
            name = "sample"

            def export(self) -> str:
                return "exported"

        class PlainPlugin(BasePlugin):
            name = "another"

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([ExportPlugin, PlainPlugin])

        extensions = pm.get_extensions(Exportable)
        assert len(extensions) == 1
        assert extensions[0].name == "sample"

    def test_get_extensions_multiple(self, app_yaml_path: Path) -> None:
        from abc import ABC, abstractmethod

        class Exportable(ABC):
            @abstractmethod
            def export(self) -> str: ...

        class ExportA(BasePlugin, Exportable):
            name = "sample"

            def export(self) -> str:
                return "a"

        class ExportB(BasePlugin, Exportable):
            name = "another"

            def export(self) -> str:
                return "b"

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([ExportA, ExportB])

        extensions = pm.get_extensions(Exportable)
        assert len(extensions) == 2

    def test_get_extensions_none_match(self, app_yaml_path: Path) -> None:
        from abc import ABC, abstractmethod

        class Exportable(ABC):
            @abstractmethod
            def export(self) -> str: ...

        pm = PluginManager(str(app_yaml_path))
        pm.register_plugins([SamplePlugin])

        extensions = pm.get_extensions(Exportable)
        assert extensions == []

    def test_get_extensions_empty(self, app_yaml_path: Path) -> None:
        pm = PluginManager(str(app_yaml_path))
        assert pm.get_extensions(BasePlugin) == []
