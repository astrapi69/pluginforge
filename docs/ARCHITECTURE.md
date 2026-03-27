# PluginForge - Architektur

**Version:** 0.5.0
**Stand:** 2026-03-27
**Lizenz:** MIT
**Basis:** pluggy (De-facto-Standard, genutzt von pytest, tox, datasette, kedro)

---

## 1. Ziel

PluginForge ist ein anwendungsunabhaengiges Python-Plugin-Framework. Es baut auf pluggy auf und ergaenzt die Schichten, die pluggy fehlen:

- YAML-Konfigurationssystem (App-Config, Plugin-Config, i18n)
- Plugin-Lifecycle (init, activate, deactivate, hot-reload)
- Enable/Disable per Config
- Plugin-Abhaengigkeitsaufloesung
- Extension Points (Plugins nach Interface abfragen)
- Config Schema Validation
- Health Checks
- Pre-Activate Hooks (Lizenzpruefung, etc.)
- Error Reporting (get_load_errors)
- Plugin Introspection (get_plugin_hooks, get_all_hook_names)
- Graceful Degradation (call_hook_safe)
- FastAPI-Router-Integration
- Alembic-Migration-Support fuer Plugin-eigene Tabellen
- API-Versionierung fuer Hook-Specs
- Security (Plugin-Name-Validierung, Path Traversal Prevention)

PluginForge ist kein Konkurrent zu pluggy, sondern eine hoehere Abstraktionsschicht:
**pluggy + Config + Lifecycle + Extensions + Security + Web-Integration**

---

## 2. Bekannte Anwendungen

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
│   ├── __init__.py          # Public API: PluginManager, BasePlugin, Exceptions
│   ├── base.py              # BasePlugin (abstrakte Basisklasse)
│   ├── manager.py           # PluginManager (wraps pluggy + Config + Lifecycle)
│   ├── config.py            # YAML-Konfigurationssystem
│   ├── discovery.py         # Entry Point Discovery + Dependency Resolution
│   ├── lifecycle.py         # Plugin-Lifecycle-Management + Config Validation
│   ├── security.py          # Plugin-Name-Validierung, Path Traversal Prevention
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
│   ├── test_i18n.py
│   └── test_security.py
├── examples/
│   └── simple_app/
├── docs/
│   └── ARCHITECTURE.md
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
    depends_on: list[str] = []         # Plugin-Abhaengigkeiten
    app_config: dict[str, Any] = {}    # Globale App-Config (gesetzt in init)
    config: dict[str, Any] = {}        # Plugin-Config (gesetzt in init)
    config_schema: dict[str, type] | None = None  # Optional: Config-Typ-Validierung

    def init(self, app_config: dict, plugin_config: dict) -> None:
        """Wird beim Laden aufgerufen. Erhaelt App- und Plugin-Config."""
        self.app_config = app_config
        self.config = plugin_config

    def activate(self) -> None:
        """Wird beim Aktivieren aufgerufen."""

    def deactivate(self) -> None:
        """Wird beim Deaktivieren aufgerufen. Ressourcen freigeben."""

    def get_routes(self) -> list:
        """FastAPI-Router zurueckgeben. Optional."""
        return []

    def get_frontend_manifest(self) -> dict[str, Any] | None:
        """Frontend-UI-Manifest zurueckgeben. Optional."""
        return None

    def health(self) -> dict[str, Any]:
        """Health-Status zurueckgeben. Optional."""
        return {"status": "ok"}

    def get_migrations_dir(self) -> str | None:
        """Pfad zu Alembic-Migrationsskripten. Optional."""
        return None
```

### 4.2 PluginManager

Zentrale Klasse. Wraps pluggy.PluginManager und ergaenzt:

- YAML-Config laden (App + pro Plugin) + Reload
- Plugin-Discovery via Entry Points
- Plugin-Registrierung (Klassen, Instanzen, Entry Points)
- Lifecycle-Management (init -> activate -> deactivate -> hot-reload)
- Pre-Activate Callback (Lizenzpruefung, etc.)
- API-Version Kompatibilitaetspruefung
- Abhaengigkeitspruefung + topologische Sortierung
- Enable/Disable per Config
- Config Schema Validation
- Error Reporting (get_load_errors)
- Extension Points (get_extensions)
- Health Checks (health_check)
- Plugin Introspection (get_plugin_hooks, get_all_hook_names)
- Graceful Hook Degradation (call_hook_safe)
- i18n-Strings laden
- Security (Plugin-Name-Validierung)

```python
class PluginManager:
    def __init__(self, config_path="config/app.yaml", pre_activate=None, api_version="1"):
        ...

    # Config
    def get_app_config(self) -> dict: ...
    def get_plugin_config(self, plugin_name: str) -> dict: ...
    def reload_config(self) -> None: ...

    # Discovery + Registration
    def list_available_plugins(self) -> list[str]: ...
    def discover_plugins(self) -> None: ...
    def register_plugins(self, plugin_classes: list) -> None: ...
    def register_plugin(self, plugin: BasePlugin, plugin_config=None) -> None: ...

    # Lifecycle
    def activate_plugin(self, name: str) -> None: ...
    def deactivate_plugin(self, name: str) -> None: ...
    def deactivate_all(self) -> None: ...
    def reload_plugin(self, name: str) -> bool: ...
    def get_plugin(self, name: str) -> BasePlugin | None: ...
    def get_active_plugins(self) -> list[BasePlugin]: ...

    # Error Reporting
    def get_load_errors(self) -> dict[str, str]: ...

    # Health Checks
    def health_check(self) -> dict[str, dict]: ...

    # Hooks (delegiert an pluggy)
    def register_hookspecs(self, spec_module) -> None: ...
    def call_hook(self, hook_name: str, **kwargs) -> list: ...
    def call_hook_safe(self, hook_name: str, **kwargs) -> list: ...

    # Introspection
    def get_plugin_hooks(self, name: str) -> list[str]: ...
    def get_all_hook_names(self) -> list[str]: ...

    # Extensions
    def get_extensions(self, extension_point: type) -> list[BasePlugin]: ...

    # FastAPI-Integration
    def mount_routes(self, app, prefix="/api") -> None: ...

    # i18n
    def get_text(self, key: str, lang: str = "en") -> str: ...

    # Alembic
    def collect_migrations(self) -> dict[str, str]: ...
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
plugins:
  export:
    label: "Export"
