from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from .catui_ir import (
    CatUIProgram,
    PageDef,
    UIElement,
    UIStylingElement,
    ScriptPlaceholder,
)


class TokenKind(Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    IDENT = "IDENT"
    ASSIGN = "ASSIGN"
    COLON = "COLON"
    COMMA = "COMMA"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    KEYWORD = "KEYWORD"
    EOF = "EOF"


class Token:
    __slots__ = ("kind", "value", "line", "col")

    def __init__(self, kind: TokenKind, value: str = "", line: int = 0, col: int = 0) -> None:
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, L{self.line}:{self.col})"


class CatUIError(Exception):
    pass


_KEYWORD_SET = {"page"}


def tokenize(source: str) -> list[Token]:
    lines = source.split("\n")
    tokens: list[Token] = []
    indent_stack: list[int] = [0]

    for line_no, raw in enumerate(lines, 1):
        raw_stripped = raw.rstrip("\r")

        # Strip trailing whitespace, keep leading for indent calc
        stripped = raw_stripped.rstrip()
        if stripped and not stripped.strip():
            continue

        # Compute indent level
        leading = len(raw_stripped) - len(raw_stripped.lstrip())
        content = raw_stripped.strip()

        # Skip blank lines and comments
        if not content or content.startswith("#"):
            if indent_stack[-1] != leading and content:
                pass
            continue

        # Emit INDENT/DEDENT based on indent level
        if leading > indent_stack[-1]:
            indent_stack.append(leading)
            tokens.append(Token(TokenKind.INDENT, "", line_no, leading))
        elif leading < indent_stack[-1]:
            while indent_stack and leading < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(Token(TokenKind.DEDENT, "", line_no, 0))
            if indent_stack and leading != indent_stack[-1]:
                raise CatUIError(
                    f"Indentation mismatch at line {line_no}: "
                    f"expected indent {indent_stack[-1]}, got {leading}"
                )

        # Tokenize the line content
        i = 0
        while i < len(content):
            c = content[i]

            # Skip whitespace within line
            if c in " \t":
                i += 1
                continue

            # Double-quoted string
            if c == '"':
                i += 1
                start = i
                while i < len(content) and content[i] != '"':
                    if content[i] == "\\":
                        i += 1
                    i += 1
                if i >= len(content):
                    raise CatUIError(f"Unterminated string at line {line_no}")
                val = content[start:i]
                tokens.append(Token(TokenKind.STRING, val, line_no, i))
                i += 1
                continue

            # Single-quoted string
            if c == "'":
                i += 1
                start = i
                while i < len(content) and content[i] != "'":
                    if content[i] == "\\":
                        i += 1
                    i += 1
                if i >= len(content):
                    raise CatUIError(f"Unterminated string at line {line_no}")
                val = content[start:i]
                tokens.append(Token(TokenKind.STRING, val, line_no, i))
                i += 1
                continue

            # Operators and punctuation
            if c == "=":
                tokens.append(Token(TokenKind.ASSIGN, "=", line_no, i))
                i += 1
                continue
            if c == ":":
                tokens.append(Token(TokenKind.COLON, ":", line_no, i))
                i += 1
                continue
            if c == ",":
                tokens.append(Token(TokenKind.COMMA, ",", line_no, i))
                i += 1
                continue
            if c == "[":
                tokens.append(Token(TokenKind.LBRACKET, "[", line_no, i))
                i += 1
                continue
            if c == "]":
                tokens.append(Token(TokenKind.RBRACKET, "]", line_no, i))
                i += 1
                continue

            # Number (integer or float)
            if c.isdigit() or (c == "." and i + 1 < len(content) and content[i + 1].isdigit()):
                start = i
                has_dot = False
                while i < len(content) and (content[i].isdigit() or (content[i] == "." and not has_dot)):
                    if content[i] == ".":
                        has_dot = True
                    i += 1
                tokens.append(Token(TokenKind.NUMBER, content[start:i], line_no, start))
                continue

            # Identifier or keyword
            if c.isalpha() or c == "_":
                start = i
                while i < len(content) and (content[i].isalnum() or content[i] == "_" or content[i] == "?"):
                    i += 1
                word = content[start:i]
                if word in _KEYWORD_SET:
                    tokens.append(Token(TokenKind.KEYWORD, word, line_no, start))
                else:
                    tokens.append(Token(TokenKind.IDENT, word, line_no, start))
                continue

            raise CatUIError(f"Unexpected character {c!r} at line {line_no}, col {i}")

    # Close remaining indentation
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token(TokenKind.DEDENT, "", len(lines), 0))

    tokens.append(Token(TokenKind.EOF, "", len(lines), 0))
    return tokens


_ELEMENT_CLASS_NAMES = {
    "frame", "scrollingframe", "scrollframe",
    "textlabel", "label", "textbutton", "button", "textbox", "input",
    "imagelabel", "image",
    "link", "donation", "transfer", "avataritem",
    "folder",
    "script",
    "uicorner", "corner", "uistroke", "stroke",
    "uigradient", "gradient", "uipadding", "padding",
    "uilistlayout", "listlayout", "uigridlayout", "gridlayout",
    "uiaspectratioconstraint", "aspectratioconstraint",
    "uisizeconstraint", "sizeconstraint",
    "uitextsizeconstraint", "textsizeconstraint",
}


