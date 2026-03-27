# CLAUDE.md

## Was ist PluginForge?

Anwendungsunabhaengiges Python-Plugin-Framework. Baut auf pluggy auf und ergaenzt:
YAML-Config, Lifecycle, Enable/Disable, Abhaengigkeiten, FastAPI-Integration, i18n.

**Repository:** https://github.com/astrapi69/pluginforge
**Architektur:** docs/ARCHITECTURE.md (lesen vor jeder Aenderung)
**Lizenz:** MIT
**Ziel:** v0.2.0 auf PyPI publizieren

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

    def activate(self) -> None:
        # PluginForge Lifecycle
        self.engine = self.config.get("engine", "default")

    @hookimpl
    def on_document_save(self, document: dict) -> None:
        # pluggy Hook - wird via pm.call_hook("on_document_save", ...) aufgerufen
        ...
```

Wichtig: Ab pluggy 1.1.0 brauchen Hook Wrapper explizit `wrapper=True`.

## Kernlogik

### PluginManager Ablauf

```
1. __init__(config_path)
   -> config.py: app.yaml laden
   -> pluggy.PluginManager erstellen mit entry_point_group aus Config

2. discover_plugins()
   -> discovery.py: Entry Points laden
   -> Gegen enabled/disabled filtern
   -> depends_on pruefen (topologische Sortierung)
   -> Fuer jeden aktiven Plugin:
      a) Plugin-YAML laden (config/plugins/{name}.yaml)
      b) plugin.init(app_config, plugin_config)
      c) Bei pluggy registrieren
      d) plugin.activate()

3. call_hook(hook_name, **kwargs)
   -> Delegiert an pluggy pm.hook.{hook_name}(**kwargs)

4. mount_routes(fastapi_app)
   -> Fuer jeden aktiven Plugin mit get_routes():
      Router unter /api/plugins/{name}/ mounten

5. deactivate_all()
   -> Umgekehrte Reihenfolge: deactivate() fuer jeden Plugin
```

### Config-Merge-Logik

```
App-Config (config/app.yaml)
  + Plugin-Config (config/plugins/{name}.yaml)  # merged in plugin.config
  + i18n (config/i18n/{lang}.yaml)               # separat, via get_text()
```

Fehlende Config-Dateien sind kein Fehler, nur leere Defaults.

### Dependency Resolution

```python
# Topologische Sortierung
# Input: {"a": ["b"], "b": [], "c": ["a", "b"]}
# Output: ["b", "a", "c"]
# Zirkulaere Abhaengigkeit -> Exception
```

## pyproject.toml Vorgaben

```toml
[tool.poetry]
name = "pluginforge"
version = "0.2.0"
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
install:        poetry install --with dev
test:           poetry run pytest
lint:           poetry run ruff check pluginforge/ tests/
format:         poetry run ruff format pluginforge/ tests/
typecheck:      poetry run mypy pluginforge/ (optional, spaeter)
build:          poetry build
publish:        poetry publish
clean:          rm -rf dist/ .pytest_cache/ .coverage
```

## Tests

- Jede Komponente (base, manager, config, discovery, lifecycle, fastapi_ext, i18n) hat eigene Testdatei
- conftest.py: Fixtures fuer temporaere YAML-Configs und Sample-Plugins
- Sample-Plugins als Klassen in tests/ definieren (nicht als Entry Points)
- Fuer Entry Point Tests: `pm.register()` direkt nutzen statt echte Entry Points
- Ziel: >= 90% Coverage

### Wichtige Testfaelle

1. Plugin laden, aktivieren, deaktivieren
2. YAML-Config laden (app, plugin, i18n)
3. Fehlende Config-Datei: kein Fehler, leere Defaults
4. Enable/Disable per Config
5. Abhaengigkeit vorhanden: Plugin wird geladen
6. Abhaengigkeit fehlt: Plugin wird uebersprungen, Warnung
7. Zirkulaere Abhaengigkeit: Exception
8. FastAPI-Router mounten (wenn fastapi installiert)
9. i18n: String in verschiedenen Sprachen abrufen
10. i18n: Fallback auf Default-Sprache wenn Key fehlt
11. Plugin mit falscher api_version: Warnung, trotzdem laden

## Beispiel-App (examples/simple_app/)

Eine minimale FastAPI-App die zeigt wie PluginForge funktioniert:

- `config/app.yaml`: App-Name, enabled Plugins
- `config/plugins/hello.yaml`: Greeting-Text
- `config/i18n/de.yaml` + `en.yaml`: UI-Strings
- `app.py`: FastAPI + PluginManager Setup
- `plugins/hello_plugin.py`: SimplePlugin das einen /hello Endpoint bereitstellt

## Release-Workflow

1. Alle Tests gruen, >= 90% Coverage
2. README mit Quickstart, Installation, Beispiel
3. `poetry build`
4. `poetry publish -r testpypi` (Test)
5. `pip install -i https://test.pypi.org/simple/ pluginforge` (Verify)
6. `poetry publish` (Production)
7. Git Tag `v0.1.0`

## Kontext: Warum PluginForge existiert

Bibliogon (Buch-Autoren-Plattform) und AdaptivLearner (Lernsystem) bauen beide darauf auf. PluginForge muss
anwendungsunabhaengig sein. Kein Bibliogon-spezifischer Code darf hier rein. Alles was Bibliogon-spezifisch ist, gehoert
in das Bibliogon-Repo als Plugin oder Hook-Spec.
