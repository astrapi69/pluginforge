"""Tests for pluginforge.discovery module."""

import pytest

from pluginforge.discovery import (
    CircularDependencyError,
    check_missing_dependencies,
    filter_plugins,
    resolve_dependencies,
)
from tests.conftest import (
    AnotherPlugin,
    CircularA,
    CircularB,
    DependentPlugin,
    MissingDepPlugin,
    SamplePlugin,
)


class TestFilterPlugins:
    def test_no_filter(self) -> None:
        plugins = {"sample": SamplePlugin, "another": AnotherPlugin}
        result = filter_plugins(plugins, enabled=None, disabled=None)
        assert set(result.keys()) == {"sample", "another"}

    def test_enabled_filter(self) -> None:
        plugins = {"sample": SamplePlugin, "another": AnotherPlugin}
        result = filter_plugins(plugins, enabled=["sample"], disabled=None)
        assert set(result.keys()) == {"sample"}

    def test_disabled_filter(self) -> None:
        plugins = {"sample": SamplePlugin, "another": AnotherPlugin}
        result = filter_plugins(plugins, enabled=None, disabled=["another"])
        assert set(result.keys()) == {"sample"}

    def test_disabled_overrides_enabled(self) -> None:
        plugins = {"sample": SamplePlugin, "another": AnotherPlugin}
        result = filter_plugins(plugins, enabled=["sample", "another"], disabled=["another"])
        assert set(result.keys()) == {"sample"}

    def test_empty_enabled(self) -> None:
        plugins = {"sample": SamplePlugin}
        result = filter_plugins(plugins, enabled=[], disabled=None)
        assert result == {}


class TestResolveDependencies:
    def test_no_dependencies(self) -> None:
        plugins = {"sample": SamplePlugin, "another": AnotherPlugin}
        order = resolve_dependencies(plugins)
        assert set(order) == {"sample", "another"}

    def test_with_dependency(self) -> None:
        plugins = {"sample": SamplePlugin, "dependent": DependentPlugin}
        order = resolve_dependencies(plugins)
        assert order.index("sample") < order.index("dependent")

    def test_circular_dependency(self) -> None:
        plugins = {"circular_a": CircularA, "circular_b": CircularB}
        with pytest.raises(CircularDependencyError):
            resolve_dependencies(plugins)

    def test_single_plugin(self) -> None:
        plugins = {"sample": SamplePlugin}
        order = resolve_dependencies(plugins)
        assert order == ["sample"]

    def test_empty_plugins(self) -> None:
        order = resolve_dependencies({})
        assert order == []

    def test_chain_dependency(self) -> None:
        class PluginC(SamplePlugin):
            name = "c"
            depends_on = ["dependent"]

        plugins = {"sample": SamplePlugin, "dependent": DependentPlugin, "c": PluginC}
        order = resolve_dependencies(plugins)
        assert order.index("sample") < order.index("dependent")
        assert order.index("dependent") < order.index("c")


class TestCheckMissingDependencies:
    def test_no_missing(self) -> None:
        plugins = {"sample": SamplePlugin, "dependent": DependentPlugin}
        missing = check_missing_dependencies(plugins)
        assert missing == {}

    def test_with_missing(self) -> None:
        plugins = {"missing_dep": MissingDepPlugin}
        missing = check_missing_dependencies(plugins)
        assert "missing_dep" in missing
        assert "nonexistent" in missing["missing_dep"]

    def test_partially_missing(self) -> None:
        plugins = {"sample": SamplePlugin, "missing_dep": MissingDepPlugin}
        missing = check_missing_dependencies(plugins)
        assert "missing_dep" in missing
        assert "sample" not in missing
