"""Tests for pluginforge.base module."""

from pluginforge.base import BasePlugin
from tests.conftest import SamplePlugin


class TestBasePlugin:
    def test_default_attributes(self) -> None:
        plugin = SamplePlugin()
        assert plugin.name == "sample"
        assert plugin.version == "1.0.0"
        assert plugin.api_version == "1"
        assert plugin.description == "A sample plugin for testing"

    def test_init_sets_config(self) -> None:
        plugin = SamplePlugin()
        plugin.init({"app": {}}, {"key": "value"})
        assert plugin.config == {"key": "value"}

    def test_activate_deactivate_no_error(self) -> None:
        plugin = SamplePlugin()
        plugin.activate()
        plugin.deactivate()

    def test_get_routes_returns_empty_list(self) -> None:
        plugin = SamplePlugin()
        assert plugin.get_routes() == []

    def test_get_migrations_dir_returns_none(self) -> None:
        plugin = SamplePlugin()
        assert plugin.get_migrations_dir() is None

    def test_depends_on_default_empty(self) -> None:
        plugin = SamplePlugin()
        assert plugin.depends_on == []

    def test_is_abstract(self) -> None:
        assert issubclass(BasePlugin, object)

    def test_custom_api_version(self) -> None:
        class V2Plugin(BasePlugin):
            name = "v2"
            api_version = "2"

        plugin = V2Plugin()
        assert plugin.api_version == "2"

    def test_default_health(self) -> None:
        plugin = SamplePlugin()
        assert plugin.health() == {"status": "ok"}

    def test_custom_health(self) -> None:
        class MonitoredPlugin(BasePlugin):
            name = "monitored"

            def health(self) -> dict:
                return {"status": "ok", "latency_ms": 42}

        plugin = MonitoredPlugin()
        result = plugin.health()
        assert result["status"] == "ok"
        assert result["latency_ms"] == 42

    def test_default_frontend_manifest(self) -> None:
        plugin = SamplePlugin()
        assert plugin.get_frontend_manifest() is None

    def test_default_config_schema(self) -> None:
        plugin = SamplePlugin()
        assert plugin.config_schema is None

    def test_app_config_stored(self) -> None:
        plugin = SamplePlugin()
        plugin.init({"app": {"name": "Test"}}, {"key": "val"})
        assert plugin.app_config == {"app": {"name": "Test"}}
        assert plugin.config == {"key": "val"}
