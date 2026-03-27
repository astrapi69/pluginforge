# CLAUDE.md

## Was ist PluginForge?

Anwendungsunabhaengiges Python-Plugin-Framework. Baut auf pluggy auf und ergaenzt:
YAML-Config, Lifecycle, Enable/Disable, Abhaengigkeiten, FastAPI-Integration, i18n,
Extension Points, Hot-Reload, Health Checks, Config Schema Validation, Security.

**Repository:** https://github.com/astrapi69/pluginforge
**Architektur:** docs/ARCHITECTURE.md (lesen vor jeder Aenderung)
**Wiki:** https://github.com/astrapi69/pluginforge/wiki
**Lizenz:** MIT
**Aktuelle Version:** v0.5.0 auf PyPI

## Tech Stack

- Python 3.11+
- pluggy >= 1.5.0 (Hook-System, NICHT selbst bauen - ab 1.1.0 new-style Hook Wrapper mit explizitem wrapper=True)
- PyYAML >= 6.0 (Konfiguration)
- FastAPI (optional, nur wenn importiert)
- Alembic (optional, nur wenn importiert)
- Poetry (Paketmanagement)
- pytest + pytest-cov (Tests)
- ruff (Linting)

## Paketstruktur

```
pluginforge/
├── pluginforge/
│   ├── __init__.py          # Public API exportieren
│   ├── base.py              # BasePlugin
│   ├── manager.py           # PluginManager
│   ├── config.py            # YAML-Config laden/mergen
│   ├── discovery.py         # Entry Point Discovery + Dependency Resolution
│   ├── lifecycle.py         # init/activate/deactivate Steuerung
│   ├── security.py          # Plugin-Name-Validierung, Path Traversal Prevention
│   ├── fastapi_ext.py       # FastAPI-Router mounten (optional)
│   ├── alembic_ext.py       # Alembic-Migrations sammeln (optional)
│   └── i18n.py              # Mehrsprachige Strings aus YAML
├── tests/
├── examples/simple_app/
├── pyproject.toml
├── README.md
├── LICENSE
├── Makefile
└── .gitignore
```

## Konventionen

- Typehints ueberall, kein `Any` wo ein konkreter Typ moeglich ist
- Keine Em-Dashes (--), stattdessen Bindestriche (-) oder Kommata
- Commit Messages: Englisch, konventionell (feat/fix/refactor/docs/test)
- Docstrings: Google-Style
- Logging: `logging.getLogger(__name__)`, keine eigene Log-Config
- Optional Dependencies: Lazy Import mit klarer Fehlermeldung wenn nicht installiert
- Keine hartcodierten Strings, alles via Config
- Plugin-Namen werden validiert (security.py) - keine Pfad-Separatoren, max 64 Zeichen

## BasePlugin + pluggy Hook-Integration (Design-Klarstellung)

Ein Plugin ist beides gleichzeitig:
- Eine Klasse die `BasePlugin` erbt (Lifecycle: init, activate, deactivate)
- Ein Objekt mit `@hookimpl`-dekorierten Methoden (pluggy Hook-System)

PluginForge managed den Lifecycle drumherum, pluggy managed die Hooks.

```python
import pluggy
from pluginforge import BasePlugin

hookimpl = pluggy.HookimplMarker("myapp")

class ExportPlugin(BasePlugin):
    name = "export"
    depends_on = ["storage"]
    config_schema = {"formats": list, "pandoc_path": str}

    def activate(self) -> None:
        # PluginForge Lifecycle
        self.engine = self.config.get("engine", "default")

    def health(self) -> dict:
        return {"status": "ok", "engine": self.engine}

    @hookimpl
    def on_document_save(self, document: dict) -> None:
        # pluggy Hook - wird via pm.call_hook("on_document_save", ...) aufgerufen
        ...
```

Wichtig: Ab pluggy 1.1.0 brauchen Hook Wrapper explizit `wrapper=True`.

## Kernlogik

### PluginManager Ablauf

