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
pm.mount_routes(app)  # Routes under /api/ (configurable prefix)
```

## Features

- **YAML Configuration** - App config, per-plugin config, and i18n strings
- **Plugin Lifecycle** - init, activate, deactivate with error handling
- **Hot-Reload** - Swap plugins at runtime without app restart
- **Enable/Disable** - Control plugins via config lists
- **Dependency Resolution** - Topological sorting with circular dependency detection
- **Extension Points** - Query plugins by interface with `get_extensions(type)`
- **Config Schema Validation** - Declare expected config types per plugin
- **Health Checks** - Monitor plugin status via `health_check()`
- **Pre-Activate Hooks** - Reject plugins before activation (license checks, etc.)
- **FastAPI Integration** - Mount plugin routes with configurable prefix
- **Alembic Support** - Collect migration directories from plugins
- **i18n** - Multi-language strings from YAML with fallback
- **Security** - Plugin name validation and path traversal prevention

For detailed documentation, see the [Wiki](https://github.com/astrapi69/pluginforge/wiki).

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

## Documentation

The full documentation is available in the [Wiki](https://github.com/astrapi69/pluginforge/wiki):

- [Getting Started](https://github.com/astrapi69/pluginforge/wiki/Getting-Started)
- [BasePlugin](https://github.com/astrapi69/pluginforge/wiki/BasePlugin)
- [PluginManager](https://github.com/astrapi69/pluginforge/wiki/PluginManager)
- [Configuration](https://github.com/astrapi69/pluginforge/wiki/Configuration)
- [Discovery and Dependencies](https://github.com/astrapi69/pluginforge/wiki/Discovery-and-Dependencies)
- [Lifecycle](https://github.com/astrapi69/pluginforge/wiki/Lifecycle)
- [Hooks](https://github.com/astrapi69/pluginforge/wiki/Hooks)
- [Extensions](https://github.com/astrapi69/pluginforge/wiki/Extensions)
- [FastAPI Integration](https://github.com/astrapi69/pluginforge/wiki/FastAPI-Integration)
- [Alembic Integration](https://github.com/astrapi69/pluginforge/wiki/Alembic-Integration)
- [i18n](https://github.com/astrapi69/pluginforge/wiki/i18n)
- [Security](https://github.com/astrapi69/pluginforge/wiki/Security)
- [Examples](https://github.com/astrapi69/pluginforge/wiki/Examples)
- [Changelog](https://github.com/astrapi69/pluginforge/wiki/Changelog)
- [Roadmap](https://github.com/astrapi69/pluginforge/wiki/Roadmap)

## Development

```bash
make install-dev   # Install with dev dependencies
make test          # Run tests
make lint          # Run ruff linter
make format        # Format code
make ci            # Full CI pipeline (lint + format-check + test)
make help          # Show all available targets
```

## License

MIT
