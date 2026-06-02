from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass
class UIStylingElement:
    class_name: str
    alias: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class ScriptPlaceholder:
    alias: str
    source: str | None = None
    enabled: str = "true"


@dataclass
class UIElement:
    class_name: str
    alias: str
    globalid: str | None = None
    properties: dict[str, str] = field(default_factory=dict)
    children: list[Union[UIElement, ScriptPlaceholder, UIStylingElement]] = field(default_factory=list)


@dataclass
class PageDef:
    name: str
    element: UIElement | None = None
    """The page root element (class="Page"). Its children are the top-level UI elements,
    and its properties are page-level metadata (background, title, description, etc.)."""


@dataclass
class CatUIProgram:
    pages: list[PageDef] = field(default_factory=list)


def build_gid_index(program: CatUIProgram) -> dict[str, str]:
    """Walk CatUI AST and build a name→globalID index.

    Indexes by alias and by dotted path (e.g. ``Page.root.title``).
    Returns a flat dict suitable for passing to ``UILinker``.
    """
    index: dict[str, str] = {}

    for page in program.pages:
        if page.element:
            for child in page.element.children:
                child_prefix = f"Page.{child.alias}" if child.alias else "Page"
                _walk_index(child, index, child_prefix)

    return index


def _walk_index(
    el: UIElement | ScriptPlaceholder | UIStylingElement,
    index: dict[str, str],
    prefix: str = "",
) -> None:
    if isinstance(el, ScriptPlaceholder):
        return
    if isinstance(el, UIStylingElement):
        return

    gid = el.globalid
    if gid:
        index[gid] = gid
        if el.alias:
            index[el.alias] = gid
        if prefix:
            index[prefix] = gid

    for child in el.children:
        child_prefix = f"{prefix}.{child.alias}" if child.alias and prefix else (child.alias or "")
        _walk_index(child, index, child_prefix)
