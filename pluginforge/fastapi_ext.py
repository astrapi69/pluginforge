"""FastAPI integration for mounting plugin routes."""

import logging

from pluginforge.base import BasePlugin

logger = logging.getLogger(__name__)


def mount_plugin_routes(app: "object", plugins: list[BasePlugin]) -> None:
    """Mount routes from all plugins onto a FastAPI app.

    Each plugin's routes are mounted under /api/plugins/{plugin_name}/.

    Args:
        app: A FastAPI application instance.
        plugins: List of active plugins.
    """
    try:
        from fastapi import FastAPI
    except ImportError:
        raise ImportError(
            "FastAPI is required for route mounting. "
            "Install it with: pip install pluginforge[fastapi]"
        )

    if not isinstance(app, FastAPI):
        raise TypeError(f"Expected FastAPI instance, got {type(app).__name__}")

    for plugin in plugins:
        routes = plugin.get_routes()
        if not routes:
            continue
        for router in routes:
            prefix = f"/api/plugins/{plugin.name}"
            app.include_router(router, prefix=prefix)
            logger.info("Mounted routes for plugin '%s' at %s", plugin.name, prefix)
