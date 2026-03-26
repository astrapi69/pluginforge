"""Tests for pluginforge.fastapi_ext module."""

import pytest

from pluginforge.base import BasePlugin


class RoutedPlugin(BasePlugin):
    name = "routed"

    def get_routes(self) -> list:
        try:
            from fastapi import APIRouter

            router = APIRouter()

            @router.get("/hello")
            def hello() -> dict[str, str]:
                return {"message": "hello"}

            return [router]
        except ImportError:
            return []


class TestFastapiExt:
    def test_mount_routes(self) -> None:
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            from pluginforge.fastapi_ext import mount_plugin_routes
        except ImportError:
            pytest.skip("FastAPI not installed")

        app = FastAPI()
        plugin = RoutedPlugin()
        plugin.init({}, {})
        plugin.activate()

        mount_plugin_routes(app, [plugin])

        client = TestClient(app)
        response = client.get("/api/plugins/routed/hello")
        assert response.status_code == 200
        assert response.json() == {"message": "hello"}

    def test_mount_no_routes(self) -> None:
        try:
            from fastapi import FastAPI

            from pluginforge.fastapi_ext import mount_plugin_routes
        except ImportError:
            pytest.skip("FastAPI not installed")

        app = FastAPI()
        plugin = BasePlugin.__new__(BasePlugin)
        plugin.name = "empty"
        mount_plugin_routes(app, [plugin])

    def test_mount_wrong_type(self) -> None:
        try:
            from fastapi import FastAPI  # noqa: F401

            from pluginforge.fastapi_ext import mount_plugin_routes
        except ImportError:
            pytest.skip("FastAPI not installed")

        with pytest.raises(TypeError):
            mount_plugin_routes("not_an_app", [])

    def test_import_error_message(self) -> None:
        import importlib
        import sys

        # Temporarily hide fastapi to test import error
        fastapi_mod = sys.modules.get("fastapi")
        sys.modules["fastapi"] = None  # type: ignore[assignment]
        try:
            # Reload to trigger ImportError path
            from pluginforge import fastapi_ext

            importlib.reload(fastapi_ext)
            with pytest.raises(ImportError, match="FastAPI is required"):
                fastapi_ext.mount_plugin_routes(object(), [])
        finally:
            if fastapi_mod is not None:
                sys.modules["fastapi"] = fastapi_mod
            else:
                del sys.modules["fastapi"]