```
1. __init__(config_path, pre_activate=None, api_version="1")
   -> config.py: app.yaml laden
   -> pluggy.PluginManager erstellen mit entry_point_group aus Config

2. discover_plugins() / register_plugins([classes]) / register_plugin(instance)
   -> discovery.py: Entry Points laden (oder Klassen/Instanzen direkt)
   -> Gegen enabled/disabled filtern
   -> Plugin-Namen validieren (security.py)
   -> depends_on pruefen (topologische Sortierung)
   -> api_version Kompatibilitaet pruefen (Warnung bei Mismatch)
   -> Fuer jeden aktiven Plugin:
      a) Plugin-YAML laden (config/plugins/{name}.yaml)
      b) plugin.init(app_config, plugin_config)
      c) config_schema validieren
      d) pre_activate Callback (wenn konfiguriert)
      e) Bei pluggy registrieren
      f) plugin.activate()
   -> Fehler werden in _load_errors gesammelt

3. call_hook(hook_name, **kwargs) / call_hook_safe(hook_name, **kwargs)
   -> Delegiert an pluggy pm.hook.{hook_name}(**kwargs)
   -> call_hook: faengt Exceptions, gibt [] zurueck
   -> call_hook_safe: ruft jede Implementation einzeln auf, uebersprungen fehlerhafte

4. get_extensions(ExtensionPoint)
   -> Alle aktiven Plugins zurueckgeben die den Typ implementieren

5. mount_routes(fastapi_app, prefix="/api")
   -> Fuer jeden aktiven Plugin mit get_routes():
      Router unter konfigurierbarem Prefix mounten

6. reload_plugin(name)
   -> deactivate -> re-import Modul -> re-init -> activate

7. deactivate_all()
   -> Umgekehrte Reihenfolge: deactivate() + pm.unregister() fuer jeden Plugin
```

### Config-Merge-Logik

```
App-Config (config/app.yaml)
  + Plugin-Config (config/plugins/{name}.yaml)  # merged in plugin.config
  + i18n (config/i18n/{lang}.yaml)               # separat, via get_text()
```

Fehlende Config-Dateien sind kein Fehler, nur leere Defaults.
Config-Schema wird validiert wenn config_schema auf dem Plugin definiert ist.

### Dependency Resolution

```python
# Topologische Sortierung
# Input: {"a": ["b"], "b": [], "c": ["a", "b"]}
# Output: ["b", "a", "c"]
# Zirkulaere Abhaengigkeit -> CircularDependencyError
```

## pyproject.toml Vorgaben

```toml
[tool.poetry]
name = "pluginforge"
version = "0.5.0"
description = "Application-agnostic plugin framework built on pluggy"
authors = ["Asterios Raptis"]
license = "MIT"
readme = "README.md"
repository = "https://github.com/astrapi69/pluginforge"
keywords = ["plugin", "framework", "pluggy", "hooks", "yaml"]
classifiers = [
   "Development Status :: 3 - Alpha",
   "Intended Audience :: Developers",
   "License :: OSI Approved :: MIT License",
   "Programming Language :: Python :: 3.11",
   "Programming Language :: Python :: 3.12",
   "Programming Language :: Python :: 3.13",
   "Topic :: Software Development :: Libraries :: Application Frameworks",
]
packages = [{ include = "pluginforge" }]

[tool.poetry.dependencies]
python = "^3.11"
pluggy = "^1.5.0"
pyyaml = "^6.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-cov = "^5.0"
ruff = "^0.4"

[tool.poetry.extras]
fastapi = ["fastapi"]
alembic = ["alembic", "sqlalchemy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=pluginforge --cov-report=term-missing"

[tool.ruff]
target-version = "py311"
line-length = 100

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## Makefile Targets

```makefile
install:        poetry install
install-dev:    poetry install --with dev
test:           poetry run pytest
test-fast:      poetry run pytest -q --maxfail=1 --disable-warnings --no-cov
lint:           poetry run ruff check pluginforge/ tests/
format:         poetry run ruff format pluginforge/ tests/
ci:             lint + format-check + test
bump-patch:     poetry version patch
bump-minor:     poetry version minor
build:          poetry build
publish:        ci + build + poetry publish
clean:          rm -rf dist/ build/ .pytest_cache/ .coverage
help:           Zeigt alle Targets
```

## Tests

- Jede Komponente hat eigene Testdatei (base, manager, config, discovery, lifecycle, fastapi_ext, alembic_ext, i18n, security)
- conftest.py: Fixtures fuer temporaere YAML-Configs und Sample-Plugins
- Sample-Plugins als Klassen in tests/ definieren (nicht als Entry Points)
- Fuer Entry Point Tests: `pm.register()` direkt nutzen statt echte Entry Points
- Aktuell: 162 Tests, 93% Coverage
- Ziel: >= 90% Coverage

## Release-Workflow

1. Alle Tests gruen, >= 90% Coverage
2. `make bump-minor` (oder bump-patch)
3. `make publish` (fuehrt CI + Build + Publish aus)
4. Git Tag `v0.x.0`
5. `git push origin main --tags`

## Kontext: Warum PluginForge existiert

Bibliogon (Buch-Autoren-Plattform) und AdaptivLearner (Lernsystem) bauen beide darauf auf. PluginForge muss
anwendungsunabhaengig sein. Kein Bibliogon-spezifischer Code darf hier rein. Alles was Bibliogon-spezifisch ist, gehoert
in das Bibliogon-Repo als Plugin oder Hook-Spec.
