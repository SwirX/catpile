"""Decompiler - CatWeb JSON → Catpile source code + UI hierarchy.

Two modes:
  1. Script decompilation: CatWeb script JSON → .cat source text
  2. UI decompilation: CatWeb UI JSON → element path hierarchy + globalID map

Control flow in the JSON is flat (IF_* → ELSE → END), but the .cat language
is nested (if/else with indented blocks). The decompiler reconstructs nesting
using a stack-based control flow parser.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import mappings as M

# Actions that open a control-flow block
_BLOCK_OPENERS = {
    "IF_EQ", "IF_NEQ", "IF_GT", "IF_GTE", "IF_LT", "IF_LTE",
    "IF_CONTAINS", "IF_NOT_CONTAINS", "IF_EXISTS", "IF_NOT_EXISTS",
    "IF_AND", "IF_OR", "IF_NOR", "IF_XOR",
    "IF_DARK_THEME", "IF_MOUSE_LEFT", "IF_MOUSE_MIDDLE", "IF_MOUSE_RIGHT",
    "IF_KEY_DOWN", "IF_IS_ANCESTOR", "IF_IS_CHILD", "IF_IS_DESCENDANT",
    "REPEAT", "REPEAT_FOREVER", "TABLE_ITER",
}

#: Inverse map: action schema id → action name
_ID_TO_ACTION: dict[str, str] = {}
for name, schema in M.ACTIONS.items():
    _ID_TO_ACTION[schema["id"]] = name

#: Inverse map: event schema id → event name
_ID_TO_EVENT: dict[str, str] = {}
for name, schema in M.EVENTS.items():
    _ID_TO_EVENT[schema["id"]] = name


# ---------------------------------------------------------------------------
# Script Decompiler
# ---------------------------------------------------------------------------

class DecompileError(Exception):
    pass


def decompile_event(event: dict, indent: str = "    ",
                    gid_to_path: dict[str, str] | None = None) -> str:
    """Decompile a single event block → .cat source lines."""
    eid = event.get("id", "0")
    event_name = _ID_TO_EVENT.get(eid, f"UNKNOWN_{eid}")
    # FUNC_DEF is special - it's a function, not an event
    if event_name == "FUNC_DEF":
        text = event.get("text", [])
        func_name = ""
        for slot in text:
            if isinstance(slot, dict) and "value" in slot:
                func_name = slot["value"]
                break
        overrides = event.get("variable_overrides", [])
        func_params = [
            o.get("value", f"p{i}") or f"p{i}"
            for i, o in enumerate(overrides)
        ]
        params_str = ", ".join(func_params)
        body = decompile_actions(event.get("actions", []), indent,
                                 level=1, gid_to_path=gid_to_path)
        return f"fn {func_name}({params_str}):\n{body}"

    # Regular event
    text = event.get("text", [])
    params: list[str] = []
    for slot in text:
        if isinstance(slot, dict) and "value" in slot:
            v = slot["value"]
            # Resolve globalID → page path for element-reference slots
            slot_type = slot.get("t", "")
            if slot_type == "object" and gid_to_path and isinstance(v, str) and v in gid_to_path:
                v = gid_to_path[v]
            if isinstance(v, str) and _is_valid_dotted_path(v):
                params.append(v)  # bare dotted path → ObjectRef on parse
            else:
                params.append(_escape_str(v, None))

    # Map event ID to .cat event keyword
    event_keyword = _event_id_to_keyword(eid)
    param_str = ""
    if params:
        param_str = "(" + ", ".join(params) + ")"

    body = decompile_actions(event.get("actions", []), indent,
                             level=1, gid_to_path=gid_to_path)
    return f"on {event_keyword}{param_str}:\n{body}"


def decompile_actions(actions: list[dict], indent: str = "    ",
                      level: int = 0,
                      gid_to_path: dict[str, str] | None = None) -> str:
    """Decompile flat action array → nested .cat source.

    Uses a stack to reconstruct if/else/repeat/foreach blocks from the
    flat END-terminated format that CatWeb JSON uses.
    """
    pad = indent * level
    lines: list[str] = []
    i = 0
    while i < len(actions):
        action = actions[i]
        aid = action.get("id", "")

        # END - close current block (handled by caller)
        if aid == "25":
            i += 1
            continue

        # ELSE - skipped; handled by the IF block reconstruction
        if aid == "112":
            i += 1
            continue

        action_name = _ID_TO_ACTION.get(aid, f"UNKNOWN_{aid}")
        text = action.get("text", [])
        args = _extract_values(text, aid, gid_to_path)

        if action_name == "BREAK":
            lines.append(f"{pad}break")
            i += 1
            continue

        if action_name == "RETURN":
            val = args[0] if args else ""
            lines.append(f"{pad}return {val}" if val else f"{pad}return")
            i += 1
            continue

        # Control flow openers
        if action_name in _BLOCK_OPENERS:
            if action_name == "REPEAT":
                count = args[0] if args else ""
                body_lines, skip = _collect_body(actions, i + 1)
                inner = decompile_actions(body_lines, indent, level + 1,
                                          gid_to_path)
                lines.append(f"{pad}repeat({count}):")
                lines.append(inner.rstrip("\n"))
                i = skip
                continue

            if action_name == "REPEAT_FOREVER":
                body_lines, skip = _collect_body(actions, i + 1)
                inner = decompile_actions(body_lines, indent, level + 1,
                                          gid_to_path)
                lines.append(f"{pad}repeat_forever:")
                lines.append(inner.rstrip("\n"))
                i = skip
                continue

            if action_name == "TABLE_ITER":
                table_name = args[0] if args else ""
                body_lines, skip = _collect_body(actions, i + 1)
                inner = decompile_actions(body_lines, indent, level + 1,
                                          gid_to_path)
                lines.append(f"{pad}foreach({table_name}):")
                lines.append(inner.rstrip("\n"))
                i = skip
                continue

        # IF_* condition
        if action_name.startswith("IF_"):
            cond_keyword = _condition_to_keyword(action_name)
            cond_args = ", ".join(args) if args else ""
            body_lines, else_lines, skip = _collect_if_body(actions, i + 1)
            inner = decompile_actions(body_lines, indent, level + 1,
                                      gid_to_path)
            else_inner = ""
            if else_lines is not None:
                else_inner = decompile_actions(else_lines, indent, level + 1,
                                              gid_to_path)
            if cond_args:
                lines.append(f"{pad}if {cond_keyword}({cond_args}):")
            else:
                lines.append(f"{pad}if {cond_keyword}():")
            lines.append(inner.rstrip("\n"))
            if else_inner:
                lines.append(f"{pad}else:")
                lines.append(else_inner.rstrip("\n"))
            i = skip
            continue

        # VAR_SET - format as assignment: var = value
        if action_name == "VAR_SET" and len(args) >= 2:
            # First arg is the variable name (bare string from JSON)
            # Second arg is the value (may be a string literal, number, or {var})
            var_name = _extract_raw(action["text"], 0)
            raw_val = _extract_raw(action["text"], 1)
            val = _format_var_value(raw_val)
            lines.append(f"{pad}{var_name} = {val}")
            i += 1
            continue

        # Dict literal: TABLE_CREATE → consecutive TABLE_SET → insert
        if action_name == "TABLE_CREATE":
            result = _try_emit_dict(actions, i, pad, indent, level)
            if result is not None:
                lines.extend(result)
                i = _dict_skip  # set by _try_emit_dict
                continue

        # Regular action
        action_call = _action_to_call(action_name, args)
        lines.append(f"{pad}{action_call}")
        i += 1

    return "\n".join(lines) + "\n"


def _collect_body(actions: list[dict], start: int) -> tuple[list[dict], int]:
    """Collect actions inside a control-flow block until matching END.

    Returns (body_actions, next_index) where next_index points past the END.
    Respects nested blocks (counts openers/closers).
    """
    depth = 1
    i = start
    while i < len(actions) and depth > 0:
        aid = actions[i].get("id", "")
        action_name = _ID_TO_ACTION.get(aid, "")
        if action_name in _BLOCK_OPENERS:
            depth += 1
        elif aid == "25":  # END
            depth -= 1
        i += 1

    body = actions[start:i - 1] if depth == 0 else actions[start:]
    return body, i


def _collect_if_body(actions: list[dict], start: int
                     ) -> tuple[list[dict], list[dict] | None, int]:
    """Collect an IF block body, detecting optional ELSE at depth 1.

    Returns (if_body, else_body_or_None, next_index).
    """
    depth = 1
    if_body_end = start
    else_body_start = None
    i = start
    while i < len(actions) and depth > 0:
        aid = actions[i].get("id", "")
        action_name = _ID_TO_ACTION.get(aid, "")
        if action_name in _BLOCK_OPENERS:
            depth += 1
        elif aid == "112" and depth == 1:
            # ELSE at depth 1 - split here
            if_body_end = i
            else_body_start = i + 1
        elif aid == "25":
            depth -= 1
            if depth == 0:
                # END at depth 0 - body ends here
                if else_body_start is None:
                    if_body_end = i
                break
        i += 1

    if_body = actions[start:if_body_end]
    else_body = None
    if else_body_start is not None:
        # else_body goes up to (but not including) the END at depth 0
        else_body = actions[else_body_start:i] if i > else_body_start else []
    return if_body, else_body, i + 1
    return if_body, else_body, i


def _extract_values(text: list, action_id: str = "",
                     gid_to_path: dict[str, str] | None = None) -> list[str]:
    """Extract ``value`` fields from a ``text`` array.

    Handles scalar values (string, number), tuple values (list),
    and empty slots gracefully. Uses schema to know which slots
    are variable/object slots (bare) vs string literals (quoted).
    """
    # Get output slot info from schema
    out_indices: set[int] = set()
    try:
        from catpile.schema_parser import get_schema, get_output_slots
        aid_int = int(action_id) if action_id else -1
        if aid_int >= 0:
            out_indices = set(get_output_slots(aid_int, get_schema()))
    except Exception:
        pass

    values: list[str] = []
    slot_idx = 0
    for slot in text:
        if isinstance(slot, dict) and "value" in slot:
            v = slot["value"]
            slot_label = slot.get("l", "")
            slot_type = slot.get("t", "")
            is_out = slot_idx in out_indices
            if isinstance(v, str):
                if v == "":
                    values.append('""')
                elif slot_label == "variable" or slot_type == "object" or is_out:
                    # Variable/object/output slot - bare if valid ident, else quote
                    # For object slots, resolve globalID → page path first
                    resolved = v
                    if slot_type == "object" and gid_to_path and isinstance(v, str) and v in gid_to_path:
                        resolved = gid_to_path[v]
                    sanitized = resolved.replace("!", "_").replace("-", "_")
                    if _is_valid_ident(sanitized):
                        values.append(sanitized)
                    elif _is_valid_dotted_path(sanitized):
                        # Dotted path like "Page.Button" → emit bare so the
                        # parser creates an ObjectRef for UILinker resolution
                        values.append(resolved)
                    else:
                        values.append(_escape_str(resolved, None))
                else:
                    # Non-variable, non-object, non-output slots hold
                    # plain string values - never resolve globalIDs here.
                    values.append(_escape_str(v, None))
            elif isinstance(v, list):
                inner = []
                for item in v:
                    if isinstance(item, dict) and "value" in item:
                        iv = item["value"]
                        if isinstance(iv, str):
                            iv = iv.replace("!", "_")
                            if iv.startswith("{") and iv.endswith("}") and len(iv) > 2:
                                iv = iv[1:-1]
                            inner.append(iv)
                if inner:
                    values.append(", ".join(inner))
                else:
                    values.append('""')
            elif v not in (None, ""):
                values.append(str(v))
            else:
                values.append('""')
            slot_idx += 1
    return values
    return values


def _extract_raw(text: list, idx: int) -> str:
    """Extract raw value from text slot at index *idx*, without quoting."""
    slot_idx = 0
    for slot in text:
        if isinstance(slot, dict) and "value" in slot:
            if slot_idx == idx:
                val = slot["value"]
                if isinstance(val, str):
                    return val.replace("!", "_")
                return val
            slot_idx += 1
    return ""


def _format_var_value(s: str) -> str:
    """Format a value for the right side of an assignment.

    If it's a ``{var}`` reference, output bare. If numeric, output bare.
    Otherwise, quote as a string literal.
    """
    # Sanitize CatWeb scope prefixes
    if "!" in s:
        s = s.replace("!", "_")
    if (s.startswith("{") and s.endswith("}") and len(s) > 2
            and s.count("{") == 1 and s.count("}") == 1):
        return s[1:-1].replace("!", "_").replace("-", "_")
    try:
        float(s)
        if s.lower() in ("inf", "-inf", "nan", "infinity", "-infinity"):
            raise ValueError
        # Normalize floats without leading digit: .1 -> 0.1
        if s.startswith("."):
            return f"0{s}"
        return s
    except ValueError:
        pass
    return f'"{s}"'


def _is_valid_ident(s: str) -> bool:
    """Check if *s* is a valid Catpile identifier (letter + alphanumeric/underscore)."""
    return bool(s) and s[0].isalpha() and all(c.isalnum() or c == "_" for c in s)


def _is_valid_dotted_path(s: str) -> bool:
    """Check if *s* is a dotted path like ``Page.Button``."""
    parts = s.split(".")
    return len(parts) >= 2 and all(_is_valid_ident(p) for p in parts)


def _escape_str(s: str,
                gid_to_path: dict[str, str] | None = None) -> str:
    """Escape a string value for .cat source output.

    Note: globalID resolution is handled by callers before invoking this
    function - this function only handles quoting and escaping.
    """
    # Sanitize CatWeb scope-prefixed variable names (l!foo -> l_foo)
    if "!" in s:
        s = s.replace("!", "_")
    # If it looks like a variable reference {name}, output bare
    # Only match if the ENTIRE value is {name} - not "{a}.{b}" or "text{var}"
    if (s.startswith("{") and s.endswith("}") and len(s) > 2
            and s.count("{") == 1 and s.count("}") == 1):
        inner = s[1:-1].replace("!", "_").replace("-", "_")
        # Only output bare if the result is a valid Catpile identifier
        if _is_valid_ident(inner):
            return inner
        # Otherwise quote the whole thing (e.g. {icy-tea} stays as string)
    # Scope-prefixed names are variable references, output bare
    if len(s) >= 3 and s[1] == "_" and s[0] in "log":
        return s
    # If it's purely numeric, output bare
    try:
        f = float(s)
        if s.lower() in ("inf", "-inf", "nan", "infinity", "-infinity"):
            raise ValueError  # treat these as strings
        # Normalize floats without leading digit: .1 -> 0.1
        if s.startswith("."):
            return f"0{s}"
        return s
    except ValueError:
        pass
    # Everything else gets quoted
    escaped = s.replace("\\", "\\\\").replace("\"", "\\\"")
    return f'"{escaped}"'


# Dict detection state (set by _try_emit_dict)
_dict_skip: int = 0


def _try_emit_dict(actions: list[dict], i: int, pad: str,
                   indent: str, level: int) -> list[str] | None:
    """Decompile TABLE_CREATE + consecutive TABLE_SET as dict literal."""
    global _dict_skip
    create_text = actions[i].get("text", [])
    table_name = _extract_raw(create_text, 0)

    entries: list[tuple[str, str, str]] = []
    j = i + 1
    while j < len(actions):
        aj = actions[j]
        ajid = aj.get("id", "")
        ajname = _ID_TO_ACTION.get(ajid, "")
        if ajname != "TABLE_SET":
            break
        ajtext = aj.get("text", [])
        key = _extract_raw(ajtext, 0)
        tbl = _extract_raw(ajtext, 1)
        val_raw = _extract_raw(ajtext, 2)
        if tbl != table_name:
            break
        entries.append((key, val_raw, _format_var_value(val_raw)))
        j += 1

    if not entries:
        return None

    # Check for parent insert
    parent_insert = None
    if j < len(actions):
        aj = actions[j]
        ajname = _ID_TO_ACTION.get(aj.get("id", ""), "")
        ajtext = aj.get("text", [])
        if ajname == "TABLE_SET":
            key = _extract_raw(ajtext, 0)
            tbl = _extract_raw(ajtext, 1)
            val_raw = _extract_raw(ajtext, 2)
            if key == table_name and tbl != table_name:
                if val_raw in ("{" + table_name + "}", table_name):
                    parent_insert = tbl
                    j += 1

    safe_name = table_name.replace("-", "_")
    kv = [f"{_format_var_value(k)}: {v}" for k, _, v in entries]
    lines = [f"{pad}{safe_name} = {{{', '.join(kv)}}}"]

    if parent_insert:
        lines.append(f"{pad}table_set(\"{table_name}\", \"{parent_insert}\", {safe_name})")

    _dict_skip = j
    return lines


def _event_id_to_keyword(eid: str) -> str:
    """Map schema event ID to .cat event keyword."""
    event_name = _ID_TO_EVENT.get(eid, f"EVENT_{eid}")
    return event_name.lower().replace("_", "_")


def _condition_to_keyword(action_name: str) -> str:
    """Map IF_* action name to condition keyword."""
    suffix = action_name[3:]  # Strip "IF_"
    return suffix.lower()


def _action_to_call(action_name: str, args: list[str]) -> str:
    """Format an action call as .cat source.

    Uses CatWeb schema to know which args are output variables (marked with ``→``).
    Actions with output vars use assignment syntax:
    ``l_fen = input_get_text("element")`` instead of ``input_get_text("element", l_fen)``.
    """
    alias = action_name.lower()
    if not args:
        return f"{alias}()"

    # Determine output slots from schema
    out_indices: set[int] = set()
    try:
        from catpile.schema_parser import get_schema, get_output_slots
        aid = _NAME_TO_ID.get(action_name, -1)
        if aid >= 0:
            out_indices = set(get_output_slots(aid, get_schema()))
    except Exception:
        pass

    if out_indices:
        # Schema-based: split args into input and output groups
        # Filter out empty output vars (e.g. optional variables with no value)
        output_vars = [
            args[i] for i in sorted(out_indices)
            if i < len(args) and args[i] not in ('""', "''")
        ]
        # Collect input args (all non-output slots), filter empties
        input_args = [
            a for i, a in enumerate(args)
            if i not in out_indices and a not in ('""', "''")
        ]
        if output_vars:
            out_str = ", ".join(output_vars)
            in_str = ", ".join(input_args) if input_args else ""
            if in_str:
                return f"{out_str} = {alias}({in_str})"
            else:
                return f"{out_str} = {alias}()"
        # Output slots exist but all empty - emit without them
        if input_args:
            return f"{alias}({', '.join(input_args)})"
        return f"{alias}()"

    # Fallback: no schema or no outputs → plain call
    # Filter out empty quoted strings for cleaner output
    clean_args = [a for a in args if a not in ('""', "''")]
    return f"{alias}({', '.join(clean_args)})"


# Build: action name → id (for schema lookup)
_NAME_TO_ID: dict[str, int] = {}
for _aid_str, _aname in _ID_TO_ACTION.items():
    _NAME_TO_ID[_aname] = int(_aid_str)


def decompile_script(script: dict,
                     gid_to_path: dict[str, str] | None = None) -> str:
    """Decompile a single CatWeb script object → .cat source code.

    Args:
        script: A CatWeb script dict with ``content`` → event blocks.
        gid_to_path: Optional map of globalID → page path for path resolution.

    Returns:
        Catpile .cat source code as a string.
    """
    alias = script.get("alias", "")
    events = script.get("content", [])
    indent = "    "

    parts: list[str] = []
    if alias:
        parts.append(f'script "{alias}":')

    for ev in events:
        decompiled = decompile_event(ev, indent, gid_to_path)
        if alias:
            # Indent each event line under the script block
            indented = "\n".join(indent + line if line.strip() else line
                                for line in decompiled.split("\n"))
            parts.append(indented)
        else:
            parts.append(decompiled)

    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# UI Decompiler - Element Path Hierarchy
# ---------------------------------------------------------------------------

def decompile_ui(ui_list: list[dict]) -> dict:
    """Decompile a CatWeb UI JSON array into a path hierarchy.

    Filters out ``script`` class objects (those go to the script decompiler).
    Builds a tree with path-based access:

        Page.header → globalid "headerFrame"
        Page.header.title → globalid "titleLabel"

    Returns a dict with:
        ``ui``: Original UI JSON (preserved for re-compilation)
        ``paths``: Dict mapping element paths to their globalIDs
        ``tree``: Nested hierarchy tree
    """
    # Filter out script elements (top level AND nested)
    ui_elements = _strip_scripts(ui_list)

    paths: dict[str, str] = {}
    tree = _build_tree(ui_elements, paths)

    return {
        "ui": ui_elements,
        "paths": paths,
        "tree": tree,
    }


def _build_tree(elements: list[dict],
                paths: dict[str, str],
                prefix: str = "Page",
                _class_counts: dict[str, int] | None = None) -> list[dict]:
    """Recursively build element tree and populate path → globalID map.

    Skips ``class: script`` elements (handled separately).
    Elements without an explicit ``alias`` or ``name`` get a class-based
    name with an index (e.g. ``Frame_1``, ``TextButton_2``).
    """
    if _class_counts is None:
        _class_counts = {}
    nodes: list[dict] = []
    for el in elements:
        if el.get("class") == "script":
            continue
        gid = el.get("globalid", "")
        cls = el.get("class", "Frame")

        # Use alias or name; fall back to <class>_<index>
        name = el.get("alias") or el.get("name")
        if not name:
            _class_counts[cls] = _class_counts.get(cls, 0) + 1
            name = f"{cls}_{_class_counts[cls]}"

        # Handle duplicate aliases - append counter
        base_path = f"{prefix}.{name}" if prefix else name
        path = base_path
        counter = 1
        while path in paths:
            counter += 1
            path = f"{base_path}_{counter}"

        paths[path] = gid

        node = {
            "name": name,
            "globalid": gid,
            "class": cls,
        }

        children = el.get("children", [])
        if children:
            node["children"] = _build_tree(children, paths, path,
                                           _class_counts)

        nodes.append(node)

    return nodes


# ---------------------------------------------------------------------------
# Page Decompiler - Full Round-Trip
# ---------------------------------------------------------------------------

def _collect_scripts(elements: list[dict]) -> list[dict]:
    """Recursively find all ``class: script`` elements in a tree.

    Scripts can be nested inside UI elements (as children of Frames, etc.)
    or at the top level. This walks the entire tree.
    """
    found: list[dict] = []
    for el in elements:
        if el.get("class") == "script":
            found.append(el)
        # Recurse into children regardless of type
        children = el.get("children", [])
        if children:
            found.extend(_collect_scripts(children))
    return found


def _strip_scripts(elements: list[dict]) -> list[dict]:
    """Return a copy of the element tree with scripts replaced by markers.

    Script markers preserve the original position and nesting in the page,
    so the builder can reconstruct the exact original structure.
    """
    result: list[dict] = []
    for el in elements:
        if el.get("class") == "script":
            marker: dict[str, Any] = {"class": "script"}
            alias = el.get("alias", "")
            if alias:
                marker["alias"] = alias
            if "globalid" in el:
                marker["globalid"] = el["globalid"]
            if "enabled" in el:
                marker["enabled"] = el["enabled"]
            children = el.get("children", [])
            if children:
                marker["children"] = _strip_scripts(children)
            result.append(marker)
            continue
        el_copy = dict(el)
        children = el_copy.get("children", [])
        if children:
            el_copy["children"] = _strip_scripts(children)
        result.append(el_copy)
    return result


def decompile_page(page_input: list[dict] | dict, output_stem: str = "page"
                   ) -> dict[str, str]:
    """Decompile a full CatWeb page export.

    Accepts either a list (CatWeb ``webcontent`` array) or a dict
    (full page export with ``webcontent`` key plus optional metadata
    like ``background``). Separates scripts from UI elements,
    decompiles both, and returns a dict of output files:

        ``{alias}.cat``: Decompiled script source (one per script)
        ``{stem}.catui``: UI hierarchy with path mappings (JSON)
        ``.catpilerc``: Project config for recompilation with ``cpile build``

    Args:
        page_input: Full CatWeb page export (list or dict with webcontent).
        output_stem: Base filename stem (default: "page").

    Returns:
        Dict mapping output filenames to their content strings.
    """
    # Handle dict wrapper: {"background": "...", "webcontent": [...]}
    metadata: dict[str, Any] = {}
    if isinstance(page_input, dict):
        metadata = {k: v for k, v in page_input.items() if k != "webcontent"}
        page_json = page_input.get("webcontent", [])
        if not isinstance(page_json, list):
            page_json = [page_json]
    else:
        page_json = page_input

    # Recursively find all scripts (including nested)
    scripts = _collect_scripts(page_json)

    # Decompile scripts - one .cat per script
    outputs: dict[str, str] = {}

    # Build reverse path map: global ID → page.Element.path
    ui_result = decompile_ui(page_json)
    gid_to_path = {
        gid: path for path, gid in ui_result.get("paths", {}).items()
    }

    cat_names: list[str] = []
    for i, script in enumerate(scripts):
        alias = script.get("alias", f"s{i}")
        cat_name = f"{alias}.cat" if script.get("alias") else f"{output_stem}_s{i}.cat"
        outputs[cat_name] = decompile_script(script, gid_to_path)
        cat_names.append(cat_name)

    if metadata:
        ui_result["metadata"] = metadata

    # UI hierarchy (used by the builder to reconstruct the full page)
    outputs[f"{output_stem}.catui"] = json.dumps(ui_result, indent=2)

    # Generate .catpilerc project config
    # (cat_names preserves original document order from _collect_scripts)
    catpilerc: dict[str, Any] = {
        "project": output_stem,
        "taste": "indent",
        "default_scope": "local",
        "pages": [
            {
                "name": output_stem,
                "ui": f"{output_stem}.catui",
                "scripts": cat_names,
                "output": f"build/{output_stem}.json",
            }
        ],
    }
    outputs[".catpilerc"] = json.dumps(catpilerc, indent=2)

    return outputs


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def main():
    """CLI entry point: cpile --decompile input.json -o output-dir/"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: cpile --decompile input.json")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    data = json.loads(input_path.read_text())
    if not isinstance(data, list):
        data = [data]

    stem = input_path.stem
    outputs = decompile_page(data, stem)

    out_dir = input_path.parent
    for name, content in outputs.items():
        out_path = out_dir / name
        out_path.write_text(content)
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
