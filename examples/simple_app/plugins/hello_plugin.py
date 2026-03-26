"""Example hello plugin for the simple app."""

from typing import Any

from pluginforge.base import BasePlugin


class HelloPlugin(BasePlugin):
    """A simple plugin that provides a /hello endpoint."""

    name = "hello"
    version = "1.0.0"
    description = "Says hello to the world"
    author = "Asterios Raptis"

    def init(self, app_config: dict[str, Any], plugin_config: dict[str, Any]) -> None:
        super().init(app_config, plugin_config)
        self._greeting = plugin_config.get("greeting", "Hello!")

    def activate(self) -> None:
        pass

    def deactivate(self) -> None:
        pass

    def get_routes(self) -> list:
        try:
            from fastapi import APIRouter
        except ImportError:
            return []

        router = APIRouter()

        greeting = self._greeting

        @router.get("/hello")
        def hello() -> dict[str, str]:
            return {"message": greeting}

        return [router]