common:
  save: "Speichern"
  cancel: "Abbrechen"
```

### 4.4 Plugin-Discovery

Discovery-Reihenfolge:

1. Entry Points aus `entry_point_group` laden (installierte Pakete)
2. Gegen `enabled`/`disabled`-Liste in app.yaml filtern
3. Plugin-Namen validieren (security.py)
4. Abhaengigkeiten pruefen (`depends_on`)
5. Topologisch sortieren (Abhaengigkeiten zuerst laden)
6. API-Version Kompatibilitaet pruefen (Warnung bei Mismatch)
7. `init()` aufrufen mit Config
8. `config_schema` validieren
9. `pre_activate` Callback aufrufen (wenn konfiguriert)
10. Bei pluggy registrieren
11. `activate()` aufrufen

Fehlerbehandlung:
- Fehlende Abhaengigkeit: Plugin wird uebersprungen, in get_load_errors() gemeldet
- Zirkulaere Abhaengigkeit: CircularDependencyError
- Plugin-Fehler in init/activate: Plugin wird uebersprungen, in get_load_errors() gemeldet
- Config-Schema-Verletzung: Plugin wird uebersprungen, in get_load_errors() gemeldet
- Pre-Activate Ablehnung: Plugin wird uebersprungen, in get_load_errors() gemeldet

### 4.5 Security

- Plugin-Namen werden per Regex validiert: Buchstaben, Ziffern, Unterstriche, Bindestriche, max 64 Zeichen
- Keine Pfad-Separatoren (`/`, `\`, `..`) erlaubt
- Config-Pfade werden gegen das Config-Verzeichnis aufgeloest
- Alembic-Migrations-Pfade werden zu absoluten Pfaden aufgeloest
- `InvalidPluginNameError` bei Verstoessen

### 4.6 FastAPI-Integration (optional)

```python
from fastapi import FastAPI
from pluginforge import PluginManager

app = FastAPI()
pm = PluginManager("config/app.yaml")
pm.discover_plugins()
pm.mount_routes(app)                    # Default: /api/
pm.mount_routes(app, prefix="/v2/api")  # Konfigurierbarer Prefix
```

Plugins kontrollieren ihre eigene URL-Struktur ueber ihren Router-Prefix.

### 4.7 Alembic-Integration (optional)

Plugins koennen eigene DB-Tabellen mitbringen. `get_migrations_dir()` gibt den Pfad zu den Alembic-Migrationsskripten zurueck. Pfade werden aufgeloest und validiert.

### 4.8 API-Versionierung

Hook-Specs werden versioniert. Plugins deklarieren `api_version: "1"`. Der PluginManager prueft die Kompatibilitaet:

- Mismatch wird geloggt als Warnung
- Plugin wird trotzdem geladen (Abwaertskompatibilitaet)
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

| Frage | Status |
|-------|--------|
| Soll PluginForge selbst logging konfigurieren? | Nein, nur `logging.getLogger(__name__)`. Anwendung konfiguriert. |
| Soll es async-Hooks geben? | Nicht geplant. Reconsider wenn eine App es braucht. |
| Semantic Versioning fuer depends_on? | Geplant fuer v0.6.0 (siehe Wiki Roadmap). |
| Transitive Extension-Zugriffe? | Geplant fuer v0.6.0. |
| Plugin Source Analysis? | Spaeter, nur fuer Marketplace relevant. |

---

## 7. Aktueller Stand

- 162 Tests, 93% Coverage
- v0.5.0 auf PyPI publiziert
- Wiki mit 15 Seiten inkl. Roadmap
- Bibliogon baut darauf auf
