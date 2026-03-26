"""Plugin lifecycle management (init, activate, deactivate)."""

import logging
from typing import Any

from pluginforge.base import BasePlugin

logger = logging.getLogger(__name__)


class PluginLifecycle:
    """Manages plugin lifecycle transitions.

    Tracks which plugins are initialized and active, handles
    init/activate/deactivate calls with error handling.
    """

    def __init__(self) -> None:
        self._initialized: dict[str, BasePlugin] = {}
        self._active: dict[str, BasePlugin] = {}

    def init_plugin(
        self,
        plugin: BasePlugin,
        app_config: dict[str, Any],
        plugin_config: dict[str, Any],
    ) -> bool:
        """Initialize a plugin with config.

        Args:
            plugin: The plugin instance to initialize.
            app_config: Global application config.
            plugin_config: Plugin-specific config.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        try:
            plugin.init(app_config, plugin_config)
            self._initialized[plugin.name] = plugin
            logger.info("Initialized plugin: %s", plugin.name)
            return True
        except Exception as e:
            logger.error("Failed to initialize plugin %s: %s", plugin.name, e)
            return False

    def activate_plugin(self, plugin: BasePlugin) -> bool:
        """Activate an initialized plugin.

        Args:
            plugin: The plugin instance to activate.

        Returns:
            True if activation succeeded, False otherwise.
        """
        if plugin.name not in self._initialized:
            logger.warning("Cannot activate uninitialized plugin: %s", plugin.name)
            return False
        try:
            plugin.activate()
            self._active[plugin.name] = plugin
            logger.info("Activated plugin: %s", plugin.name)
            return True
        except Exception as e:
            logger.error("Failed to activate plugin %s: %s", plugin.name, e)
            return False

    def deactivate_plugin(self, plugin: BasePlugin) -> bool:
        """Deactivate an active plugin.

        Args:
            plugin: The plugin instance to deactivate.

        Returns:
            True if deactivation succeeded, False otherwise.
        """
        if plugin.name not in self._active:
            logger.warning("Cannot deactivate inactive plugin: %s", plugin.name)
            return False
        try:
            plugin.deactivate()
            del self._active[plugin.name]
            logger.info("Deactivated plugin: %s", plugin.name)
            return True
        except Exception as e:
            logger.error("Failed to deactivate plugin %s: %s", plugin.name, e)
            return False

    def deactivate_all(self) -> None:
        """Deactivate all active plugins in reverse activation order."""
        names = list(reversed(list(self._active.keys())))
        for name in names:
            plugin = self._active[name]
            self.deactivate_plugin(plugin)

    def get_active_plugins(self) -> list[BasePlugin]:
        """Return list of currently active plugins.

        Returns:
            List of active BasePlugin instances.
        """
        return list(self._active.values())

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get an initialized plugin by name.

        Args:
            name: Plugin name.

        Returns:
            The plugin instance or None.
        """
        return self._initialized.get(name)

    def is_active(self, name: str) -> bool:
        """Check if a plugin is currently active.

        Args:
            name: Plugin name.

        Returns:
            True if the plugin is active.
        """
        return name in self._active
