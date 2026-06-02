"""Schema loader and action/event mapping helpers for CatWeb JSON."""

import json
import random
import string
from pathlib import Path

_HERE = Path(__file__).parent
_SCHEMA_PATH = _HERE / "schema.json"

with open(_SCHEMA_PATH) as _f:
    _raw = json.load(_f)

#: Dict[str, dict] - action name -> {id, text, ...}
ACTIONS: dict[str, dict] = _raw["actions"]

#: Dict[str, dict] - event name -> {id, text, params, ...}
EVENTS: dict[str, dict] = _raw["events"]

# Build alias map: lowercase name → canonical name
_ACTION_ALIASES: dict[str, str] = {}
for name in ACTIONS:
    _ACTION_ALIASES[name.lower()] = name
# Add common shorthand aliases
_ACTION_ALIASES.update({
    "log": "LOG",
    "warn": "WARN",
    "error": "ERROR",
    "wait": "WAIT",
    "set": "VAR_SET",
    "inc": "VAR_INC",
    "dec": "VAR_DEC",
    "mul": "VAR_MUL",
    "div": "VAR_DIV",
    "pow": "VAR_POW",
    "mod": "VAR_MOD",
    "round": "VAR_ROUND",
    "floor": "VAR_FLOOR",
    "ceil": "VAR_CEIL",
    "random": "VAR_RANDOM",
    "redirect": "NAV_REDIRECT",
    "hide": "LOOK_HIDE",
    "show": "LOOK_SHOW",
    "settext": "LOOK_SET_TEXT",
    "setprop": "LOOK_SET_PROP",
    "getprop": "LOOK_GET_PROP",
    "play": "AUDIO_PLAY",
    # Condition aliases (for decompiled IF statements)
    "eq": "IF_EQ", "neq": "IF_NEQ", "gt": "IF_GT", "lt": "IF_LT",
    "gte": "IF_GTE", "lte": "IF_LTE",
    "and": "IF_AND", "or": "IF_OR", "nor": "IF_NOR", "xor": "IF_XOR",
    "exists": "IF_EXISTS", "not_exists": "IF_NOT_EXISTS",
    "contains": "IF_CONTAINS", "not_contains": "IF_NOT_CONTAINS",
    "if_lmb_down": "IF_LMB_DOWN", "if_mmb_down": "IF_MMB_DOWN",
    "if_rmb_down": "IF_RMB_DOWN", "if_key_down": "IF_KEY_DOWN",
    "stop": "AUDIO_STOP",
    "pause": "AUDIO_PAUSE",
    "resume": "AUDIO_RESUME",
    "broadcast": "NET_BROADCAST_PAGE",
    "repeat": "REPEAT",
    "break": "BREAK",
    "end": "END",
    "else": "ELSE",
    "return": "RETURN",
    "runFunction": "FUNC_RUN",
    "run_function": "FUNC_RUN",
    "runfunction": "FUNC_RUN",
    "func_run": "FUNC_RUN",
    "run": "FUNC_RUN",
    "getCursor": "INPUT_GET_CURSOR",
    "getcursor": "INPUT_GET_CURSOR",
    "getViewport": "INPUT_GET_VIEWPORT",
    "getviewport": "INPUT_GET_VIEWPORT",
    "getUsername": "USER_GET_NAME",
    "getusername": "USER_GET_NAME",
    "getDisplayName": "USER_GET_DISPLAY",
    "getUserId": "USER_GET_ID",
    "getUrl": "NAV_GET_URL",
    "geturl": "NAV_GET_URL",
    "getQueryParam": "NAV_GET_QUERY",
    "getqueryparam": "NAV_GET_QUERY",
    "getCookie": "COOKIE_GET",
    "getcookie": "COOKIE_GET",
    "getentry": "TABLE_GET",
    "create_table": "TABLE_CREATE",
    "createtable": "TABLE_CREATE",
    "createTable": "TABLE_CREATE",
    "set_entry": "TABLE_SET",
    "setentry": "TABLE_SET",
    "setentryobj": "TABLE_SET_OBJ",
    "get_entry": "TABLE_GET",
    "getentry": "TABLE_GET",
    "delete_entry": "TABLE_DEL",
    "deleteentry": "TABLE_DEL",
    "table_len": "TABLE_LEN",
    "table_insert": "TABLE_INSERT",
    "table_remove": "TABLE_REMOVE",
    "table_join": "TABLE_JOIN",
    "foreach_table": "TABLE_ITER",
    "iteratetable": "TABLE_ITER",
})

# Event aliases
_EVENT_ALIASES: dict[str, str] = {}
for name in EVENTS:
    _EVENT_ALIASES[name.lower()] = name
_EVENT_ALIASES.update({
    "loaded": "LOADED",
    "pressed": "PRESSED",
    "key_pressed": "KEY_PRESSED",
    "mouse_enter": "MOUSE_ENTER",
    "mouse_leave": "MOUSE_LEAVE",
    "message_received": "MSG_RECEIVED",
    "changed": "CHANGED",
    "function": "FUNC_DEF",
    "func_def": "FUNC_DEF",
})


