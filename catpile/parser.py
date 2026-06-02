"""Catpile text DSL parser - Pythonic syntax → IR.

Grammar (informal):

    program       := (event_def | function_def | comment_line)*

    event_def     := 'on' IDENT ['(' param (',' param)* ')'] ':' NEWLINE
                     INDENT statement+ DEDENT

    function_def  := 'fn' IDENT '(' param_list ')' ':' NEWLINE
                     INDENT statement+ DEDENT

    param_list    := IDENT (',' IDENT)*

    statement     := action_call
                   | assignment
                   | if_stmt
                   | repeat_stmt
                   | foreach_stmt
                   | break_stmt
                   | return_stmt
                   | comment_line

    action_call   := IDENT '(' arg (',' arg)* ')'
    arg           := STRING | NUMBER | IDENT | '{' IDENT '}' | dict | list

    assignment    := IDENT '=' arg

    if_stmt       := 'if' IDENT '(' arg (',' arg)* ')' ':' NEWLINE
                     INDENT statement+ DEDENT
                     ('else:' NEWLINE INDENT statement+ DEDENT)?

    repeat_stmt   := 'repeat' '(' NUMBER ')' ':' NEWLINE
                     INDENT statement+ DEDENT
                   | 'repeat_forever' ':' NEWLINE
                     INDENT statement+ DEDENT

    foreach_stmt  := 'foreach' '(' IDENT ')' ':' NEWLINE
                     INDENT statement+ DEDENT

    break_stmt    := 'break' NEWLINE
    return_stmt   := 'return' arg? NEWLINE
    comment_line  := '#' .* NEWLINE
"""

from __future__ import annotations

import re
from typing import Any

from . import ir
from . import mappings as M
from .ir import MathNum, MathVarRef, BinOp, MathNode, MathExpr, DictLiteral, ListLiteral, KVPair
from catpile import scope_var_name


