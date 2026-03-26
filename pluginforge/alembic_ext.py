"""Alembic migration support for plugins."""

import logging
from pathlib import Path

from pluginforge.base import BasePlugin

logger = logging.getLogger(__name__)


def collect_migrations_dirs(plugins: list[BasePlugin]) -> dict[str, str]:
    """Collect Alembic migration directories from all plugins.

    Args:
        plugins: List of active plugins.

    Returns:
        Dict mapping plugin name to migrations directory path.
    """
    migrations: dict[str, str] = {}
    for plugin in plugins:
        migrations_dir = plugin.get_migrations_dir()
        if migrations_dir is None:
            continue
        path = Path(migrations_dir)
        if not path.is_dir():
            logger.warning(
                "Plugin '%s' migrations dir does not exist: %s", plugin.name, migrations_dir
            )
            continue
        migrations[plugin.name] = str(path)
        logger.info("Collected migrations for plugin '%s': %s", plugin.name, migrations_dir)
    return migrations
