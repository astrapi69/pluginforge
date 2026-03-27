"""Tests for pluginforge.lifecycle module."""

from tests.conftest import (
    FailingActivatePlugin,
    FailingDeactivatePlugin,
    FailingInitPlugin,
    SamplePlugin,
)

from pluginforge.lifecycle import PluginLifecycle


class TestPluginLifecycle:
    def test_init_plugin(self) -> None:
        lc = PluginLifecycle()
        plugin = SamplePlugin()
        assert lc.init_plugin(plugin, {}, {"key": "val"})
        assert plugin.config == {"key": "val"}
        assert lc.get_plugin("sample") is plugin

    def test_activate_plugin(self) -> None:
        lc = PluginLifecycle()
        plugin = SamplePlugin()
        lc.init_plugin(plugin, {}, {})
        assert lc.activate_plugin(plugin)
        assert lc.is_active("sample")

    def test_activate_uninitialized_fails(self) -> None:
        lc = PluginLifecycle()
        plugin = SamplePlugin()
        assert not lc.activate_plugin(plugin)

    def test_deactivate_plugin(self) -> None:
        lc = PluginLifecycle()
        plugin = SamplePlugin()
        lc.init_plugin(plugin, {}, {})
        lc.activate_plugin(plugin)
        assert lc.deactivate_plugin(plugin)
        assert not lc.is_active("sample")

    def test_deactivate_inactive_fails(self) -> None:
        lc = PluginLifecycle()
        plugin = SamplePlugin()
        assert not lc.deactivate_plugin(plugin)

    def test_deactivate_all_reverse_order(self) -> None:
        lc = PluginLifecycle()
        from tests.conftest import AnotherPlugin

        p1 = SamplePlugin()
        p2 = AnotherPlugin()
        lc.init_plugin(p1, {}, {})
        lc.init_plugin(p2, {}, {})
        lc.activate_plugin(p1)
        lc.activate_plugin(p2)
        assert len(lc.get_active_plugins()) == 2
        lc.deactivate_all()
        assert len(lc.get_active_plugins()) == 0

    def test_get_active_plugins(self) -> None:
        lc = PluginLifecycle()
        plugin = SamplePlugin()
        lc.init_plugin(plugin, {}, {})
        lc.activate_plugin(plugin)
        active = lc.get_active_plugins()
        assert len(active) == 1
        assert active[0].name == "sample"

    def test_get_plugin_not_found(self) -> None:
        lc = PluginLifecycle()
        assert lc.get_plugin("nonexistent") is None

    def test_failing_init(self) -> None:
        lc = PluginLifecycle()
        plugin = FailingInitPlugin()
        assert not lc.init_plugin(plugin, {}, {})
        assert lc.get_plugin("failing_init") is None

    def test_failing_activate(self) -> None:
        lc = PluginLifecycle()
        plugin = FailingActivatePlugin()
        lc.init_plugin(plugin, {}, {})
        assert not lc.activate_plugin(plugin)
        assert not lc.is_active("failing_activate")

    def test_failing_deactivate(self) -> None:
        lc = PluginLifecycle()
        plugin = FailingDeactivatePlugin()
        lc.init_plugin(plugin, {}, {})
        lc.activate_plugin(plugin)
        assert not lc.deactivate_plugin(plugin)

    def test_config_schema_validation_rejects_bad_type(self) -> None:
        from pluginforge.base import BasePlugin

        class SchemaPlugin(BasePlugin):
            name = "schema_test"
            config_schema = {"port": int}

        lc = PluginLifecycle()
        plugin = SchemaPlugin()
        result = lc.init_plugin(plugin, {}, {"port": "not_int"})
        assert result is False

    def test_config_schema_validation_passes_good_type(self) -> None:
        from pluginforge.base import BasePlugin

        class SchemaPlugin(BasePlugin):
            name = "schema_test"
            config_schema = {"port": int}

        lc = PluginLifecycle()
        plugin = SchemaPlugin()
        result = lc.init_plugin(plugin, {}, {"port": 8080})
        assert result is True

    def test_remove_plugin(self) -> None:
        lc = PluginLifecycle()
        plugin = SamplePlugin()
        lc.init_plugin(plugin, {}, {})
        lc.activate_plugin(plugin)
        assert lc.is_active("sample")

        lc.remove_plugin("sample")
        assert lc.get_plugin("sample") is None
        assert not lc.is_active("sample")

    def test_remove_nonexistent_plugin(self) -> None:
        lc = PluginLifecycle()
        lc.remove_plugin("nonexistent")  # should not raise