def resolve_action(name: str) -> str:
    """Resolve a user-facing action name to the canonical schema name.

    Supports lowercase, aliases, and direct access.
    """
    # Try direct access first (fast path)
    if name in ACTIONS:
        return name
    # Try lowercase alias map
    canonical = _ACTION_ALIASES.get(name.lower())
    if canonical is not None:
        return canonical
    raise KeyError(f"Unknown action {name!r}")


def resolve_event(name: str) -> str:
    """Resolve a user-facing event name to the canonical schema name."""
    if name in EVENTS:
        return name
    canonical = _EVENT_ALIASES.get(name.lower())
    if canonical is not None:
        return canonical
    raise KeyError(f"Unknown event {name!r}")



# ---------------------------------------------------------------------------
# Global ID generator
# ---------------------------------------------------------------------------

class IDGen:
    """Generates unique short IDs for CatWeb elements."""

    def __init__(self, length: int = 4) -> None:
        self._used: set[str] = set()
        self._chars = string.ascii_letters + string.digits + "!@#$%^&*"
        self._length = length

    def next(self) -> str:
        while True:
            gid = "".join(random.choices(self._chars, k=self._length))
            if gid not in self._used:
                self._used.add(gid)
                return gid

# ---------------------------------------------------------------------------
# Script / Event / Action builders
# ---------------------------------------------------------------------------

def make_script(alias: str | None = None) -> dict:
    """Return a CatWeb script dict.

    Scripts require ``globalid`` and ``enabled`` fields. ``alias`` is
    optional - only included when set.
    """
    gid = "".join(random.choices(
        string.ascii_letters + string.digits + "!@#$%^&*", k=4))
    result = {
        "class": "script",
        "globalid": gid,
        "content": [],
        "enabled": "true",
    }
    if alias:
        result["alias"] = alias
    return result


def make_event(event_name: str, idgen: IDGen | None = None,
               x: int = 0, y: int = 0, width: str = "350",
               clean: bool = False) -> dict:
    """Build a CatWeb event block dict from *event_name* (supports aliases)."""
    canonical = resolve_event(event_name)
    schema = EVENTS.get(canonical)
    if schema is None:
        raise KeyError(f"Unknown event type {event_name!r}. "
                       f"Known: {', '.join(sorted(EVENTS))}")

    gid = (idgen or IDGen()).next()
    text: list = []
    for slot in schema["text"]:
        if isinstance(slot, str):
            text.append(slot)
        else:
            text.append(dict(slot))  # shallow-copy slot template

    if clean:
        for slot in text:
            if isinstance(slot, dict) and "value" in slot and "l" in slot:
                slot["l"] = slot["value"]
    result = {
        "id": schema["id"],
        "text": text,
        "x": str(x),
        "y": str(y),
        "width": width,
        "globalid": gid,
        "actions": [],
    }
    return result


def make_action(action_name: str, *values,
                clean: bool = True,
                idgen: IDGen | None = None) -> dict:
    """Build a single CatWeb action dict.

    *values* fill the parameter slots (``{t: …}`` dicts) in order.
    For slots with ``t="tuple"``, the value should be a list of
    ``{value, t, l}`` param objects (the tuple's argument array).
    Pass ``None`` for a slot to leave it empty (unfilled parameter).
    *action_name* supports aliases (e.g. ``log`` → ``LOG``).

    When *clean* is True (default), the ``value`` of each parameter slot
    is copied into its ``l`` label field. This preserves the original
    variable name in the label even if Roblox tags the value field.
    Pass ``clean=False`` to keep schema-default labels.
    Tuple slot values (lists) are skipped during clean.
    """
    canonical = resolve_action(action_name)
    schema = ACTIONS.get(canonical)
    if schema is None:
        raise KeyError(f"Unknown action {action_name!r}. "
                       f"Known: {', '.join(sorted(ACTIONS))}")

    gid = (idgen or IDGen()).next()
    text: list = []
    val_iter = iter(values)

    for slot in schema["text"]:
        if isinstance(slot, str):
            text.append(slot)
        else:
            param = dict(slot)
            try:
                v = next(val_iter)
            except StopIteration:
                v = None
            if v is not None:
                if isinstance(v, list) and param.get("t") == "tuple":
                    param["value"] = v
                else:
                    # Strip {} braces for variable/object slots - they expect bare names.
                    # Slot types: t="object" or l="variable" mean bare name, not {var}.
                    if (isinstance(v, str) and v.startswith("{") and v.endswith("}")
                            and (param.get("t") == "object"
                                 or param.get("l") == "variable")):
                        v = v[1:-1]
                    param["value"] = v
            text.append(param)

    result = {"id": schema["id"], "text": text, "globalid": gid}
    if clean:
        for slot in text:
            if isinstance(slot, dict) and "value" in slot and "l" in slot:
                if isinstance(slot["value"], list):
                    continue  # tuple values are arrays, skip clean
                slot["l"] = slot["value"]
    return result
