# PluginForge Examples

## simple_app

A minimal FastAPI application demonstrating PluginForge.

### Setup

```bash
cd examples/simple_app
pip install pluginforge[fastapi] uvicorn
python app.py
```

### Endpoints

- `GET /` - App info and active plugins
- `GET /api/plugins/hello/hello` - Hello greeting from plugin

### Config

- `config/app.yaml` - Application config with enabled plugins
- `config/plugins/hello.yaml` - Hello plugin config
- `config/i18n/en.yaml` / `de.yaml` - Translations
