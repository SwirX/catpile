"""Bracket syntax taste - JS/Dart/C++ style with { } blocks and ; terminators.

Syntax:
    on loaded { log("hello"); msg = "world"; }

    fn add(a, b) { return x + y; }

    if eq(x, 5) { log("five"); } else { log("not"); }

    repeat(3) { log("loop"); }
    repeat_forever { log("inf"); break; }

    foreach(items) { log("item"); }
"""

from __future__ import annotations

import re
from typing import Any

from . import Taste
from ..ir import (
    Program, ScriptDef, EventDef, FunctionDef,
    ActionStmt, IfStmt, RepeatStmt, ForEachStmt, BreakStmt, ReturnStmt,
    VarRef, StrLit, NumLit, ObjectRef, InterpolatedStr, MathExpr,
    MathNode, MathNum, MathVarRef, BinOp,
    DictLiteral, ListLiteral, KVPair,
)
from .. import mappings as M
from catpile import scope_var_name


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class Token:
    __slots__ = ("kind", "value", "line", "col")
    def __init__(self, kind: str, value: str, line: int, col: int) -> None:
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r})"


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    lineno = 1
    i = 0

    while i < len(source):
        ch = source[i]
        col = i

        # Newline
        if ch == "\n":
            lineno += 1
            i += 1
            continue

        # Whitespace
        if ch in " \t\r":
            i += 1
            continue

        # Line comment //
        if ch == "/" and i + 1 < len(source) and source[i + 1] == "/":
            end = source.find("\n", i)
            if end == -1:
                end = len(source)
            tokens.append(Token("COMMENT", source[i:end], lineno, col))
            i = end
            continue

        # Braces
        if ch == "{":
            # Check for variable reference {name} first - look ahead for }
            j = source.find("}", i + 1)
            if j != -1 and j - i < 50:  # reasonable var name length
                inside = source[i + 1:j]
                if inside.isidentifier() and inside != "":
                    tokens.append(Token("VARIABLE", inside, lineno, col))
                    i = j + 1
                    continue
            tokens.append(Token("BLOCK_OPEN", "{", lineno, col))
            i += 1
            continue
        if ch == "}":
            tokens.append(Token("BLOCK_CLOSE", "}", lineno, col))
            i += 1
            continue

        # Semicolon
        if ch == ";":
            tokens.append(Token("SEMICOLON", ";", lineno, col))
            i += 1
            continue

        # Parentheses
        if ch == "(":
            tokens.append(Token("LPAREN", "(", lineno, col))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token("RPAREN", ")", lineno, col))
            i += 1
            continue

        # Comma
        if ch == ",":
            tokens.append(Token("COMMA", ",", lineno, col))
            i += 1
            continue

        # Colon (for event params, etc.)
        if ch == ":":
            tokens.append(Token("COLON", ":", lineno, col))
            i += 1
            continue

        # Brackets (for list/dict literals)
        if ch == "[":
            tokens.append(Token("LBRACKET", "[", lineno, col))
            i += 1
            continue
        if ch == "]":
            tokens.append(Token("RBRACKET", "]", lineno, col))
            i += 1
            continue

        # Assign
        if ch == "=":
            # Check for == first (condition) before single = (assignment)
            # We need to peek ahead. If next char is =, it's a condition.
            # Since we can't unread a char after advancing, handle == here.
            if i + 1 < len(source) and source[i + 1] == "=":
                tokens.append(Token("COND", "==", lineno, col))
                i += 2
                continue
            tokens.append(Token("ASSIGN", "=", lineno, col))
            i += 1
            continue

        # Condition operators
        if ch == "!" and i + 1 < len(source) and source[i + 1] == "=":
            tokens.append(Token("COND", "!=", lineno, col))
            i += 2
            continue
        if ch == ">" and i + 1 < len(source) and source[i + 1] == "=":
            tokens.append(Token("COND", ">=", lineno, col))
            i += 2
            continue
        if ch == "<" and i + 1 < len(source) and source[i + 1] == "=":
            tokens.append(Token("COND", "<=", lineno, col))
            i += 2
            continue
        if ch == ">":
            tokens.append(Token("COND", ">", lineno, col))
            i += 1
            continue
        if ch == "<":
            tokens.append(Token("COND", "<", lineno, col))
            i += 1
            continue
        if ch == "!":
            tokens.append(Token("OP", "!", lineno, col))
            i += 1
            continue

        # Math operators
        if ch in "+-*/%^":
            tokens.append(Token("OP", ch, lineno, col))
            i += 1
            continue

        # String literal
        if ch == '"':
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == "\\" and j + 1 < len(source):
                    j += 2
                    continue
                j += 1
            if j >= len(source):
                raise SyntaxError(f"Unterminated string at line {lineno}")
            value = source[i + 1:j]
            tokens.append(Token("STRING", value, lineno, col))
            i = j + 1
            continue

        # Number
        if ch.isdigit() or (ch == "-" and i + 1 < len(source)
                            and source[i + 1].isdigit()):
            j = i + 1
            while j < len(source) and (source[j].isdigit()
                                       or source[j] == "."):
                j += 1
            tokens.append(Token("NUMBER", source[i:j], lineno, col))
            i = j
            continue

        # Identifier or keyword (supports dotted paths: page.Button.Name)
        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < len(source) and (source[j].isalnum()
                                       or source[j] == "_"):
                j += 1
            # Allow dotted paths: ident.ident.ident
            while j < len(source) and source[j] == "." and j + 1 < len(source) \
                    and (source[j+1].isalpha() or source[j+1] == "_"):
                j += 1
                while j < len(source) and (source[j].isalnum()
                                           or source[j] == "_"):
                    j += 1
            word = source[i:j]
            tokens.append(Token("IDENT", word, lineno, col))
            i = j
            continue

        raise SyntaxError(
            f"Unexpected character {ch!r} at line {lineno}")

    tokens.append(Token("EOF", "", lineno, i))
    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class ParseError(Exception):
    pass


