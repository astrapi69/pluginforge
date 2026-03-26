# PluginForge

Application-agnostic Python plugin framework built on [pluggy](https://pluggy.readthedocs.io/).

PluginForge adds the layers that pluggy is missing: YAML configuration, plugin lifecycle management, enable/disable per config, dependency resolution, FastAPI integration, and i18n support.

## Installation

```bash
pip install pluginforge
```

With optional FastAPI support:

```bash
pip install pluginforge[fastapi]
```

## Quickstart

### 1. Create a plugin

```python
from pluginforge import BasePlugin

class HelloPlugin(BasePlugin):
    name = "hello"
    version = "1.0.0"
    description = "A hello world plugin"

    def activate(self):
        print(f"Hello plugin activated with config: {self.config}")

    def get_routes(self):
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/hello")
        def hello():
            return {"message": self.config.get("greeting", "Hello!")}

        return [router]
```

### 2. Configure your app

```yaml
# config/app.yaml
app:
  name: "MyApp"
  version: "1.0.0"
  default_language: "en"

plugins:
  entry_point_group: "myapp.plugins"
  enabled:
    - "hello"
  disabled: []
```

```yaml
# config/plugins/hello.yaml
greeting: "Hello from PluginForge!"
```

### 3. Use PluginManager

```python
from pluginforge import PluginManager

pm = PluginManager("config/app.yaml")

# Register plugins directly (or use entry points for auto-discovery)
pm.register_plugins([HelloPlugin])

# Access plugins
for plugin in pm.get_active_plugins():
    print(f"Active: {plugin.name} v{plugin.version}")

# Mount FastAPI routes
from fastapi import FastAPI
app = FastAPI()
pm.mount_routes(app)  # Routes at /api/plugins/{name}/
```

## Features

- **YAML Configuration** - App config, per-plugin config, and i18n strings
- **Plugin Lifecycle** - init, activate, deactivate with error handling
- **Enable/Disable** - Control plugins via config lists
- **Dependency Resolution** - Topological sorting with circular dependency detection
- **FastAPI Integration** - Auto-mount plugin routes under `/api/plugins/{name}/`
- **Alembic Support** - Collect migration directories from plugins
- **i18n** - Multi-language strings from YAML with fallback

## Entry Point Discovery

Register plugins as entry points in your `pyproject.toml`:

```toml
[project.entry-points."myapp.plugins"]
hello = "myapp.plugins.hello:HelloPlugin"
```

Then use `discover_plugins()` instead of `register_plugins()`:

```python
pm = PluginManager("config/app.yaml")
pm.discover_plugins()  # Auto-discovers from entry points
```

## i18n

```yaml
# config/i18n/en.yaml
common:
  save: "Save"
  cancel: "Cancel"
```

```python
pm.get_text("common.save", "en")  # "Save"
pm.get_text("common.save", "de")  # "Speichern"
```

## Development

```bash
# Install dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Lint
poetry run ruff check pluginforge/ tests/

# Format
poetry run ruff format pluginforge/ tests/
```

## License

MIT
