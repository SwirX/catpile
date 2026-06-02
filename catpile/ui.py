"""UI element linker - resolves element names to CatWeb globalIDs.

CatWeb UI elements are defined in JSON with ``globalid`` fields.
Scripts reference these elements by name. This module:

  1. Parses CatWeb UI JSON files to build a name → globalID index
  2. Scans compiled IR for element name references
  3. Resolves names to their actual globalID values

Usage::

    linker = UILinker("page.json")
    linker.link(program)
    # Now all \"myButton\" references in the IR resolve to the globalID
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ir import (
    Program, ScriptDef, EventDef, FunctionDef,
    ActionStmt, IfStmt, RepeatStmt, ForEachStmt, BreakStmt, ReturnStmt,
    VarRef, StrLit, NumLit, ObjectRef, InterpolatedStr, MathExpr,
    DictLiteral, ListLiteral, KVPair,
    Arg, Stmt,
)


class UILinkError(Exception):
    pass


def _walk_ui(elements: list[dict], index: dict[str, str],
             prefix: str = "") -> None:
    """Recursively walk CatWeb UI elements, building name → globalid index."""
    for el in elements:
        gid = el.get("globalid", "")
        if not gid:
            continue

        # Index by globalid
        index[gid] = gid

        # Index by explicit 'name' field if present
        name = el.get("name", "")
        if name:
            if name in index and index[name] != gid:
                raise UILinkError(
                    f"Duplicate element name {name!r}: "
                    f"maps to both {index[name]!r} and {gid!r}"
                )
            index[name] = gid

        # Index by flattened path
        path = f"{prefix}/{gid}" if prefix else gid
        if path != gid:
            index[path] = gid

        children = el.get("children")
        if children:
            _walk_ui(children, index, path)


def load_ui(path: str | Path) -> tuple[dict[str, str], dict[str, str]]:
    """Load a CatWeb UI file and build name → globalID index and path → globalID map.

    Accepts raw CatWeb UI arrays and .catui format (dict with ``ui`` key and
    optional ``paths`` dict mapping dotted paths like ``Page.Button`` to globalIDs).

    Returns a ``(index, paths)`` tuple where:
      * *index* maps element names/aliases → globalID
      * *paths* maps .catui dotted paths → globalID (may be empty)
    """
    raw = json.loads(Path(path).read_text())
    paths: dict[str, str] = {}

    # Handle .catui format: {"ui": [...], "paths": {...}, "tree": [...]}
    if isinstance(raw, dict):
        paths = raw.get("paths", {})
        raw = raw.get("ui", [raw])
    if not isinstance(raw, list):
        raw = [raw]

    index: dict[str, str] = {}
    _walk_ui(raw, index)
    # Merge paths into the index so dotted-path lookups work directly
    index.update(paths)
    return index, paths


class UILinker:
    """Links element name references in IR to their UI globalIDs.

    After linking, references like ``hide(myButton)`` are resolved to
    the actual globalID from the UI definition file.

    Accepts either an index dict directly (from CatUI AST) or a path to a
    ``.catui`` JSON file (backward compat). Use ``from_file()`` for explicit
    file-based construction.
    """

    def __init__(self, source: dict[str, str] | str | Path) -> None:
        if isinstance(source, (str, Path)):
            self._index, self._paths = load_ui(source)
            self._index.update(self._paths)
        else:
            self._index = source
        self._resolved: int = 0

    @classmethod
    def from_file(cls, ui_path: str | Path) -> UILinker:
        """Construct a UILinker from a .catui JSON file path."""
        return cls(ui_path)

    def link(self, program: Program) -> int:
        """Walk the program IR and resolve element name references.

        Scans all action arguments that look like element references
        (bare strings in object slots) and replaces them with the
        corresponding globalID from the UI index.

        Also resolves event params (e.g. ``on pressed(Page.myBtn)``)
        to their globalIDs.

        Returns count of resolved references.
        """
        self._resolved = 0

        for script in program.scripts:
            for kind, _, owner in self._iter_script_items(script):
                self._link_stmts(owner.body)
                if isinstance(owner, EventDef):
                    self._link_event_params(owner)

        return self._resolved

    def _link_event_params(self, event: EventDef) -> None:
        """Resolve dotted-path event params to globalIDs."""
        new_params: list[str] = []
        for p in event.params:
            gid = self._index.get(p)
            if gid is not None and gid != p:
                new_params.append(gid)
                self._resolved += 1
            else:
                new_params.append(p)
        event.params = new_params

    @staticmethod
    def _iter_script_items(script: ScriptDef):
        for i, e in enumerate(script.events):
            yield "event", i, e
        for i, f in enumerate(script.functions):
            yield "fn", i, f

    def _link_stmts(self, stmts: list[Stmt]) -> None:
        for stmt in stmts:
            if isinstance(stmt, ActionStmt):
                self._link_action(stmt)
            elif isinstance(stmt, IfStmt):
                self._link_stmts(stmt.body)
                if stmt.else_body:
                    self._link_stmts(stmt.else_body)
            elif isinstance(stmt, RepeatStmt):
                self._link_stmts(stmt.body)
            elif isinstance(stmt, ForEachStmt):
                self._link_stmts(stmt.body)

    def _link_action(self, stmt: ActionStmt) -> None:
        new_args: list[Arg] = []
        for arg in stmt.args:
            resolved = self._resolve_arg(arg)
            if resolved is not arg:
                self._resolved += 1
            new_args.append(resolved)
        stmt.args = new_args

    def _resolve_arg(self, arg: Arg) -> Arg:
        """Resolve an element name reference in an argument."""
        if isinstance(arg, ObjectRef):
            # Dotted path like "page.Button" → resolve to global ID
            gid = self._index.get(arg.name)
            if gid is not None:
                return StrLit(gid)
            return arg
        if isinstance(arg, StrLit):
            gid = self._index.get(arg.value)
            if gid is not None and gid != arg.value:
                return StrLit(gid)
            return arg
        # Also resolve bare identifiers that match element aliases
        if isinstance(arg, VarRef):
            gid = self._index.get(arg.name)
            if gid is not None:
                return StrLit(gid)
            return arg
        if isinstance(arg, InterpolatedStr):
            new_parts = []
            changed = False
            for p in arg.parts:
                if isinstance(p, StrLit):
                    gid = self._index.get(p.value)
                    if gid is not None and gid != p.value:
                        new_parts.append(StrLit(gid))
                        changed = True
                    else:
                        new_parts.append(p)
                else:
                    new_parts.append(p)
            if changed:
                return InterpolatedStr(new_parts)
            return arg
        if isinstance(arg, DictLiteral):
            new_entries = []
            changed = False
            for kv in arg.entries:
                k = self._resolve_arg(kv.key)
                v = self._resolve_arg(kv.value)
                if k is not kv.key or v is not kv.value:
                    changed = True
                new_entries.append(KVPair(k, v))
            if changed:
                return DictLiteral(new_entries)
            return arg
        if isinstance(arg, ListLiteral):
            new_items = []
            changed = False
            for item in arg.items:
                resolved = self._resolve_arg(item)
                if resolved is not item:
                    changed = True
                new_items.append(resolved)
            if changed:
                return ListLiteral(new_items)
            return arg
        return arg

    def report(self) -> str:
        return f"UI linker: resolved {self._resolved} element reference(s)"