class BracketParser:
    """Bracket-based parser for the { } block syntax."""

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        return self._tokens[idx] if idx < len(self._tokens) else self._tokens[-1]

    def _advance(self) -> Token:
        t = self._tokens[self._pos]
        self._pos += 1
        return t

    def _match(self, *kinds: str, value: str | None = None) -> Token | None:
        t = self._peek()
        if t.kind in kinds and (value is None or t.value == value):
            return self._advance()
        return None

    def _expect(self, kind: str, value: str | None = None) -> Token:
        t = self._match(kind, value=value)
        if t is None:
            got = self._peek()
            expected = f"{kind}={value!r}" if value else kind
            raise ParseError(
                f"Expected {expected}, got {got.kind}={got.value!r} "
                f"at line {got.line}")
        return t

    def _skip_semicolons(self) -> None:
        """Consume optional semicolons and comments."""
        while self._peek().kind in ("SEMICOLON", "COMMENT"):
            self._advance()

    # -- Top-level ----------------------------------------------------------

    def parse(self) -> Program:
        scripts: list[ScriptDef] = []
        current = ScriptDef()

        while self._peek().kind != "EOF":
            self._skip_semicolons()
            if self._peek().kind == "EOF":
                break

            t = self._peek()

            if t.kind == "IDENT" and t.value in ("local", "obj"):
                scope = self._advance().value
                self._skip_semicolons()
                if self._peek().kind == "IDENT" and self._peek(1).kind == "ASSIGN":
                    stmt = self._parse_assignment()
                    current.events.append(
                        EventDef(type="LOADED", body=[stmt]))
                continue

            if t.kind == "IDENT" and t.value == "script":
                self._advance()
                name_tok = self._match("STRING", "IDENT")
                alias = name_tok.value if name_tok else "Script"
                self._expect("BLOCK_OPEN")
                if current.events or current.functions or current.alias:
                    scripts.append(current)
                current = ScriptDef(alias=alias)
                # Parse all events/functions inside this script block
                while self._peek().kind not in ("BLOCK_CLOSE", "EOF"):
                    self._skip_semicolons()
                    if self._peek().kind in ("BLOCK_CLOSE", "EOF"):
                        break
                    st = self._peek()
                    if st.kind == "IDENT" and st.value == "on":
                        current.events.append(self._parse_event_def())
                    elif st.kind == "IDENT" and st.value == "fn":
                        current.functions.append(self._parse_function_def())
                    else:
                        raise ParseError(
                            f"Expected 'on' or 'fn' inside script, "
                            f"got {st.value!r} at line {st.line}")
                self._expect("BLOCK_CLOSE")
                continue

            if t.kind == "IDENT" and t.value == "on":
                ev = self._parse_event_def()
                current.events.append(ev)
            elif t.kind == "IDENT" and t.value == "fn":
                fn = self._parse_function_def()
                current.functions.append(fn)
            else:
                raise ParseError(
                    f"Expected 'on', 'fn', or 'script', "
                    f"got {t.value!r} at line {t.line}")

        if current.events or current.functions or current.alias:
            scripts.append(current)
        return Program(scripts=scripts)

    # -- Events -------------------------------------------------------------

    def _parse_event_def(self) -> EventDef:
        self._expect("IDENT", value="on")
        name = scope_var_name(self._expect("IDENT").value)
        try:
            name = M.resolve_event(name.lower().replace(" ", "_"))
        except KeyError:
            pass

        params: list[str] = []
        if self._match("LPAREN"):
            if not self._match("RPAREN"):
                tok = self._advance()
                params.append(tok.value)
                while self._match("COMMA"):
                    params.append(self._expect("STRING", "IDENT").value)
                self._expect("RPAREN")

        self._expect("BLOCK_OPEN")
        body = self._parse_body()
        self._expect("BLOCK_CLOSE")

        return EventDef(type=name, params=params, body=body)

    # -- Functions ----------------------------------------------------------

    def _parse_function_def(self) -> FunctionDef:
        self._expect("IDENT", value="fn")
        name = scope_var_name(self._expect("IDENT").value)
        self._expect("LPAREN")
        params: list[str] = []
        if not self._match("RPAREN"):
            params.append(self._expect("IDENT").value)
            while self._match("COMMA"):
                params.append(self._expect("IDENT").value)
            self._expect("RPAREN")
        self._expect("BLOCK_OPEN")
        body = self._parse_body()
        self._expect("BLOCK_CLOSE")
        return FunctionDef(name=name, params=params, body=body)

    # -- Body / Block -------------------------------------------------------

    def _parse_body(self) -> list:
        """Parse statements until BLOCK_CLOSE or EOF."""
        stmts: list = []
        while self._peek().kind not in ("BLOCK_CLOSE", "EOF"):
            self._skip_semicolons()
            if self._peek().kind in ("BLOCK_CLOSE", "EOF"):
                break
            stmts.append(self._parse_statement())
            self._skip_semicolons()
        return stmts

    def _parse_statement(self):
        t = self._peek()

        if t.kind == "COMMENT":
            self._advance()
            return self._parse_statement() if self._peek().kind != "BLOCK_CLOSE" else ActionStmt("COMMENT", [])

        # Scope keyword + assignment
        if t.kind == "IDENT" and t.value in ("global", "local", "obj"):
            self._advance()
            return self._parse_assignment()

        # Assignment: IDENT = value
        if t.kind == "IDENT" and self._peek(1).kind == "ASSIGN":
            return self._parse_assignment()

        if t.kind == "IDENT":
            if t.value == "if":
                return self._parse_if_stmt()
            if t.value == "repeat":
                return self._parse_repeat_stmt()
            if t.value == "repeat_forever":
                return self._parse_repeat_forever()
            if t.value == "foreach":
                return self._parse_foreach_stmt()
            if t.value == "break":
                self._advance()
                return BreakStmt()
            if t.value == "return":
                return self._parse_return_stmt()
            if t.value == "else":
                raise ParseError(
                    f"'else' without matching 'if' at line {t.line}")

        return self._parse_action_call()

    # -- Assignment ---------------------------------------------------------

    def _parse_assignment(self) -> ActionStmt:
        line = self._peek().line
        name = scope_var_name(self._expect("IDENT").value)
        self._expect("ASSIGN")
        value = self._parse_arg()
        # Pass the raw arg through - emitter handles dict/list/math/interpolation
        return ActionStmt("VAR_SET", [StrLit(name), value],
                          line=line)

    def _parse_scope_assignment(self) -> ActionStmt:
        """local|obj IDENT = value  →  VAR_SET."""
        line = self._peek().line
        scope = self._advance().value
        name = scope_var_name(self._expect("IDENT").value)
        self._expect("ASSIGN")
        value = self._parse_arg()
        return ActionStmt("VAR_SET", [StrLit(name), value], line=line)

    # -- Control flow -------------------------------------------------------

    def _parse_if_stmt(self) -> IfStmt:
        line = self._peek().line
        self._expect("IDENT", value="if")

        # Check for operator syntax: if left == right { body }
        # vs function syntax: if eq(left, right) { body }
        if (self._peek().kind in ("IDENT", "VARIABLE", "NUMBER")
                and self._peek(1).kind == "COND"):
            left = self._parse_arg()
            cond_tok = self._expect("COND")
            right = self._parse_arg()
            cond_map = {
                "==": "IF_EQ", "!=": "IF_NEQ", ">": "IF_GT",
                "<": "IF_LT", ">=": "IF_GTE", "<=": "IF_LTE",
            }
            cond_name = cond_map.get(cond_tok.value, "IF_EQ")
            rendered_left = self._render_arg_to_str(left)
            rendered_right = self._render_arg_to_str(right)
            args = [StrLit(rendered_left), StrLit(rendered_right)]
        else:
            cond_name = self._expect("IDENT").value
            try:
                cond_name = M.resolve_action(cond_name)
            except KeyError:
                pass
            self._expect("LPAREN")
            args = []
            if not self._match("RPAREN"):
                args.append(self._parse_arg())
                while self._match("COMMA"):
                    args.append(self._parse_arg())
                self._expect("RPAREN")

        self._expect("BLOCK_OPEN")
        body = self._parse_body()
        self._expect("BLOCK_CLOSE")

        else_body = None
        self._skip_semicolons()
        if (self._peek().kind == "IDENT" and self._peek().value == "else"
                and self._peek(1).kind == "BLOCK_OPEN"):
            self._advance()
            self._expect("BLOCK_OPEN")
            else_body = self._parse_body()
            self._expect("BLOCK_CLOSE")

        return IfStmt(condition=cond_name, args=args,
                      body=body, else_body=else_body, line=line)

    def _parse_repeat_stmt(self) -> RepeatStmt:
        line = self._peek().line
        self._expect("IDENT", value="repeat")
        self._expect("LPAREN")
        t = self._peek()
        if t.kind == "NUMBER":
            times_str = self._advance().value
        elif t.kind in ("IDENT", "VARIABLE"):
            times_str = scope_var_name(t.value)
            self._advance()
        else:
            raise ParseError(
                f"Expected number or variable, got {t.kind}={t.value!r}"
                f" at line {t.line}")
        self._expect("RPAREN")
        self._expect("BLOCK_OPEN")
        body = self._parse_body()
        self._expect("BLOCK_CLOSE")
        return RepeatStmt(times=times_str, body=body, line=line)

    def _parse_repeat_forever(self) -> RepeatStmt:
        line = self._peek().line
        self._advance()
        self._expect("BLOCK_OPEN")
        body = self._parse_body()
        self._expect("BLOCK_CLOSE")
        return RepeatStmt(times=None, body=body, line=line)

    def _parse_foreach_stmt(self) -> ForEachStmt:
        line = self._peek().line
        self._expect("IDENT", value="foreach")
        self._expect("LPAREN")
        t = self._peek()
        if t.kind == "STRING":
            table_arg = StrLit(self._advance().value)
        else:
            table_arg = VarRef(scope_var_name(self._expect("IDENT").value))
        self._expect("RPAREN")
        self._expect("BLOCK_OPEN")
        body = self._parse_body()
        self._expect("BLOCK_CLOSE")
        return ForEachStmt(table=table_arg, body=body, line=line)

    def _parse_return_stmt(self) -> ReturnStmt:
        self._expect("IDENT", value="return")
        if self._peek().kind in ("STRING", "NUMBER", "IDENT", "VARIABLE"):
            val = self._parse_arg()
            return ReturnStmt(value=val)
        return ReturnStmt(value=None)

    # -- Action calls -------------------------------------------------------

    def _parse_action_call(self) -> ActionStmt:
        line = self._peek().line
        name = scope_var_name(self._expect("IDENT").value)
        try:
            canonical = M.resolve_action(name)
        except KeyError:
            canonical = name
        name = canonical
        self._expect("LPAREN")
        args: list = []
        if not self._match("RPAREN"):
            args.append(self._parse_arg())
            while self._match("COMMA"):
                args.append(self._parse_arg())
            self._expect("RPAREN")
        return ActionStmt(name=name, args=args, line=line)

    # -- Arguments ----------------------------------------------------------

    def _parse_arg(self):
        t = self._peek()
        if t.kind == "STRING":
            self._advance()
            val = t.value
            parts = self._detect_interpolation(val)
            if parts is not None:
                return InterpolatedStr(parts)
            return StrLit(val)
        if t.kind == "NUMBER":
            self._advance()
            return NumLit(t.value)
        if t.kind == "VARIABLE":
            self._advance()
            return VarRef(scope_var_name(t.value))
        if t.kind == "IDENT":
            self._advance()
            if "." in t.value:
                return ObjectRef(t.value)
            return VarRef(scope_var_name(t.value))
        if t.kind == "BLOCK_OPEN":
            return self._parse_dict_literal()
        if t.kind == "LBRACKET":
            return self._parse_list_literal()
        raise ParseError(
            f"Expected argument, got {t.kind}={t.value!r} at line {t.line}")

    def _parse_dict_literal(self) -> DictLiteral:
        """Parse a dict literal: ``{key: value, ...}``."""
        self._expect("BLOCK_OPEN")
        entries: list[KVPair] = []

        if self._peek().kind != "BLOCK_CLOSE":
            while True:
                key = self._parse_arg()
                self._expect("COLON")
                value = self._parse_arg()
                entries.append(KVPair(key=key, value=value))
                if not self._match("COMMA"):
                    break

        self._expect("BLOCK_CLOSE")
        return DictLiteral(entries=entries)

    def _parse_list_literal(self) -> ListLiteral:
        """Parse a list literal: ``[item, ...]``."""
        self._expect("LBRACKET")
        items: list = []

        if self._peek().kind != "RBRACKET":
            while True:
                items.append(self._parse_arg())
                if not self._match("COMMA"):
                    break

        self._expect("RBRACKET")
        return ListLiteral(items=items)

    def _render_arg_to_str(self, arg) -> str:
        if isinstance(arg, StrLit):
            return arg.value
        if isinstance(arg, NumLit):
            return arg.value
        if isinstance(arg, VarRef):
            return "{" + arg.name + "}"
        if isinstance(arg, InterpolatedStr):
            return self._render_arg_to_str(arg.parts[0]) if arg.parts else ""
        return str(arg)

    def _detect_interpolation(self, val: str) -> list | None:
        parts: list = []
        last = 0
        found = False
        for m in re.finditer(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", val):
            found = True
            if m.start() > last:
                parts.append(StrLit(val[last:m.start()]))
            parts.append(VarRef(scope_var_name(m.group(1))))
            last = m.end()
        if not found:
            return None
        if last < len(val):
            parts.append(StrLit(val[last:]))
        return parts


# ---------------------------------------------------------------------------
# Taste
# ---------------------------------------------------------------------------

class BracketSyntax(Taste):
    """Braces syntax - JS/Dart/C++ style with { } blocks and ; terminators."""

    @property
    def name(self) -> str:
        return "bracket"

    def compile(self, source: str) -> Program:
        tokens = tokenize(source)
        return BracketParser(tokens).parse()

    def validate(self, source: str) -> list[dict]:
        try:
            self.compile(source)
            return []
        except (SyntaxError, ParseError) as e:
            line = getattr(e, 'line', 0) or 1
            return [{
                "line": line,
                "col": 1,
                "message": str(e),
                "severity": "error",
            }]
