"""Taste protocol - abstract interface for syntax front-ends.

A "taste" is a pluggable syntax variant that compiles to the Catpile IR.
Different tastes parse different source syntaxes but target the same
CatWeb JSON backend via the shared emitter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..ir import Program


class Taste(ABC):
    """Base class for a syntax front-end (taste).

    Each taste implements ``compile(source: str) → Program``.
    The resulting Program is then fed to the shared emitter.
    """

    def __init__(self, config: dict | None = None):
        self._config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this taste (e.g. 'indent')."""
        ...

    @abstractmethod
    def compile(self, source: str) -> Program:
        """Parse *source* text into an IR Program."""
        ...

    def validate(self, source: str) -> list[dict]:
        """Return a list of diagnostics (error/warning dicts).

        Each diagnostic::
            {"line": int, "col": int, "message": str, "severity": "error"|"warning"}
        """
        return []
