"""Catpile indent taste - the current indentation-based Pythonic syntax."""

from __future__ import annotations

from . import Taste
from ..ir import Program
from ..parser import parse as indent_parse, ParseError


class IndentSyntax(Taste):
    """Indentation-based syntax - Pythonic, no braces needed."""

    @property
    def name(self) -> str:
        return "indent"

    def compile(self, source: str) -> Program:
        default_scope = self._config.get("default_scope", "local")
        return indent_parse(source, default_scope=default_scope)

    def validate(self, source: str) -> list[dict]:
        """Quick syntax validation. Returns diagnostics."""
        try:
            default_scope = self._config.get("default_scope", "local")
            indent_parse(source, default_scope=default_scope)
            return []
        except (SyntaxError, ParseError) as e:
            line = getattr(e, 'line', 0) or 1
            return [{
                "line": line,
                "col": 1,
                "message": str(e),
                "severity": "error",
            }]
