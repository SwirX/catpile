"""Catpile Language Server - full LSP implementation over stdio.

Provides:
  - Code completion: actions, events, UI element paths from .catui files
  - Hover: action/event details with ID and schema
  - Diagnostics: syntax errors from the selected taste parser
  - Document symbols: events and functions in the outline
  - Snippet-like completion for control flow

Protocol: LSP 3.17 over stdio
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .tastes.registry import get_taste
from .mappings import ACTIONS, EVENTS, resolve_action


class CatpileLSPServer:
    """Full LSP server for Catpile language."""

    def __init__(self) -> None:
        self._taste = get_taste("indent")
        self._content: str = ""
        self._uri: str = ""
        self._workspace_root: Path | None = None
        # Cache for .catui element paths
        self._ui_paths: dict[str, str] = {}
        self._ui_tree: list[dict] = []

    # -- LSP protocol --------------------------------------------------------

    def _send(self, msg: dict) -> None:
        body = json.dumps(msg)
        sys.stdout.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
        sys.stdout.flush()

    def _handle_request(self, msg: dict) -> None:
        method = msg.get("method", "")
        req_id = msg.get("id")

        if method == "initialize":
            root_uri = msg.get("params", {}).get("rootUri", "")
            if root_uri:
                self._workspace_root = Path(root_uri.replace("file://", ""))
                self._load_catui_files()
            self._send({
                "id": req_id,
                "result": {
                    "capabilities": {
                        "textDocumentSync": {
                            "change": 2,  # incremental
                            "openClose": True,
                        },
                        "completionProvider": {
                            "triggerCharacters": ["."],
                            "resolveProvider": False,
                        },
                        "hoverProvider": True,
                        "documentSymbolProvider": True,
                    },
                    "serverInfo": {
                        "name": "catpile-lsp",
                        "version": "0.2.0",
                    },
                },
            })

        elif method == "textDocument/didOpen":
            self._update_doc(msg)
            self._publish_diagnostics()

        elif method == "textDocument/didChange":
            self._update_doc(msg)
            self._publish_diagnostics()

        elif method == "textDocument/didSave":
            self._update_doc(msg)
            # Reload .catui files on save (user may have updated them)
            self._load_catui_files()

        elif method == "workspace/didChangeWatchedFiles":
            self._load_catui_files()

        elif method == "textDocument/completion":
            self._handle_completion(req_id, msg)

        elif method == "textDocument/hover":
            self._handle_hover(req_id, msg)

        elif method == "textDocument/documentSymbol":
            self._handle_symbols(req_id)

        elif method == "shutdown":
            self._send({"id": req_id, "result": None})
            sys.exit(0)

        elif method == "exit":
            sys.exit(0)

    def _update_doc(self, msg: dict) -> None:
        params = msg.get("params", {})
        doc = params.get("textDocument", {})
        self._uri = doc.get("uri", "")
        if "text" in doc:
            self._content = doc["text"]
        elif "contentChanges" in params:
            changes = params["contentChanges"]
            if changes:
                # Full sync: replace entire content
                self._content = changes[-1].get("text", self._content)

    # -- .catui file loading ------------------------------------------------

    def _load_catui_files(self) -> None:
        """Scan workspace for .catui files and load element paths."""
        if not self._workspace_root:
            return
        self._ui_paths.clear()
        self._ui_tree.clear()
        for f in self._workspace_root.rglob("*.catui"):
            try:
                data = json.loads(f.read_text())
                paths = data.get("paths", {})
                self._ui_paths.update(paths)
                tree = data.get("tree", [])
                self._ui_tree.extend(tree)
            except (json.JSONDecodeError, OSError):
                pass

    # -- Diagnostics ---------------------------------------------------------

    def _publish_diagnostics(self) -> None:
        """Parse current content and publish errors as diagnostics."""
        diags = []
        try:
            prog = self._taste.compile(self._content)
            # No errors
        except SyntaxError as e:
            diags.append({
                "range": {
                    "start": {"line": max(0, e.lineno - 1), "character": 0},
                    "end": {"line": max(0, e.lineno - 1), "character": 999},
                },
                "severity": 1,
                "message": str(e),
                "source": "catpile",
            })
        except Exception as e:
            diags.append({
                "range": {"start": {"line": 0, "character": 0},
                          "end": {"line": 0, "character": 999}},
                "severity": 1,
                "message": str(e),
                "source": "catpile",
            })
        self._send({
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": self._uri, "diagnostics": diags},
        })

    # -- Completion ----------------------------------------------------------

    def _handle_completion(self, req_id: int | None, msg: dict) -> None:
        """Return completions: actions, events, UI paths."""
        params = msg.get("params", {})
        context = params.get("context", {})
        pos = params.get("position", {})
        line_num = pos.get("line", 0)
        char = pos.get("character", 0)

        items: list[dict] = []

        lines = self._content.split("\n")
        current_line = lines[line_num] if line_num < len(lines) else ""
        word_before = current_line[:char].split()[-1] if current_line[:char].strip() else ""

        # Trigger on "." → show UI element paths
        if word_before.endswith(".") or word_before == "" and char > 0 and current_line[char-1:char] == ".":
            prefix = current_line[:char].rstrip(".")
            # Find matching paths from .catui
            for path, gid in sorted(self._ui_paths.items()):
                path_lower = path.lower()
                prefix_lower = prefix.lower()
                if path_lower.startswith(prefix_lower):
                    remainder = path[len(prefix):].lstrip(".")
                    if remainder and "." not in remainder:
                        items.append({
                            "label": remainder,
                            "kind": 6,  # Variable
                            "detail": f"→ {gid}",
                            "insertText": remainder,
                        })
            self._send({
                "id": req_id,
                "result": {"isIncomplete": False, "items": items},
            })
            return

        # Always provide action completions (filtered by what user typed)
        typed = word_before.lower() if word_before else ""
        for name in sorted(ACTIONS):
            if typed and not name.lower().startswith(typed):
                continue
            schema = ACTIONS[name]
            items.append({
                "label": name.lower(),
                "kind": 3,
                "detail": f"id={schema['id']}",
                "insertText": name.lower() + "(${1})",
                "insertTextFormat": 2,
            })

        # Event completions (filtered)
        for name in sorted(EVENTS):
            label = f"on {name.lower()}"
            if typed and not label.startswith(typed) and not name.lower().startswith(typed):
                continue
            items.append({
                "label": label,
                "kind": 12,
                "detail": f"event id={EVENTS[name]['id']}",
                "insertText": f"on {name.lower()}:",
            })

        # UI path completions (start typing "Page" to see elements)
        if self._ui_paths:
            for path, gid in sorted(self._ui_paths.items()):
                # Only show top-level paths on empty trigger
                parts = path.split(".")
                if len(parts) <= 2:
                    items.append({
                        "label": path,
                        "kind": 6,
                        "detail": f"→ {gid}",
                        "insertText": path,
                    })

        # Control flow snippets
        snippets = [
            ("if", "if ${1:cond}(${2:args}):\n\t$3\nelse:\n\t$4", "If-else"),
            ("repeat", "repeat(${1:n}):\n\t$2", "Repeat"),
            ("foreach", "foreach(${1:table}):\n\t$2", "For each"),
            ("fn", "fn ${1:name}(${2:params}):\n\t$3", "Function"),
        ]
        for label, insert, desc in snippets:
            items.append({
                "label": label,
                "kind": 15,
                "detail": desc,
                "insertText": insert,
                "insertTextFormat": 2,
            })

        self._send({
            "id": req_id,
            "result": {"isIncomplete": False, "items": items},
        })

    # -- Hover ---------------------------------------------------------------

    def _handle_hover(self, req_id: int | None, msg: dict) -> None:
        """Show action/event details on hover."""
        params = msg.get("params", {})
        pos = params.get("position", {})
        line_num = pos.get("line", 0)

        lines = self._content.split("\n")
        if line_num >= len(lines):
            self._send({"id": req_id, "result": None})
            return

        line = lines[line_num]
        # Extract word at cursor
        char = pos.get("character", 0)
        start = char
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1
        end = char
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1
        word = line[start:end]

        if not word:
            self._send({"id": req_id, "result": None})
            return

        # Check actions
        name = word.lower()
        try:
            canonical = resolve_action(name)
            schema = ACTIONS[canonical]
            text_lines = [
                f"**{canonical}** (id: {schema['id']})",
                "",
                "```",
                " ".join(str(s) if isinstance(s, str) else f"{{{s.get('t','?')}}}"
                        for s in schema.get("text", [])),
                "```",
            ]
            self._send({
                "id": req_id,
                "result": {
                    "contents": {"kind": "markdown", "value": "\n".join(text_lines)},
                },
            })
            return
        except (KeyError, ValueError):
            pass

        # Check events
        if name.startswith("on "):
            ev_name = name[3:]
        else:
            ev_name = name
        for en in EVENTS:
            if en.lower() == ev_name:
                schema = EVENTS[en]
                self._send({
                    "id": req_id,
                    "result": {
                        "contents": {
                            "kind": "markdown",
                            "value": f"**{en}** (event id: {schema['id']})",
                        },
                    },
                })
                return

        # Check UI paths
        if "." in word:
            gid = self._ui_paths.get(word)
            if gid:
                self._send({
                    "id": req_id,
                    "result": {
                        "contents": {
                            "kind": "markdown",
                            "value": f"**UI Element** → globalID `{gid}`",
                        },
                    },
                })
                return

        self._send({"id": req_id, "result": None})

    # -- Document Symbols ----------------------------------------------------

    def _handle_symbols(self, req_id: int | None) -> None:
        """Provide document outline: events and functions."""
        symbols = []
        lines = self._content.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("on "):
                name = stripped.split(":")[0].strip()
                symbols.append({
                    "name": name,
                    "kind": 12,
                    "range": {
                        "start": {"line": i, "character": 0},
                        "end": {"line": i, "character": len(line)},
                    },
                    "selectionRange": {
                        "start": {"line": i, "character": 0},
                        "end": {"line": i, "character": len(line)},
                    },
                })
            elif stripped.startswith("fn "):
                name = stripped.split("(")[0].replace("fn ", "").strip()
                symbols.append({
                    "name": f"fn {name}",
                    "kind": 2,
                    "range": {
                        "start": {"line": i, "character": 0},
                        "end": {"line": i, "character": len(line)},
                    },
                    "selectionRange": {
                        "start": {"line": i, "character": 0},
                        "end": {"line": i, "character": len(line)},
                    },
                })
        self._send({"id": req_id, "result": symbols})

    # -- Main loop -----------------------------------------------------------

    def run(self) -> None:
        buffer = ""
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            buffer += line

            if "\r\n\r\n" in buffer:
                header_end = buffer.index("\r\n\r\n")
                headers_raw = buffer[:header_end]
                body_start = header_end + 4

                headers: dict[str, str] = {}
                for h in headers_raw.split("\r\n"):
                    if ":" in h:
                        k, v = h.split(":", 1)
                        headers[k.strip()] = v.strip()

                cl = int(headers.get("Content-Length", 0))
                if len(buffer) >= body_start + cl:
                    body = buffer[body_start:body_start + cl]
                    buffer = buffer[body_start + cl:]
                    if body:
                        try:
                            msg = json.loads(body)
                            self._handle_request(msg)
                        except json.JSONDecodeError:
                            pass


if __name__ == "__main__":
    CatpileLSPServer().run()