# ---------------------------------------------------------------------------
# Lexer
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
    """Simple line-based tokenizer for the Catpile DSL."""
    tokens: list[Token] = []
    indent_stack = [0]
    lines = source.split("\n")

    for lineno, raw_line in enumerate(lines, start=1):
        stripped = raw_line.lstrip()
        indent = len(raw_line) - len(stripped)

        # Skip blank lines
        if not stripped:
            continue

        # Custom behaviour for our DSL: comments
        if stripped.startswith("#"):
            # Track indentation for comments so body parsing works
            if indent > indent_stack[-1]:
                indent_stack.append(indent)
                tokens.append(Token("INDENT", "", lineno, indent))
            elif indent < indent_stack[-1]:
                while indent_stack and indent_stack[-1] != indent:
                    indent_stack.pop()
                    tokens.append(Token("DEDENT", "", lineno, indent))
                if indent_stack[-1] != indent:
                    raise SyntaxError(
                        f"Inconsistent indentation at line {lineno}")
            tokens.append(Token("COMMENT", stripped, lineno, indent))
            continue

        # Indentation tracking
        if indent > indent_stack[-1]:
            indent_stack.append(indent)
            tokens.append(Token("INDENT", "", lineno, indent))
        elif indent < indent_stack[-1]:
            while indent_stack and indent_stack[-1] != indent:
                indent_stack.pop()
                tokens.append(Token("DEDENT", "", lineno, indent))
            if indent_stack[-1] != indent:
                raise SyntaxError(
                    f"Inconsistent indentation at line {lineno}")
        # same indent = nothing

        # Tokenize the line content
        col = indent
        i = 0
        while i < len(stripped):
            ch = stripped[i]

            # Skip spaces within the line
            if ch in " \t":
                i += 1
                col += 1
                continue

            # Assign (=)
            if ch == "=":
                tokens.append(Token("ASSIGN", "=", lineno, col))
                i += 1
                col += 1
                continue

            # Punctuation
            if ch == "(":
                tokens.append(Token("LPAREN", "(", lineno, col))
                i += 1
                col += 1
                continue
            if ch == ")":
                tokens.append(Token("RPAREN", ")", lineno, col))
                i += 1
                col += 1
                continue
            if ch == ":":
                tokens.append(Token("COLON", ":", lineno, col))
                i += 1
                col += 1
                continue
            if ch == ",":
                tokens.append(Token("COMMA", ",", lineno, col))
                i += 1
                col += 1
                continue
            if ch == "[":
                tokens.append(Token("LBRACKET", "[", lineno, col))
                i += 1
                col += 1
                continue
            if ch == "]":
                tokens.append(Token("RBRACKET", "]", lineno, col))
                i += 1
                col += 1
                continue
            if ch == "{":
                # Check if it's a variable reference {name} first
                j = source.find("}", i + 1, i + 50)
                if j != -1:
                    inside = source[i + 1:j]
                    if inside.isidentifier() and inside:
                        tokens.append(Token("VARIABLE", inside, lineno, col))
                        i = j + 1
                        col += (j - i + 1)
                        continue
                # Otherwise it's a dict literal
                tokens.append(Token("BLOCK_OPEN", "{", lineno, col))
                i += 1
                col += 1
                continue
            if ch == "}":
                tokens.append(Token("BLOCK_CLOSE", "}", lineno, col))
                i += 1
                col += 1
                continue

            # String literal (double-quoted)
            if ch == '"':
                j = i + 1
                while j < len(stripped) and stripped[j] != '"':
                    if stripped[j] == "\\" and j + 1 < len(stripped):
                        j += 2  # skip backslash AND the escaped character
                        continue
                    j += 1
                if j >= len(stripped):
                    raise SyntaxError(
                        f"Unterminated string at line {lineno}")
                value = stripped[i + 1:j]
                tokens.append(Token("STRING", value, lineno, col))
                i = j + 1
                col = col + (j - i + 1)
                continue

            # Variable reference {name}
            if ch == "{":
                j = stripped.find("}", i + 1)
                if j == -1:
                    raise SyntaxError(
                        f"Unterminated variable reference at line {lineno}")
                name = stripped[i + 1:j]
                tokens.append(Token("VARIABLE", name, lineno, col))
                i = j + 1
                col += (j - i + 1)
                continue

            # Number literal
            if ch.isdigit() or (ch == "-" and i + 1 < len(stripped) and stripped[i + 1].isdigit()):
                j = i + 1
                while j < len(stripped) and (stripped[j].isdigit() or stripped[j] == "."):
                    j += 1
                tokens.append(Token("NUMBER", stripped[i:j], lineno, col))
                i = j
                col += (j - i)
                continue

            # Identifier or keyword (supports dotted paths: page.Button.Name)
            if ch.isalpha() or ch == "_":
                j = i + 1
                while j < len(stripped) and (stripped[j].isalnum() or stripped[j] == "_"):
                    j += 1
                # Allow dotted paths: ident.ident.ident
                while j < len(stripped) and stripped[j] == "." and j + 1 < len(stripped) \
                        and (stripped[j+1].isalpha() or stripped[j+1] == "_"):
                    j += 1  # skip dot
                    while j < len(stripped) and (stripped[j].isalnum() or stripped[j] == "_"):
                        j += 1
                word = stripped[i:j]
                tokens.append(Token("IDENT", word, lineno, col))
                i = j
                col += (j - i)
                continue

            # Math operators
            if ch in "+-*/%^":
                tokens.append(Token("OP", ch, lineno, col))
                i += 1
                col += 1
                continue

            raise SyntaxError(
                f"Unexpected character {ch!r} at line {lineno}")

    # Close remaining indentation
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token("DEDENT", "", lineno, 0))

    tokens.append(Token("EOF", "", lineno, 0))
    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class ParseError(Exception):
    pass


