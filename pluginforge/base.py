"""Base plugin class for all PluginForge plugins."""

from abc import ABC
from typing import Any


class BasePlugin(ABC):
    """Abstract base class for all PluginForge plugins.

    Attributes:
        name: Unique plugin identifier (e.g. "export").
        version: Plugin version string.
        api_version: Hook spec compatibility version.
        description: Human-readable description.
        author: Plugin author.
        depends_on: List of plugin names this plugin depends on.
        app_config: Global application configuration, populated during init().
        config: Plugin configuration, populated during init().
    """

    name: str
    version: str = "0.1.0"
    api_version: str = "1"
    description: str = ""
    author: str = ""
    depends_on: list[str] = []
    app_config: dict[str, Any] = {}
    config: dict[str, Any] = {}

    def init(self, app_config: dict[str, Any], plugin_config: dict[str, Any]) -> None:
        """Called when the plugin is loaded. Receives app and plugin config.

        Args:
            app_config: The global application configuration.
            plugin_config: Plugin-specific configuration from YAML.
        """
        self.app_config = app_config
        self.config = plugin_config

    def activate(self) -> None:
        """Called when the plugin is activated."""

    def deactivate(self) -> None:
        """Called when the plugin is deactivated. Release resources here."""

    def get_routes(self) -> list:
        """Return FastAPI routers to be mounted. Optional.

        Returns:
            List of FastAPI APIRouter instances.
        """
        return []

    def get_migrations_dir(self) -> str | None:
        """Return path to Alembic migration scripts. Optional.

        Returns:
            Path string or None if no migrations.
        """
        return None
