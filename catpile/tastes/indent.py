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
        return indent_parse(source)

    def validate(self, source: str) -> list[dict]:
        """Quick syntax validation. Returns diagnostics."""
        try:
            indent_parse(source)
            return []
        except (SyntaxError, ParseError) as e:
            line = getattr(e, 'line', 0) or 1
            return [{
                "line": line,
                "col": 1,
                "message": str(e),
                "severity": "error",
            }]