def _is_element_class(name: str) -> bool:
    return name.lower() in _ELEMENT_CLASS_NAMES


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: TokenKind, value: str | None = None) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise CatUIError(
                f"Expected {kind.value}, got {tok.kind.value} ({tok.value!r}) "
                f"at line {tok.line}"
            )
        if value is not None and tok.value != value:
            raise CatUIError(
                f"Expected {value!r}, got {tok.value!r} at line {tok.line}"
            )
        return self.advance()

    def skip_if(self, kind: TokenKind, value: str | None = None) -> bool:
        tok = self.peek()
        if tok.kind == kind and (value is None or tok.value == value):
            self.advance()
            return True
        return False

    def parse(self) -> CatUIProgram:
        prog = CatUIProgram()

        if self.skip_if(TokenKind.KEYWORD, "page"):
            name_tok = self.expect(TokenKind.STRING)
            self.expect(TokenKind.COLON)
            self.expect(TokenKind.INDENT)
            properties, children = self._parse_body()
            self.expect(TokenKind.DEDENT)
            page_el = UIElement(
                class_name="Page",
                alias=name_tok.value,
                properties=properties,
                children=children,
            )
            prog.pages.append(PageDef(name=name_tok.value, element=page_el))
        else:
            properties, children = self._parse_body()
            if children:
                page_el = UIElement(
                    class_name="Page",
                    alias="",
                    properties=properties,
                    children=children,
                )
                prog.pages.append(PageDef(name="", element=page_el))

        return prog

    def _parse_body(self) -> tuple[dict[str, str], list[UIElement | ScriptPlaceholder | UIStylingElement]]:
        """Parse properties and child elements from current position until DEDENT or EOF."""
        properties: dict[str, str] = {}
        children: list[UIElement | ScriptPlaceholder | UIStylingElement] = []
        while self.peek().kind not in (TokenKind.DEDENT, TokenKind.EOF):
            if self._is_property():
                key, val = self._parse_property()
                properties[key] = val
            else:
                child = self._parse_element()
                children.append(child)
        return properties, children

    def _parse_element(self) -> UIElement | ScriptPlaceholder:
        class_tok = self.expect(TokenKind.IDENT)
        alias_tok = self.expect(TokenKind.IDENT)

        class_name = class_tok.value
        alias = alias_tok.value

        globalid: str | None = None
        annotations: dict[str, str] = {}
        if self.skip_if(TokenKind.LBRACKET):
            while self.peek().kind != TokenKind.RBRACKET:
                key_tok = self.expect(TokenKind.IDENT)
                self.expect(TokenKind.COLON)
                val_tok = self.peek()
                if val_tok.kind in (TokenKind.STRING, TokenKind.NUMBER):
                    self.advance()
                    annotations[key_tok.value] = val_tok.value
                else:
                    raise CatUIError(
                        f"Expected string or number in annotation at line {val_tok.line}"
                    )
                self.skip_if(TokenKind.COMMA)
            self.expect(TokenKind.RBRACKET)

        if "globalid" in annotations:
            globalid = annotations["globalid"]
            del annotations["globalid"]

        self.expect(TokenKind.COLON)

        properties: dict[str, str] = {}
        children: list[UIElement | ScriptPlaceholder | UIStylingElement] = []

        if self.peek().kind == TokenKind.INDENT:
            self.advance()
            properties, children = self._parse_body()
            if self.peek().kind == TokenKind.DEDENT:
                self.advance()
        elif self.peek().kind == TokenKind.IDENT and self._is_property():
            key, val = self._parse_property()
            properties[key] = val

        if class_name.lower() == "script":
            source = properties.pop("source", None)
            enabled = properties.pop("enabled", "true")
            return ScriptPlaceholder(
                alias=alias,
                source=source,
                enabled=enabled,
            )

        # Determine if this is a styling element
        styling_prefixes = {"ui", "uicorner", "uistroke", "uigradient",
                           "uipadding", "uilistlayout", "uigridlayout",
                           "uiaspectratioconstraint", "uisizeconstraint",
                           "uitextsizeconstraint"}
        is_styling = class_name.lower() in styling_prefixes or (
            class_name.lower() in ("corner", "stroke", "gradient", "padding",
                                  "listlayout", "gridlayout",
                                  "aspectratioconstraint", "sizeconstraint",
                                  "textsizeconstraint")
        )

        if is_styling:
            return UIStylingElement(
                class_name=class_name,
                alias=alias,
                properties=properties,
            )

        return UIElement(
            class_name=class_name,
            alias=alias,
            globalid=globalid,
            properties=properties,
            children=children,
        )

    def _is_property(self) -> bool:
        if self.peek().kind != TokenKind.IDENT:
            return False
        saved = self.pos
        try:
            self.advance()
            return self.peek().kind == TokenKind.ASSIGN
        finally:
            self.pos = saved

    def _parse_property(self) -> tuple[str, str]:
        key_tok = self.expect(TokenKind.IDENT)
        self.expect(TokenKind.ASSIGN)
        val_tok = self.peek()
        if val_tok.kind == TokenKind.STRING:
            self.advance()
            return key_tok.value, val_tok.value
        if val_tok.kind == TokenKind.NUMBER:
            self.advance()
            return key_tok.value, val_tok.value
        if val_tok.kind == TokenKind.IDENT:
            self.advance()
            return key_tok.value, val_tok.value
        raise CatUIError(
            f"Expected string, number, or identifier after '=', "
            f"got {val_tok.kind.value} at line {val_tok.line}"
        )


def parse_catui(source: str) -> CatUIProgram:
    """Parse CatUI DSL source text into a CatUIProgram AST."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse()



