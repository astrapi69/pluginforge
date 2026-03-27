"""FastAPI integration for mounting plugin routes."""

import logging

from pluginforge.base import BasePlugin

logger = logging.getLogger(__name__)


def mount_plugin_routes(app: "object", plugins: list[BasePlugin], prefix: str = "/api") -> None:
    """Mount routes from all plugins onto a FastAPI app.

    Plugins bring their own route prefixes via their routers.
    The prefix parameter is prepended to all plugin routes.

    Args:
        app: A FastAPI application instance.
        plugins: List of active plugins.
        prefix: URL prefix for all plugin routes (default: "/api").
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
            app.include_router(router, prefix=prefix)
            logger.info("Mounted routes for plugin '%s' under %s", plugin.name, prefix)
