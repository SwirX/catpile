"""CatWeb schema parser - extracts slot types and output variable positions.

Parses CatWeb schema markdown (from quitism/catlua) to build maps for:
- Which action slots are output variables (marked with ``→``)
- Slot types (string, number, object, any, variable) for proper {} wrapping
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple
from urllib.request import urlopen


# ---------------------------------------------------------------------------
# Parsed slot info
# ---------------------------------------------------------------------------

class SlotInfo(NamedTuple):
    """Metadata for one action/event text slot."""
    name: str          # e.g. "value", "element", "variable"
    slot_type: str     # "string", "number", "object", "any", "variable"
    optional: bool     # True if slot is marked with ? 
    is_output: bool    # True if this slot is an output (follows →)


# ---------------------------------------------------------------------------
# Schema format
# ---------------------------------------------------------------------------
# ## ACTION_NAME (`id: N`)
# `Human description {name:type} {name:type} → {output:type}`

_SCHEMA_URL = (
    "https://raw.githubusercontent.com/quitism/catlua/main/docs/schema.md"
)

# Regex: {name:type} or {name?:type}
_SLOT_RE = re.compile(r"\{(\w+)(\??):(\w+)\}")


def parse_slots(raw: str) -> list[SlotInfo]:
    """Parse slot specs from a schema action line.

    ``"Get entry {entry:string} of {table:string} → {variable:string}"``
    → three slots, the last being an output.
    """
    slots: list[SlotInfo] = []
    saw_arrow = False
    for m in _SLOT_RE.finditer(raw):
        name = m.group(1)
        optional = m.group(2) == "?"
        slot_type = m.group(3)
        # Check if → appears before this slot
        start = m.start()
        before = raw[:start]
        if "→" in before:
            saw_arrow = True
        is_output = saw_arrow
        slots.append(SlotInfo(name, slot_type, optional, is_output))
    return slots


def load_schema(url: str = _SCHEMA_URL) -> dict[int, list[SlotInfo]]:
    """Fetch and parse the CatWeb schema, returning ``action_id → slots`` map."""
    result: dict[int, list[SlotInfo]] = {}
    # Try cached local copy first, then URL
    text = None
    for src in [url, None]:
        try:
            if src:
                with urlopen(src, timeout=10) as resp:
                    text = resp.read().decode("utf-8")
                    break
        except Exception:
            continue
    if text is None:
        return result

    # Parse: ## ACTION_NAME (`id: N`)
    action_re = re.compile(r"^##\s+(\w+)\s+\(`id:\s*(\d+)`\)", re.MULTILINE)
    slot_re = re.compile(r"^`(.+)`$", re.MULTILINE)

    for m in action_re.finditer(text):
        name = m.group(1)
        aid = int(m.group(2))
        # Find the slot spec line that follows this action header
        pos = m.end()
        sm = slot_re.search(text, pos)
        if sm and sm.start() - pos < 200:  # within reasonable distance
            slots = parse_slots(sm.group(1))
            result[aid] = slots

    return result


# ---------------------------------------------------------------------------
# Helpers for compiler/decompiler
# ---------------------------------------------------------------------------

def get_output_slots(action_id: int | str, schema: dict[int, list[SlotInfo]] | None = None
                     ) -> list[int]:
    """Return indices of output slots for *action_id*.

    Returns empty list for actions with no outputs.
    """
    aid = int(action_id) if isinstance(action_id, str) else action_id
    if schema is None:
        return []
    slots = schema.get(aid, [])
    return [i for i, s in enumerate(slots) if s.is_output]


def slot_uses_braces(action_id: int | str, slot_index: int,
                     schema: dict[int, list[SlotInfo]] | None = None) -> bool:
    """Whether a variable reference in *slot_index* should be wrapped in ``{}``.

    Returns True for ``any`` and ``number`` slots, False for ``variable``,
    ``object``, and output slots (they expect bare names).
    """
    aid = int(action_id) if isinstance(action_id, str) else action_id
    if schema is None:
        return True  # default: wrap in braces
    slots = schema.get(aid, [])
    if slot_index >= len(slots):
        return True
    s = slots[slot_index]
    # Output slots and variable/object slots use bare names
    if s.is_output or s.slot_type in ("variable", "object"):
        return False
    return True


# Cache
_schema_cache: dict[int, list[SlotInfo]] | None = None


def get_schema() -> dict[int, list[SlotInfo]]:
    """Get cached schema (loads on first call)."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = load_schema()
    return _schema_cache
