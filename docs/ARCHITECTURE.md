# PluginForge - Architektur

**Version:** 0.1.0
**Stand:** 2026-03-26
**Lizenz:** MIT
**Basis:** pluggy (De-facto-Standard, genutzt von pytest, tox, datasette, kedro)

---

## 1. Ziel

PluginForge ist ein anwendungsunabhaengiges Python-Plugin-Framework. Es baut auf pluggy auf und ergaenzt die Schichten, die pluggy fehlen:

- YAML-Konfigurationssystem (App-Config, Plugin-Config, i18n)
- Plugin-Lifecycle (init, activate, deactivate)
- Enable/Disable per Config
- Plugin-Abhaengigkeitsaufloesung
- FastAPI-Router-Integration
- Alembic-Migration-Support fuer Plugin-eigene Tabellen
- API-Versionierung fuer Hook-Specs

PluginForge ist kein Konkurrent zu pluggy, sondern eine hoehere Abstraktionsschicht:
**pluggy + Config + Lifecycle + Web-Integration**

---

## 2. Bekannte Anwendungen (geplant)

| App | Beschreibung | Entry Point Group |
|-----|-------------|-------------------|
| Bibliogon | Buch-Autoren-Plattform | `bibliogon.plugins` |
| AdaptivLearner | Adaptives Lernsystem | `adaptivlearner.plugins` |

Ein Drittentwickler kann PluginForge fuer beliebige Anwendungen nutzen (CMS, Podcast-Tool, etc.).

---

## 3. Paketstruktur

```
pluginforge/
├── pluginforge/
│   ├── __init__.py          # Public API: PluginManager, BasePlugin, hookspec
│   ├── base.py              # BasePlugin (abstrakte Basisklasse)
│   ├── manager.py           # PluginManager (wraps pluggy + Config + Lifecycle)
│   ├── config.py            # YAML-Konfigurationssystem
│   ├── discovery.py         # Entry Point Discovery + Dependency Resolution
│   ├── lifecycle.py         # Plugin-Lifecycle-Management
│   ├── fastapi_ext.py       # FastAPI-Router-Integration (optional import)
│   ├── alembic_ext.py       # Alembic-Migration-Support (optional import)
│   └── i18n.py              # Internationalisierung via YAML
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures: temp configs, sample plugins
│   ├── test_base.py
│   ├── test_manager.py
│   ├── test_config.py
│   ├── test_discovery.py
│   ├── test_lifecycle.py
│   ├── test_fastapi_ext.py
│   ├── test_alembic_ext.py
│   └── test_i18n.py
├── examples/
│   ├── simple_app/
│   │   ├── config/
│   │   │   ├── app.yaml
│   │   │   ├── plugins/
│   │   │   │   └── hello.yaml
│   │   │   └── i18n/
│   │   │       ├── de.yaml
│   │   │       └── en.yaml
│   │   ├── app.py            # Minimale FastAPI-App mit PluginForge
│   │   └── plugins/
│   │       └── hello_plugin.py
│   └── README.md
├── pyproject.toml
├── README.md
├── LICENSE
├── CLAUDE.md
├── Makefile
└── .gitignore
```

---

## 4. Kernkomponenten

### 4.1 BasePlugin

```python
from abc import ABC
from typing import Any

class BasePlugin(ABC):
    """Abstrakte Basisklasse fuer alle PluginForge-Plugins."""

    name: str                          # Eindeutiger Bezeichner (z.B. "export")
    version: str = "0.1.0"
    api_version: str = "1"             # Kompatibilitaet mit Hook-Spec-Version
    description: str = ""
    author: str = ""
    depends_on: list[str] = []         # Plugin-Abhaengigkeiten (z.B. ["export"])
    config: dict[str, Any] = {}

    def init(self, app_config: dict, plugin_config: dict) -> None:
        """Wird beim Laden aufgerufen. Erhaelt App- und Plugin-Config."""
        self.config = plugin_config

    def activate(self) -> None:
        """Wird beim Aktivieren aufgerufen."""
        pass

    def deactivate(self) -> None:
        """Wird beim Deaktivieren aufgerufen. Ressourcen freigeben."""
        pass

    def get_routes(self) -> list:
        """FastAPI-Router zurueckgeben. Optional."""
        return []

    def get_migrations_dir(self) -> str | None:
        """Pfad zu Alembic-Migrationsskripten. Optional."""
        return None
```

### 4.2 PluginManager

Zentrale Klasse. Wraps pluggy.PluginManager und ergaenzt:

- YAML-Config laden (App + pro Plugin)
- Plugin-Discovery via Entry Points
- Lifecycle-Management (init -> activate -> deactivate)
- Abhaengigkeitspruefung
- Enable/Disable per Config
- i18n-Strings laden

