"""Minimal FastAPI app using PluginForge."""

from pluginforge import PluginManager

# Import the plugin class directly (in production, use entry points)
from plugins.hello_plugin import HelloPlugin


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError:
        raise ImportError("FastAPI is required: pip install fastapi[standard]")

    app = FastAPI(title="SimpleApp")
    pm = PluginManager("config/app.yaml")
    pm.register_plugins([HelloPlugin])
    pm.mount_routes(app)

    @app.get("/")
    def root():
        return {
            "app": pm.get_app_config().get("app", {}).get("name"),
            "plugins": [p.name for p in pm.get_active_plugins()],
        }

    return app


if __name__ == "__main__":
    import uvicorn

    application = create_app()
    uvicorn.run(application, host="0.0.0.0", port=8000)
