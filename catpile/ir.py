"""Intermediate Representation (IR) for Catpile programs.

This is the output of the parser and the input to the emitter.
Language-agnostic - any front-end syntax can target this IR.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VarRef:
    """Reference to a CatWeb variable (rendered as ``{name}`` in JSON)."""
    name: str


@dataclass(frozen=True)
class StrLit:
    value: str


@dataclass(frozen=True)
class NumLit:
    value: str  # keep as string for CatWeb


@dataclass(frozen=True)
class ObjectRef:
    """Reference to a UI object / element (rendered with ``t: object``)."""
    name: str


@dataclass(frozen=True)
class InterpolatedStr:
    """String with ``{var}`` interpolation markers.

    ``parts`` alternates between string literals and variable references.
    On emission this becomes concatenation actions + a temp variable.
    """
    parts: list[StrLit | VarRef]


@dataclass(frozen=True)
class MathExpr:
    """A math expression used as an argument.

    Resolved at emit time: constant-folded if all literals,
    or expanded to math actions if variables are involved.
    """
    tree: "MathNode"


# ---------------------------------------------------------------------------
# Dict / List literals
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KVPair:
    """A single key-value pair in a dict literal."""
    key: "Arg"
    value: "Arg"


@dataclass(frozen=True)
class DictLiteral:
    """A dictionary/object literal compiled to CatWeb table actions.

    ``{"key": value, ...}`` → createTable + setentry actions at emit time.
    """
    entries: list[KVPair]


@dataclass(frozen=True)
class ListLiteral:
    """A list/array literal compiled to CatWeb table actions.

    ``[item1, item2, ...]`` → createTable + numeric-keyed setentry actions.
    """
    items: list["Arg"]


# ---------------------------------------------------------------------------
# Arg union
# ---------------------------------------------------------------------------

Arg = (
    StrLit | NumLit | VarRef | ObjectRef
    | InterpolatedStr | MathExpr | DictLiteral | ListLiteral | str
)


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MathNum:
    """Numeric literal in an expression."""
    value: str


@dataclass(frozen=True)
class MathVarRef:
    """Variable reference in an expression."""
    name: str


@dataclass(frozen=True)
class BinOp:
    """Binary math operation."""
    left: "MathNode"
    op: str
    right: "MathNode"


MathNode = MathNum | MathVarRef | BinOp


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

@dataclass
class ActionStmt:
    """A single CatWeb action block."""
    name: str       # Action name from ACTIONS (e.g. "LOG", "VAR_SET")
    args: list[Arg] = field(default_factory=list)
    line: int = 0   # Source line number


@dataclass
class IfStmt:
    condition: str       # Action name for the condition (e.g. "IF_EQ")
    args: list[Arg] = field(default_factory=list)
    body: list[Stmt] = field(default_factory=list)
    else_body: list[Stmt] | None = None
    line: int = 0


@dataclass
class RepeatStmt:
    times: str | None = None   # None = forever, string = count or {var}
    body: list[Stmt] = field(default_factory=list)
    line: int = 0


@dataclass
class ForEachStmt:
    """Iterate through a table.

    *table* is an Arg: ``VarRef`` (bare identifier → variable ref) or
    ``StrLit`` (quoted string → string literal).
    """
    table: Arg
    body: list[Stmt] = field(default_factory=list)
    line: int = 0


@dataclass
class BreakStmt:
    pass


@dataclass
class ReturnStmt:
    value: Arg | None = None


Stmt = ActionStmt | IfStmt | RepeatStmt | ForEachStmt | BreakStmt | ReturnStmt


# ---------------------------------------------------------------------------
# Top-level definitions
# ---------------------------------------------------------------------------

@dataclass
class EventDef:
    """An event handler (e.g. "When website loaded...")."""
    type: str               # Event key from EVENTS (e.g. "LOADED", "PRESSED")
    params: list[str] = field(default_factory=list)  # Event parameter values
    body: list[Stmt] = field(default_factory=list)


@dataclass
class FunctionDef:
    """A CatWeb function definition."""
    name: str
    params: list[str] = field(default_factory=list)
    body: list[Stmt] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Program (entry-point)
# ---------------------------------------------------------------------------

@dataclass
class ScriptDef:
    """A single CatWeb script file with multiple events/functions."""
    alias: str | None = None
    events: list[EventDef] = field(default_factory=list)
    functions: list[FunctionDef] = field(default_factory=list)


@dataclass
class Program:
    """Top-level compilation unit - one or more scripts."""
    scripts: list[ScriptDef] = field(default_factory=list)
