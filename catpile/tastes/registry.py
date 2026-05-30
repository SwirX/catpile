"""Taste registry - discover and select syntax front-ends."""

from __future__ import annotations

from typing import Any
from . import Taste
from .v1 import IndentSyntax
from .bracket import BracketSyntax


#: Built-in tastes, registered by name.
_BUILTINS: dict[str, type[Taste]] = {
    "indent": IndentSyntax,
    "bracket": BracketSyntax,
}


def get_taste(name: str, config: dict | None = None) -> Taste:
    """Return a Taste instance by name, optionally with *config*.

    Raises ``KeyError`` if not found.
    """
    cls = _BUILTINS.get(name)
    if cls is None:
        raise KeyError(
            f"Unknown taste {name!r}. "
            f"Available: {', '.join(sorted(_BUILTINS))}"
        )
    return cls(config=config)


def list_tastes() -> list[str]:
    """Return list of registered taste names."""
    return sorted(_BUILTINS)


def register_taste(name: str, taste_cls: type[Taste]) -> None:
    """Register a custom taste."""
    _BUILTINS[name] = taste_cls