```python
class PluginManager:
    def __init__(self, config_path: str = "config/app.yaml"):
        ...

    # Config
    def get_app_config(self) -> dict: ...
    def get_plugin_config(self, plugin_name: str) -> dict: ...

    # Discovery + Lifecycle
    def discover_plugins(self) -> None: ...
    def activate_plugin(self, name: str) -> None: ...
    def deactivate_plugin(self, name: str) -> None: ...
    def get_plugin(self, name: str) -> BasePlugin | None: ...
    def get_active_plugins(self) -> list[BasePlugin]: ...

    # Hooks (delegiert an pluggy)
    def register_hookspecs(self, spec_module) -> None: ...
    def call_hook(self, hook_name: str, **kwargs) -> list: ...

    # FastAPI-Integration
    def mount_routes(self, app: "FastAPI") -> None: ...

    # i18n
    def get_text(self, key: str, lang: str = "en") -> str: ...
```

### 4.3 YAML-Konfiguration

**App-Config** (`config/app.yaml`):

```yaml
app:
  name: "MyApp"
  version: "1.0.0"
  description: "Beschreibung"
  default_language: "de"

plugins:
  entry_point_group: "myapp.plugins"
  enabled:
    - "export"
    - "analytics"
  disabled:
    - "experimental"
```

**Plugin-Config** (`config/plugins/{name}.yaml`):

```yaml
# config/plugins/export.yaml
formats:
  - epub
  - pdf
pandoc_path: "/usr/bin/pandoc"
pdf_engine: "xelatex"
```

**i18n** (`config/i18n/{lang}.yaml`):

```yaml
# config/i18n/de.yaml
app:
  title: "Meine App"
  subtitle: "Untertitel"
plugins:
  export:
    label: "Export"
    description: "Buecher exportieren"
common:
  save: "Speichern"
  cancel: "Abbrechen"
  delete: "Loeschen"
```

### 4.4 Plugin-Discovery

Discovery-Reihenfolge:

1. Entry Points aus `entry_point_group` laden (installierte Pakete)
2. Gegen `enabled`/`disabled`-Liste in app.yaml filtern
3. Abhaengigkeiten pruefen (`depends_on`)
4. Topologisch sortieren (Abhaengigkeiten zuerst laden)
5. `init()` aufrufen mit Config
6. `activate()` aufrufen

Fehlerbehandlung:
- Fehlende Abhaengigkeit: Plugin wird uebersprungen, Warnung geloggt
- Zirkulaere Abhaengigkeit: Exception
- Plugin-Fehler in init/activate: Plugin wird uebersprungen, Fehler geloggt

### 4.5 FastAPI-Integration (optional)

```python
# In der Anwendung:
from fastapi import FastAPI
from pluginforge import PluginManager

app = FastAPI()
pm = PluginManager("config/app.yaml")
pm.discover_plugins()
pm.mount_routes(app)  # Alle Plugin-Router unter /api/plugins/{name}/
```

Jedes Plugin kann `get_routes()` ueberschreiben und einen oder mehrere FastAPI-Router zurueckgeben. Diese werden automatisch gemountet.

### 4.6 Alembic-Integration (optional)

Plugins koennen eigene DB-Tabellen mitbringen. `get_migrations_dir()` gibt den Pfad zu den Alembic-Migrationsskripten zurueck. Der PluginManager sammelt alle Migrations-Verzeichnisse und stellt sie der Anwendung bereit.

### 4.7 API-Versionierung

Hook-Specs werden versioniert. Plugins deklarieren `api_version: "1"`. Wenn sich Hooks aendern:

- Neue Spec-Version (v2) wird erstellt
- Alte Hooks bleiben erhalten (Deprecation-Warnung)
- Plugins mit alter api_version funktionieren weiter
- Erst bei Major-Release werden alte Hooks entfernt

---

## 5. Abhaengigkeiten (minimal)

**Runtime:**
- `pluggy >= 1.5.0` (Hook-System)
- `pyyaml >= 6.0` (YAML-Config)

**Optional:**
- `fastapi` (nur wenn FastAPI-Integration genutzt wird)
- `alembic` (nur wenn Migrations-Support genutzt wird)

**Dev:**
- `pytest`
- `pytest-cov`
- `ruff` (Linting)

---

## 6. Offene Designentscheidungen

| Frage | Empfehlung |
|-------|------------|
| Soll PluginForge selbst logging konfigurieren? | Nein, nur `logging.getLogger(__name__)` nutzen. Anwendung konfiguriert. |
| Soll es async-Hooks geben? | Nicht in v0.1.0. Spaeter optional. |
| Wie werden Plugin-Frontend-Manifeste behandelt? | v0.1.0 nur Backend. Frontend-Integration in v0.2.0. |
| Soll es einen CLI-Befehl geben? | Optional in v0.2.0 (`pluginforge list`, `pluginforge info`). |

---

## 7. Release-Kriterien v0.1.0

- [ ] BasePlugin, PluginManager, Config, Discovery, Lifecycle implementiert
- [ ] YAML-Config (App, Plugin, i18n) funktioniert
- [ ] Entry Point Discovery funktioniert
- [ ] Enable/Disable per Config funktioniert
- [ ] Abhaengigkeitsaufloesung funktioniert
- [ ] FastAPI-Integration funktioniert (optional import)
- [ ] Tests: >= 90% Coverage
- [ ] README mit Quickstart und Beispiel
- [ ] Auf PyPI publiziert als `pluginforge`
- [ ] Beispiel-App in `examples/`
