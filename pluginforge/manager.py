"""Central PluginManager that orchestrates config, discovery, lifecycle, and hooks."""

import logging
from pathlib import Path
from typing import Any

import pluggy

from pluginforge.base import BasePlugin
from pluginforge.config import load_app_config, load_plugin_config
from pluginforge.discovery import (
    CircularDependencyError,
    check_missing_dependencies,
    discover_entry_points,
    filter_plugins,
    resolve_dependencies,
)
from pluginforge.i18n import I18n
from pluginforge.lifecycle import PluginLifecycle

logger = logging.getLogger(__name__)


class PluginManager:
    """Central manager for plugin discovery, lifecycle, and hooks.

    Wraps pluggy.PluginManager and adds YAML config, lifecycle management,
    dependency resolution, and i18n support.

    Args:
        config_path: Path to app.yaml configuration file.
    """

    def __init__(self, config_path: str = "config/app.yaml") -> None:
        self._config_path = Path(config_path)
        self._config_dir = self._config_path.parent
        self._app_config = load_app_config(self._config_path)

        plugins_config = self._app_config.get("plugins", {})
        group = plugins_config.get("entry_point_group", "pluginforge.plugins")
        self._entry_point_group = group

        self._pm = pluggy.PluginManager(group)
        self._lifecycle = PluginLifecycle()

        default_lang = self._app_config.get("app", {}).get("default_language", "en")
        self._i18n = I18n(self._config_dir, default_lang=default_lang)

    def get_app_config(self) -> dict[str, Any]:
        """Return the loaded application configuration.

        Returns:
            App config dict.
        """
        return self._app_config

    def get_plugin_config(self, plugin_name: str) -> dict[str, Any]:
        """Load and return config for a specific plugin.

        Args:
            plugin_name: Name of the plugin.

        Returns:
            Plugin configuration dict.
        """
        return load_plugin_config(self._config_dir, plugin_name)

    def discover_plugins(self) -> None:
        """Discover, filter, resolve dependencies, and activate plugins.

        Loads plugins from entry points, filters by enabled/disabled config,
        checks dependencies, sorts topologically, then initializes and
        activates each plugin.
        """
        plugins = discover_entry_points(self._entry_point_group)

        plugins_config = self._app_config.get("plugins", {})
        enabled = plugins_config.get("enabled")
        disabled = plugins_config.get("disabled")
        plugins = filter_plugins(plugins, enabled, disabled)

        missing = check_missing_dependencies(plugins)
        for name, deps in missing.items():
            logger.warning("Plugin '%s' has missing dependencies %s, skipping", name, deps)
            del plugins[name]

        try:
            order = resolve_dependencies(plugins)
        except CircularDependencyError as e:
            raise e

        for name in order:
            cls = plugins[name]
            plugin = cls()
            plugin_config = self.get_plugin_config(name)

            if not self._lifecycle.init_plugin(plugin, self._app_config, plugin_config):
                continue

            self._pm.register(plugin, name=name)

            if not self._lifecycle.activate_plugin(plugin):
                self._pm.unregister(name=name)

    def register_plugins(self, plugin_classes: list[type[BasePlugin]]) -> None:
        """Register plugin classes directly (without entry point discovery).

        Useful for testing or programmatic plugin registration.

        Args:
            plugin_classes: List of plugin classes to register.
        """
        plugins_map: dict[str, type[BasePlugin]] = {}
        for cls in plugin_classes:
            plugins_map[cls.name] = cls

        plugins_config = self._app_config.get("plugins", {})
        enabled = plugins_config.get("enabled")
        disabled = plugins_config.get("disabled")
        plugins_map = filter_plugins(plugins_map, enabled, disabled)

        missing = check_missing_dependencies(plugins_map)
        for name, deps in missing.items():
            logger.warning("Plugin '%s' has missing dependencies %s, skipping", name, deps)
            del plugins_map[name]

        order = resolve_dependencies(plugins_map)

        for name in order:
            cls = plugins_map[name]
            plugin = cls()
            plugin_config = self.get_plugin_config(name)

            if not self._lifecycle.init_plugin(plugin, self._app_config, plugin_config):
                continue

            self._pm.register(plugin, name=name)

            if not self._lifecycle.activate_plugin(plugin):
                self._pm.unregister(name=name)

    def activate_plugin(self, name: str) -> None:
        """Activate a specific initialized plugin.

        Args:
            name: Plugin name.
        """
        plugin = self._lifecycle.get_plugin(name)
        if plugin is None:
            logger.warning("Plugin '%s' not found", name)
            return
        self._lifecycle.activate_plugin(plugin)

    def deactivate_plugin(self, name: str) -> None:
        """Deactivate a specific active plugin.

        Args:
            name: Plugin name.
        """
        plugin = self._lifecycle.get_plugin(name)
        if plugin is None:
            logger.warning("Plugin '%s' not found", name)
            return
        self._lifecycle.deactivate_plugin(plugin)

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get a plugin instance by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin instance or None.
        """
        return self._lifecycle.get_plugin(name)

    def get_active_plugins(self) -> list[BasePlugin]:
        """Return all currently active plugins.

        Returns:
            List of active plugins.
        """
        return self._lifecycle.get_active_plugins()

    def deactivate_all(self) -> None:
        """Deactivate all active plugins in reverse order."""
        self._lifecycle.deactivate_all()

    def register_hookspecs(self, spec_module: object) -> None:
        """Register hook specifications from a module.

        Args:
            spec_module: Module containing hookspec-decorated functions.
        """
        self._pm.add_hookspecs(spec_module)

    def call_hook(self, hook_name: str, **kwargs: Any) -> list[Any]:
        """Call a named hook on all registered plugins.

        Args:
            hook_name: Name of the hook to call.
            **kwargs: Arguments to pass to hook implementations.

        Returns:
            List of results from all hook implementations.
        """
        hook = getattr(self._pm.hook, hook_name, None)
        if hook is None:
            logger.warning("Hook '%s' not found", hook_name)
            return []
        return hook(**kwargs)

    def mount_routes(self, app: object) -> None:
        """Mount FastAPI routes from all active plugins.

        Args:
            app: A FastAPI application instance.
        """
        from pluginforge.fastapi_ext import mount_plugin_routes

        mount_plugin_routes(app, self.get_active_plugins())

    def get_text(self, key: str, lang: str | None = None) -> str:
        """Get an internationalized string.

        Args:
            key: Dot-notation i18n key.
            lang: Language code, or None for default.

        Returns:
            Translated string.
        """
        return self._i18n.get_text(key, lang)

    def collect_migrations(self) -> dict[str, str]:
        """Collect Alembic migration directories from all active plugins.

        Returns:
            Dict mapping plugin name to migrations directory path.
        """
        from pluginforge.alembic_ext import collect_migrations_dirs

        return collect_migrations_dirs(self.get_active_plugins())
