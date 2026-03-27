"""Central PluginManager that orchestrates config, discovery, lifecycle, and hooks."""

import importlib
import logging
import sys
from pathlib import Path
from collections.abc import Callable
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
from pluginforge.security import validate_plugin_name

logger = logging.getLogger(__name__)


class PluginManager:
    """Central manager for plugin discovery, lifecycle, and hooks.

    Wraps pluggy.PluginManager and adds YAML config, lifecycle management,
    dependency resolution, and i18n support.

    Args:
        config_path: Path to app.yaml configuration file.
        pre_activate: Optional callback called before plugin activation.
            Receives (plugin, config) and must return True to allow activation.
        api_version: Current hook spec version. Plugins with a different
            api_version will log a warning but still load.
    """

    def __init__(
        self,
        config_path: str = "config/app.yaml",
        pre_activate: Callable[[BasePlugin, dict[str, Any]], bool] | None = None,
        api_version: str = "1",
    ) -> None:
        self._config_path = Path(config_path)
        self._config_dir = self._config_path.parent
        self._app_config = load_app_config(self._config_path)
        self._pre_activate = pre_activate
        self._api_version = api_version

        plugins_config = self._app_config.get("plugins", {})
        group = plugins_config.get("entry_point_group", "pluginforge.plugins")
        self._entry_point_group = group

        self._pm = pluggy.PluginManager(group)
        self._lifecycle = PluginLifecycle()
        self._load_errors: dict[str, str] = {}

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

    def reload_config(self) -> None:
        """Reload application config from disk.

        Reloads app.yaml and clears the i18n cache. Active plugins are
        not affected - call deactivate_all() + discover_plugins() to
        fully restart with new config.
        """
        self._app_config = load_app_config(self._config_path)
        default_lang = self._app_config.get("app", {}).get("default_language", "en")
        self._i18n = I18n(self._config_dir, default_lang=default_lang)
        logger.info("Reloaded config from %s", self._config_path)

    def list_available_plugins(self) -> list[str]:
        """Return names of all discoverable plugins from entry points.

        Returns:
            List of plugin names without loading them.
        """
        return list(discover_entry_points(self._entry_point_group).keys())

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
            msg = f"Missing dependencies: {deps}"
            logger.warning("Plugin '%s' has missing dependencies %s, skipping", name, deps)
            self._load_errors[name] = msg
            del plugins[name]

        try:
            order = resolve_dependencies(plugins)
        except CircularDependencyError as e:
            raise e

        self._activate_ordered(plugins, order)

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
            msg = f"Missing dependencies: {deps}"
            logger.warning("Plugin '%s' has missing dependencies %s, skipping", name, deps)
            self._load_errors[name] = msg
            del plugins_map[name]

        order = resolve_dependencies(plugins_map)

        self._activate_ordered(plugins_map, order)

    def register_plugin(
        self, plugin: BasePlugin, plugin_config: dict[str, Any] | None = None
    ) -> None:
        """Register a single pre-instantiated plugin.

        Useful for tests or dynamically created plugins.

        Args:
            plugin: An already instantiated plugin.
            plugin_config: Optional config dict. If None, loaded from YAML.
        """
        validate_plugin_name(plugin.name)

        if plugin_config is None:
            plugin_config = self.get_plugin_config(plugin.name)

        self._check_api_version(plugin)

        if not self._lifecycle.init_plugin(plugin, self._app_config, plugin_config):
            self._load_errors[plugin.name] = "Failed to initialize"
            return

        if self._pre_activate is not None:
            if not self._pre_activate(plugin, plugin_config):
                logger.info("Pre-activate check rejected plugin '%s'", plugin.name)
                self._load_errors[plugin.name] = "Rejected by pre-activate check"
                return

        self._pm.register(plugin, name=plugin.name)

        if not self._lifecycle.activate_plugin(plugin):
            self._load_errors[plugin.name] = "Failed to activate"
            self._pm.unregister(name=plugin.name)

    def _check_api_version(self, plugin: BasePlugin) -> None:
        """Log a warning if the plugin's api_version differs from the manager's.

        Args:
            plugin: The plugin to check.
        """
        if plugin.api_version != self._api_version:
            logger.warning(
                "Plugin '%s' has api_version '%s', expected '%s'",
                plugin.name,
                plugin.api_version,
                self._api_version,
            )

    def _activate_ordered(self, plugins: dict[str, type[BasePlugin]], order: list[str]) -> None:
        """Initialize and activate plugins in dependency order.

        Args:
            plugins: Map of plugin name to plugin class.
            order: Topologically sorted list of plugin names.
        """
        for name in order:
            validate_plugin_name(name)
            cls = plugins[name]
            plugin = cls()
            plugin_config = self.get_plugin_config(name)

            self._check_api_version(plugin)

            if not self._lifecycle.init_plugin(plugin, self._app_config, plugin_config):
                self._load_errors[name] = "Failed to initialize"
                continue

            if self._pre_activate is not None:
                if not self._pre_activate(plugin, plugin_config):
                    logger.info("Pre-activate check rejected plugin '%s'", name)
                    self._load_errors[name] = "Rejected by pre-activate check"
                    continue

            self._pm.register(plugin, name=name)

            if not self._lifecycle.activate_plugin(plugin):
                self._load_errors[name] = "Failed to activate"
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
        """Deactivate a specific active plugin and unregister its hooks.

        Args:
            name: Plugin name.
        """
        plugin = self._lifecycle.get_plugin(name)
        if plugin is None:
            logger.warning("Plugin '%s' not found", name)
            return
        if self._lifecycle.deactivate_plugin(plugin):
            self._pm.unregister(name=name)

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

    def get_load_errors(self) -> dict[str, str]:
        """Return errors from plugin loading/activation.

        Returns:
            Dict mapping plugin name to error message for failed plugins.
        """
        return dict(self._load_errors)

    def deactivate_all(self) -> None:
        """Deactivate all active plugins in reverse order and unregister hooks."""
        for plugin in reversed(self._lifecycle.get_active_plugins()):
            if self._lifecycle.deactivate_plugin(plugin):
                self._pm.unregister(name=plugin.name)

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

    def mount_routes(self, app: object, prefix: str = "/api") -> None:
        """Mount FastAPI routes from all active plugins.

        Args:
            app: A FastAPI application instance.
            prefix: URL prefix for all plugin routes (default: "/api").
        """
        from pluginforge.fastapi_ext import mount_plugin_routes

        mount_plugin_routes(app, self.get_active_plugins(), prefix=prefix)

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

    def health_check(self) -> dict[str, dict[str, Any]]:
        """Run health checks on all active plugins.

        Returns:
            Dict mapping plugin name to health status dict.
        """
        results: dict[str, dict[str, Any]] = {}
        for plugin in self.get_active_plugins():
            try:
                results[plugin.name] = plugin.health()
            except Exception as e:
                results[plugin.name] = {"status": "error", "error": str(e)}
        return results

    def reload_plugin(self, name: str) -> bool:
        """Hot-reload a plugin: deactivate, re-import module, re-init, activate.

        The plugin's module is reloaded from disk so code changes take effect
        without restarting the application.

        Args:
            name: Name of the plugin to reload.

        Returns:
            True if reload succeeded, False otherwise.
        """
        plugin = self._lifecycle.get_plugin(name)
        if plugin is None:
            logger.warning("Cannot reload unknown plugin '%s'", name)
            return False

        plugin_cls = type(plugin)
        module_name = plugin_cls.__module__

        # Deactivate and unregister
        if self._lifecycle.is_active(name):
            self._lifecycle.deactivate_plugin(plugin)
            self._pm.unregister(name=name)

        # Remove from lifecycle tracking
        self._lifecycle.remove_plugin(name)

        # Reload the module
        try:
            module = sys.modules.get(module_name)
            if module is not None:
                module = importlib.reload(module)
                plugin_cls = getattr(module, plugin_cls.__name__)
        except Exception as e:
            logger.error("Failed to reload module '%s': %s", module_name, e)
            self._load_errors[name] = f"Failed to reload module: {e}"
            return False

        # Re-instantiate and activate
        new_plugin = plugin_cls()
        plugin_config = self.get_plugin_config(name)

        if not self._lifecycle.init_plugin(new_plugin, self._app_config, plugin_config):
            self._load_errors[name] = "Failed to initialize after reload"
            return False

        if self._pre_activate is not None:
            if not self._pre_activate(new_plugin, plugin_config):
                self._load_errors[name] = "Rejected by pre-activate check after reload"
                return False

        self._pm.register(new_plugin, name=name)

        if not self._lifecycle.activate_plugin(new_plugin):
            self._load_errors[name] = "Failed to activate after reload"
            self._pm.unregister(name=name)
            return False

        logger.info("Reloaded plugin '%s'", name)
        return True

    def get_extensions(self, extension_point: type) -> list[BasePlugin]:
        """Return all active plugins that implement a given extension point.

        An extension point is any class or ABC. This method returns all active
        plugins that are instances of that type.

        Args:
            extension_point: The extension point class to filter by.

        Returns:
            List of active plugins implementing the extension point.
        """
        return [p for p in self.get_active_plugins() if isinstance(p, extension_point)]