class Parser:
    """Recursive-descent parser producing IR nodes."""

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # -- Helpers ------------------------------------------------------------

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return self._tokens[-1]

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
                f"Expected {expected}, got {got.kind}={got.value!r} at line {got.line}")
        return t

    def _skip_newlines(self) -> None:
        while self._match("COMMENT"):
            pass

    # -- Top-level ----------------------------------------------------------

    def parse(self) -> ir.Program:
        """Parse a complete program."""
        scripts: list[ir.ScriptDef] = []
        current = ir.ScriptDef()

        while self._peek().kind != "EOF":
            self._skip_newlines()
            if self._peek().kind == "EOF":
                break

            t = self._peek()

            if t.kind == "IDENT" and t.value == "script":
                # Flush current script
                if current.events or current.functions:
                    scripts.append(current)
                elif current.alias:
                    scripts.append(current)
                # Start new script with name
                self._advance()
                name_tok = self._match("STRING", "IDENT")
                alias = name_tok.value if name_tok else "Script"
                self._expect("COLON")
                current = ir.ScriptDef(alias=alias)
                # Check for empty script body (DEDENT or EOF right after COLON)
                self._skip_newlines()
                if self._peek().kind in ("DEDENT", "EOF"):
                    if self._peek().kind == "DEDENT":
                        self._advance()
                    continue
                # Consume script body indent
                self._expect("INDENT")
                # Parse all events/functions inside this script block
                while self._peek().kind not in ("DEDENT", "EOF"):
                    self._skip_newlines()
                    if self._peek().kind in ("DEDENT", "EOF"):
                        break
                    t2 = self._peek()
                    if t2.kind == "IDENT" and t2.value == "on":
                        current.events.append(self._parse_event_def())
                    elif t2.kind == "IDENT" and t2.value == "fn":
                        current.functions.append(self._parse_function_def())
                    else:
                        raise ParseError(
                            f"Expected 'on' or 'fn' inside script block, "
                            f"got {t2.value!r} at line {t2.line}")
                # Consume the DEDENT closing this script block
                if self._peek().kind == "DEDENT":
                    self._advance()

            elif t.kind == "IDENT" and t.value == "on":
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

        return ir.Program(scripts=scripts)

    # -- Events -------------------------------------------------------------

    def _parse_event_def(self) -> ir.EventDef:
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
                params.append(scope_var_name(tok.value))
                while self._match("COMMA"):
                    tok = self._expect("STRING", "IDENT")
                    params.append(scope_var_name(tok.value))
                self._expect("RPAREN")

        self._expect("COLON")
        body = self._parse_body()

        return ir.EventDef(type=name, params=params, body=body)

    # -- Functions ----------------------------------------------------------

    def _parse_function_def(self) -> ir.FunctionDef:
        self._expect("IDENT", value="fn")
        name = scope_var_name(self._expect("IDENT").value)
        self._expect("LPAREN")
        params: list[str] = []
        if not self._match("RPAREN"):
            params.append(scope_var_name(self._expect("IDENT").value))
            while self._match("COMMA"):
                params.append(scope_var_name(self._expect("IDENT").value))
            self._expect("RPAREN")
        self._expect("COLON")
        body = self._parse_body()
        return ir.FunctionDef(name=name, params=params, body=body)

    # -- Body parser --------------------------------------------------------

    def _parse_body(self) -> list[ir.Stmt]:
        """Parse indented block until DEDENT, consume the DEDENT.
        
        Handles empty blocks: if the next token is DEDENT (not INDENT),
        the block has no body.
        """
        # Skip any comments at the start of a body (they may lack indentation)
        while self._peek().kind == "COMMENT":
            self._advance()
        self._skip_newlines()
        # Empty body: next token is DEDENT instead of INDENT
        if self._peek().kind == "DEDENT":
            self._advance()
            return []
        self._expect("INDENT")
        stmts: list[ir.Stmt] = []
        while self._peek().kind not in ("DEDENT", "EOF"):
            self._skip_newlines()
            if self._peek().kind in ("DEDENT", "EOF"):
                break
            stmts.append(self._parse_statement())
        # Consume the DEDENT that closes this body
        if self._peek().kind == "DEDENT":
            self._advance()
        return stmts

    def _parse_statement(self) -> ir.Stmt:
        t = self._peek()

        if t.kind == "COMMENT":
            self._advance()
            return self._parse_statement() if self._peek().kind != "DEDENT" else ir.ActionStmt("COMMENT", [])

        # Scope keyword + assignment: local|obj IDENT = value
        if t.kind == "IDENT" and t.value in ("local", "obj"):
            return self._parse_scope_assignment()

        # Multi-target assignment: IDENT, IDENT = action_call()
        if (t.kind == "IDENT" and self._peek(1).kind == "COMMA"
                and self._peek(2).kind == "IDENT"
                and self._peek(3).kind == "ASSIGN"):
            return self._parse_multi_assign()

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
                return ir.BreakStmt()
            if t.value == "return":
                return self._parse_return_stmt()
            if t.value == "else":
                raise ParseError(
                    f"'else' without matching 'if' at line {t.line}")

        return self._parse_action_call()

    # -- Assignments --------------------------------------------------------

    def _parse_assignment(self) -> ir.ActionStmt:
        """IDENT = value or IDENT = action_call()  →  VAR_SET or action call"""
        line = self._peek().line
        name = scope_var_name(self._expect("IDENT").value)
        self._expect("ASSIGN")
        if (self._peek().kind == "IDENT"
                and self._peek(1).kind == "LPAREN"):
            act_name = self._expect("IDENT").value
            try:
                canonical = M.resolve_action(act_name)
            except KeyError:
                canonical = act_name
            self._expect("LPAREN")
            args: list[ir.Arg] = []
            if not self._match("RPAREN"):
                args.append(self._parse_arg())
                while self._match("COMMA"):
                    args.append(self._parse_arg())
                self._expect("RPAREN")
            args.append(ir.StrLit(name))
            return ir.ActionStmt(canonical, args, line=line)
        value = self._parse_arg()
        return ir.ActionStmt("VAR_SET", [ir.StrLit(name), value],
                             line=line)

    def _parse_multi_assign(self) -> ir.ActionStmt:
        """IDENT, IDENT = action_call()  →  action_call with targets as args"""
        line = self._peek().line
        targets: list[str] = []
        targets.append(scope_var_name(self._expect("IDENT").value))
        while self._match("COMMA"):
            targets.append(scope_var_name(self._expect("IDENT").value))
        self._expect("ASSIGN")
        # Now parse the action call: IDENT LPAREN args RPAREN
        name = scope_var_name(self._expect("IDENT").value)
        try:
            canonical = M.resolve_action(name)
        except KeyError:
            canonical = name
        name = canonical
        self._expect("LPAREN")
        call_args: list[ir.Arg] = []
        if not self._match("RPAREN"):
            call_args.append(self._parse_arg())
            while self._match("COMMA"):
                call_args.append(self._parse_arg())
            self._expect("RPAREN")
        # The output targets are passed as the LAST args
        # (they fill the schema's output variable slots)
        all_args = call_args + [ir.StrLit(t) for t in targets]
        return ir.ActionStmt(name, all_args, line=line)

    def _parse_scope_assignment(self) -> ir.ActionStmt:
        """local|obj IDENT = value  →  VAR_SET"""
        line = self._peek().line
        scope = self._advance().value
        name = scope_var_name(self._expect("IDENT").value)
        self._expect("ASSIGN")
        value = self._parse_arg()
        return ir.ActionStmt("VAR_SET", [ir.StrLit(name), value], line=line)

    # -- Control flow -------------------------------------------------------

    def _parse_if_stmt(self) -> ir.IfStmt:
        line = self._peek().line
        self._expect("IDENT", value="if")
        cond_name = self._expect("IDENT").value
        try:
            cond_name = M.resolve_action(cond_name)
        except KeyError:
            pass
        self._expect("LPAREN")
        args: list[ir.Arg] = []
        if not self._match("RPAREN"):
            args.append(self._parse_arg())
            while self._match("COMMA"):
                args.append(self._parse_arg())
            self._expect("RPAREN")
        self._expect("COLON")
        body = self._parse_body()

        else_body: list[ir.Stmt] | None = None
        if (self._peek().kind == "IDENT" and self._peek().value == "else"
                and self._peek(1).kind == "COLON"):
            self._advance()
            self._expect("COLON")
            else_body = self._parse_body()

        return ir.IfStmt(condition=cond_name, args=args,
                         body=body, else_body=else_body, line=line)

    def _parse_repeat_stmt(self) -> ir.RepeatStmt:
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
        self._expect("COLON")
        body = self._parse_body()
        return ir.RepeatStmt(times=times_str, body=body, line=line)

    def _parse_repeat_forever(self) -> ir.RepeatStmt:
        line = self._peek().line
        self._expect("IDENT", value="repeat_forever")
        self._expect("COLON")
        body = self._parse_body()
        return ir.RepeatStmt(times=None, body=body, line=line)

    def _parse_foreach_stmt(self) -> ir.ForEachStmt:
        line = self._peek().line
        self._expect("IDENT", value="foreach")
        self._expect("LPAREN")
        # Accept both bare IDENT and quoted STRING (decompiler uses strings)
        t = self._peek()
        if t.kind == "STRING":
            table_arg: ir.Arg = ir.StrLit(self._advance().value)
        else:
            table_arg = ir.VarRef(scope_var_name(self._expect("IDENT").value))
        self._expect("RPAREN")
        self._expect("COLON")
        body = self._parse_body()
        return ir.ForEachStmt(table=table_arg, body=body, line=line)

    def _parse_return_stmt(self) -> ir.ReturnStmt:
        self._expect("IDENT", value="return")
        if self._peek().kind in ("STRING", "NUMBER", "IDENT", "VARIABLE"):
            val = self._parse_arg()
            return ir.ReturnStmt(value=val)
        return ir.ReturnStmt(value=None)

    # -- Action calls -------------------------------------------------------

    def _parse_action_call(self) -> ir.ActionStmt:
        line = self._peek().line
        name = scope_var_name(self._expect("IDENT").value)
        # Resolve to canonical action name
        try:
            canonical = M.resolve_action(name)
        except KeyError:
            canonical = name  # let emitter handle error
        name = canonical
        self._expect("LPAREN")
        args: list[ir.Arg] = []
        if not self._match("RPAREN"):
            args.append(self._parse_arg())
            while self._match("COMMA"):
                args.append(self._parse_arg())
            self._expect("RPAREN")
        return ir.ActionStmt(name=name, args=args, line=line)

    # -- Argument parsing ---------------------------------------------------

    def _parse_arg(self) -> ir.Arg:
        t = self._peek()
        if t.kind == "STRING":
            self._advance()
            val = t.value
            parts = self._detect_interpolation(val)
            if parts is not None:
                return ir.InterpolatedStr(parts)
            return ir.StrLit(val)
        if t.kind == "NUMBER":
            self._advance()
            return ir.NumLit(t.value)
        if t.kind == "VARIABLE":
            self._advance()
            return ir.VarRef(scope_var_name(t.value))
        if t.kind == "IDENT":
            self._advance()
            # Dotted path (page.Button.Name) → ObjectRef for UI linker
            if "." in t.value:
                return ir.ObjectRef(t.value)
            return ir.VarRef(scope_var_name(t.value))
        if t.kind == "BLOCK_OPEN":
            return self._parse_dict_literal()
        if t.kind == "LBRACKET":
            return self._parse_list_literal()
        # Check for math expression: primary (OP primary)*
        result = self._parse_math_primary()
        if result is not None:
            # Check if followed by an operator → math expression
            if self._peek().kind == "OP":
                tree = self._parse_math_expr(result)
                return ir.MathExpr(tree)
            return result
        raise ParseError(
            f"Expected argument (string, number, or identifier), "
            f"got {t.kind}={t.value!r} at line {t.line}")

    def _parse_math_primary(self) -> ir.Arg | None:
        """Parse a math primary: NUMBER, VARIABLE, or IDENT."""
        t = self._peek()
        if t.kind == "NUMBER":
            self._advance()
            return ir.NumLit(t.value)
        if t.kind == "VARIABLE":
            self._advance()
            return ir.VarRef(scope_var_name(t.value))
        if t.kind == "IDENT":
            self._advance()
            # Dotted path (page.Button.Name) → ObjectRef for UI linker
            if "." in t.value:
                return ir.ObjectRef(t.value)
            return ir.VarRef(scope_var_name(t.value))
        return None

    def _parse_math_expr(self, left: ir.Arg) -> "ir.MathNode":
        """Parse the rest of a math expression: (OP primary)* → binop tree."""
        # Convert the left arg to a MathNode
        left_node = self._arg_to_math_node(left)

        while self._peek().kind == "OP":
            op = self._advance().value
            right_primary = self._parse_math_primary()
            if right_primary is None:
                raise ParseError(
                    f"Expected number or variable after '{op}', "
                    f"got {self._peek().value!r}")
            right_node = self._arg_to_math_node(right_primary)
            left_node = ir.BinOp(left=left_node, op=op, right=right_node)

        return left_node

    def _arg_to_math_node(self, arg: ir.Arg) -> "ir.MathNode":
        """Convert an Arg to a MathNode for expression parsing."""
        if isinstance(arg, ir.NumLit):
            return ir.MathNum(arg.value)
        if isinstance(arg, ir.VarRef):
            return ir.MathVarRef(arg.name)
        raise ParseError(f"Cannot use {type(arg).__name__} in math expression")

    def _render_arg_to_str(self, arg: ir.Arg) -> str:
        if isinstance(arg, ir.StrLit):
            return arg.value
        if isinstance(arg, ir.NumLit):
            return arg.value
        if isinstance(arg, ir.VarRef):
            return "{" + arg.name + "}"
        if isinstance(arg, ir.InterpolatedStr):
            return self._render_arg_to_str(arg.parts[0]) if arg.parts else ""
        return str(arg)

    def _parse_dict_literal(self) -> ir.DictLiteral:
        """Parse ``{key: value, ...}``."""
        self._expect("BLOCK_OPEN")
        entries: list = []
        if self._peek().kind != "BLOCK_CLOSE":
            while True:
                key = self._parse_arg()
                self._expect("COLON")
                value = self._parse_arg()
                entries.append(ir.KVPair(key=key, value=value))
                if not self._match("COMMA"):
                    break
        self._expect("BLOCK_CLOSE")
        return ir.DictLiteral(entries=entries)

    def _parse_list_literal(self) -> ir.ListLiteral:
        """Parse ``[item, ...]``."""
        self._expect("LBRACKET")
        items = []
        if self._peek().kind != "RBRACKET":
            while True:
                items.append(self._parse_arg())
                if not self._match("COMMA"):
                    break
        self._expect("RBRACKET")
        return ir.ListLiteral(items=items)

    def _detect_interpolation(self, val: str) -> list[ir.StrLit | ir.VarRef] | None:
        """Check if a string literal contains ``{varname}`` interpolation.

        Returns a list of parts (StrLit | VarRef) if interpolation found,
        or None for a plain string.
        """
        import re
        parts: list[ir.StrLit | ir.VarRef] = []
        last = 0
        found = False
        for m in re.finditer(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", val):
            found = True
            # Text before the {var}
            if m.start() > last:
                parts.append(ir.StrLit(val[last:m.start()]))
            # The variable reference
            parts.append(ir.VarRef(scope_var_name(m.group(1))))
            last = m.end()
        if not found:
            return None
        # Trailing text
        if last < len(val):
            parts.append(ir.StrLit(val[last:]))
        return parts


def parse(source: str) -> ir.Program:
    """Parse Catpile source code into an IR Program.

    Args:
        source: Catpile source text.
    """
    tokens = tokenize(source)
    return Parser(tokens).parse()
