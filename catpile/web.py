"""WSGI web API for Catpile - compile .cat source via HTTP POST.

Usage (development):
    python3 -m catpile.web

Usage (production, behind nginx/Cloudflare):
    gunicorn catpile.web:app  # or any WSGI server

Deploy on Vercel:
    This file can be adapted as a serverless function.
    See: https://vercel.com/docs/functions
"""

import json
import os
import sys
from typing import Any
from wsgiref.simple_server import make_server

from .parser import parse, ParseError
from .emitter import Emitter, EmitError
from .ir import Program


# ---------------------------------------------------------------------------
# WSGI Application
# ---------------------------------------------------------------------------

def app(environ: dict, start_response: Any) -> list[bytes]:
    """WSGI entry point.

    GET   /       →  HTML form (test page)
    POST  /       →  Compile .cat source, return CatWeb JSON
    POST  /compile  →  Same as POST / (accepts JSON body)
    POST  /decompile →  Decompile CatWeb page JSON → .cat + .catui
    """
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/").rstrip("/") or "/"

    # --- CORS headers ---
    cors_headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]

    if method == "OPTIONS":
        start_response("200 OK", cors_headers + [("Content-Type", "text/plain")])
        return [b""]

    if method == "GET" and path == "/":
        return _serve_form(start_response, cors_headers)

    if method == "POST":
        if path == "/decompile":
            return _handle_decompile(environ, start_response, cors_headers)
        return _handle_compile(environ, start_response, cors_headers)

    start_response("404 Not Found", cors_headers + [
        ("Content-Type", "application/json"),
    ])
    return [json.dumps({"error": "Not found"}).encode()]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _serve_form(start_response, cors_headers) -> list[bytes]:
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Catpile Compiler</title>
<style>
body{font-family:system-ui,sans-serif;max-width:800px;margin:2em auto;padding:0 1em}
textarea{width:100%;font-family:monospace;font-size:13px}
h1{color:#333}
button{background:#0070f3;color:#fff;border:none;padding:8px 16px;border-radius:4px;cursor:pointer}
button:hover{background:#0050c0}
pre{background:#f5f5f5;padding:1em;border-radius:4px;overflow:auto}
.error{color:#d00}
</style></head>
<body>
<h1>Catpile Compiler</h1>
<p>Write Catpile source and compile to CatWeb JSON.</p>
<form method="POST" action="/">
<textarea name="source" rows="15" placeholder="on loaded:&#10;    log(&quot;Hello!&quot;)" required></textarea>
<br><br>
<button type="submit">Compile</button>
</form>
<script>
// Handle form submission via fetch to avoid page navigation
document.querySelector('form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const res = await fetch(form.action, {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams(new FormData(form))
    });
    const data = await res.json();
    const pre = document.createElement('pre');
    if (res.ok) {
        pre.textContent = JSON.stringify(data, null, 2);
    } else {
        pre.className = 'error';
        pre.textContent = 'Error: ' + (data.error || res.statusText);
    }
    const existing = document.querySelector('pre');
    if (existing) existing.remove();
    form.after(pre);
});
</script>
</body></html>"""
    start_response("200 OK", cors_headers + [
        ("Content-Type", "text/html; charset=utf-8"),
    ])
    return [html.encode("utf-8")]


def _handle_compile(environ, start_response, cors_headers) -> list[bytes]:
    # Read request body
    try:
        content_length = int(environ.get("CONTENT_LENGTH", "0"))
    except ValueError:
        content_length = 0

    body = environ["wsgi.input"].read(content_length)

    # Parse form data or JSON
    content_type = environ.get("CONTENT_TYPE", "")
    source: str = ""

    if "application/json" in content_type:
        try:
            data = json.loads(body)
            source = data.get("source", "")
        except (json.JSONDecodeError, TypeError):
            source = ""
    else:
        # form-encoded
        try:
            from urllib.parse import parse_qs
            params = parse_qs(body.decode("utf-8"))
            source = params.get("source", [""])[0]
        except Exception:
            source = ""

    if not source.strip():
        start_response("400 Bad Request", cors_headers + [
            ("Content-Type", "application/json"),
        ])
        return [json.dumps({"error": "Missing 'source' field"}).encode()]

    # Compile
    try:
        prog = parse(source)
        emitter = Emitter()
        result = emitter.emit(prog)
        data = json.loads(result)
        start_response("200 OK", cors_headers + [
            ("Content-Type", "application/json"),
        ])
        return [json.dumps(data, indent=2).encode()]
    except (ParseError, EmitError, SyntaxError) as e:
        # Find which script the error occurred in for multi-script projects
        script_name, local_line = _find_script_name(source, str(e))
        if script_name and local_line:
            import re
            msg = re.sub(r"at line \d+", f"at line {local_line}", str(e))
            prefix = f"[{script_name}] "
        else:
            msg = str(e)
            prefix = ""
        start_response("400 Bad Request", cors_headers + [
            ("Content-Type", "application/json"),
        ])
        return [json.dumps({
            "error": prefix + msg,
            "type": type(e).__name__,
            "script": script_name,
            "line": local_line
        }).encode()]


def _find_script_name(source: str, error_msg: str) -> tuple[str | None, int | None]:
    """Find which script an error occurred in and the local line number.

    Parses ``script "name":`` directives, maps line ranges to script names,
    and converts the absolute line number to a local line within the script.
    """
    import re
    line_match = re.search(r"at line (\d+)", error_msg)
    if not line_match:
        return None, None
    error_line = int(line_match.group(1))

    # Find all script directives and their line ranges
    script_ranges: list[tuple[int, str]] = []
    for m in re.finditer(r'^script\s+"([^"]+)"\s*:', source, re.MULTILINE):
        script_name = m.group(1)
        start_line = source[: m.start()].count('\n') + 1
        script_ranges.append((start_line, script_name))

    if not script_ranges:
        return None, None

    # Find which script the error line falls in
    for i, (start, name) in enumerate(script_ranges):
        end = script_ranges[i + 1][0] - 1 if i + 1 < len(script_ranges) else 999999
        if start <= error_line <= end:
            local_line = error_line - start + 1  # relative to script body
            return name, local_line

    return None, None


def _read_body(environ) -> bytes:
    try:
        cl = int(environ.get("CONTENT_LENGTH", "0"))
    except ValueError:
        cl = 0
    return environ["wsgi.input"].read(cl)


def _handle_decompile(environ, start_response, cors_headers) -> list[bytes]:
    body = _read_body(environ)
    content_type = environ.get("CONTENT_TYPE", "")

    page_json: list | dict | None = None
    if "application/json" in content_type:
        try:
            data = json.loads(body)
            page_json = data.get("webcontent", data) if isinstance(data, dict) else data
        except (json.JSONDecodeError, TypeError):
            pass

    if page_json is None:
        try:
            from urllib.parse import parse_qs
            params = parse_qs(body.decode("utf-8"))
            raw = params.get("page", [""])[0]
            if raw:
                data = json.loads(raw)
                page_json = data.get("webcontent", data) if isinstance(data, dict) else data
        except Exception:
            pass

    if not page_json:
        start_response("400 Bad Request", cors_headers + [
            ("Content-Type", "application/json"),
        ])
        return [json.dumps({"error": "Missing page JSON"}).encode()]

    try:
        from .decompiler import decompile_page
        if not isinstance(page_json, list):
            page_json = [page_json]
        outputs = decompile_page(page_json, "page")
        start_response("200 OK", cors_headers + [
            ("Content-Type", "application/json"),
        ])
        return [json.dumps(outputs, indent=2).encode()]
    except Exception as e:
        start_response("400 Bad Request", cors_headers + [
            ("Content-Type", "application/json"),
        ])
        return [json.dumps({"error": str(e), "type": type(e).__name__}).encode()]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8788"))
    with make_server("0.0.0.0", port, app) as httpd:
        print(f"Catpile web API listening on http://0.0.0.0:{port}")
        httpd.serve_forever()
