# Tools: Web API

Catpile runs as a web service with compile and decompile endpoints.

## Starting the Server

```bash
# Development (HTTP)
python3 -m catpile.web

# Production (gunicorn)
gunicorn catpile.web:app -b 0.0.0.0:8788
```

## Endpoints

### `POST /compile`

Compile CatLang source to CatWeb JSON.

**Request:**
```json
{
  "source": "script \"game\":\n    on loaded:\n        log(\"hello\")",
  "taste": "indent",
  "config": {}
}
```

**Response:**
```json
[
  {
    "class": "script",
    "globalid": "aB",
    "content": [{"id": 0, "text": ["When website loaded..."], "actions": [...], "globalid": "cD"}],
    "alias": "game",
    "enabled": "true"
  }
]
```

### `POST /decompile`

Decompile CatWeb JSON to CatLang source + `.catui`.

**Request:** Full page JSON or array of script objects.

**Response:**
```json
{
  "game.cat": "script \"game\":\n    on loaded:\n        log(\"hello\")",
  "page.catui": "{\"paths\": {\"Page.Element\": \"globalid\"}, ...}",
  "page.json": "[\n  {\"class\": \"script\", ...}\n]"
}
```

### Error Handling

Errors return HTTP 400/500 with JSON:

```json
{
  "error": "[script_name] Expected NUMBER, got IDENT='l_value' at line 14",
  "type": "ParseError",
  "script": "script_name",
  "line": 14
}
```

## CORS

The server sets CORS headers for cross-origin requests from the web editor.

## Online Editor

Available at: **[cpile.bouyakhsass.com](https://cpile.bouyakhsass.com)**

Features:
- Multi-script project editing
- Import CatWeb JSON (decompile)
- Full Project compilation
- Syntax highlighting (Monaco editor)
- Auto-complete for actions, variables, page paths, Colors
- Color picker for hex values
- UI properties editor
- VFS search
- Export compiled JSON + .catui

### API Base URL

The editor sends requests to `https://cpile.bouyakhsass.com/api/`

| Endpoint | URL |
|---|---|
| Compile | `POST /api/compile` |
| Decompile | `POST /api/decompile` |

### Using the API from Code

```python
import requests

# Compile
resp = requests.post("https://cpile.bouyakhsass.com/api/compile", json={
    "source": "on loaded:\n    log('Hello')",
    "taste": "indent",
    "config": {}
})
print(resp.json())

# Decompile
with open("page.json") as f:
    page_data = json.load(f)
resp = requests.post("https://cpile.bouyakhsass.com/api/decompile", json=page_data)
files = resp.json()
for name, content in files.items():
    with open(name, "w") as f:
        f.write(content)
```
