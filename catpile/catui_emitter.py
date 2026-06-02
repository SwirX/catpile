from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catui_ir import CatUIProgram, PageDef, UIElement, UIStylingElement, ScriptPlaceholder
from .mappings import IDGen


def _load_ui_schema() -> dict[str, Any]:
    here = Path(__file__).parent
    schema_path = here / "ui_elements.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return {}


def _resolve_class_name(dsl_name: str, schema: dict) -> str:
    """Map DSL class name (e.g. 'button') to JSON class name (e.g. 'TextButton')."""
    aliases = schema.get("element_aliases", {})
    return aliases.get(dsl_name.lower(), dsl_name)


def _resolve_property_name(dsl_key: str, schema: dict) -> str:
    """Map DSL property alias (e.g. 'bg') to JSON property name (e.g. 'background_color')."""
    aliases = schema.get("property_aliases", {})
    return aliases.get(dsl_key, dsl_key)


DEFAULT_PAGE_METADATA: dict[str, str] = {
    "description": "",
    "title": "",
    "background": "",
}


class CatUIEmitter:
    def __init__(self, clean: bool = True) -> None:
        self.idgen = IDGen()
        self.schema = _load_ui_schema()
        self.clean = clean

    def emit(self, program: CatUIProgram) -> str:
        pages_json: list = []
        for page in program.pages:
            if page.element:
                pages_json.append(self._emit_page(page.element))
        if len(pages_json) == 1:
            return json.dumps(pages_json[0], indent=2)
        return json.dumps(pages_json, indent=2)

    def _emit_page(self, page_el: UIElement) -> dict:
        """Emit a page element: properties→metadata, children→webcontent array."""
        children_json = [self._emit_element(c) for c in page_el.children]
        result = dict(DEFAULT_PAGE_METADATA)
        result.update(page_el.properties)
        result["webcontent"] = children_json
        return result

    def _emit_element(self, el: UIElement | ScriptPlaceholder | UIStylingElement) -> dict:
        if isinstance(el, ScriptPlaceholder):
            return self._emit_script_marker(el)
        if isinstance(el, UIStylingElement):
            return self._emit_styling(el)

        class_name = _resolve_class_name(el.class_name, self.schema)
        globalid = el.globalid or self.idgen.next()

        obj: dict[str, Any] = {
            "class": class_name,
            "globalid": globalid,
        }

        if el.alias:
            obj["alias"] = el.alias

        for dsl_key, value in el.properties.items():
            json_key = _resolve_property_name(dsl_key, self.schema)
            obj[json_key] = value

        children: list[dict] = []
        for child in el.children:
            child_json = self._emit_element(child)
            children.append(child_json)

        if children:
            obj["children"] = children

        return obj

    def _emit_script_marker(self, script: ScriptPlaceholder) -> dict:
        marker: dict[str, Any] = {
            "class": "script",
            "alias": script.alias,
        }
        if script.enabled != "true":
            marker["enabled"] = script.enabled
        return marker

    def _emit_styling(self, el: UIStylingElement) -> dict:
        class_name = _resolve_class_name(el.class_name, self.schema)
        obj: dict[str, Any] = {
            "class": class_name,
            "globalid": self.idgen.next(),
        }

        for dsl_key, value in el.properties.items():
            json_key = _resolve_property_name(dsl_key, self.schema)
            obj[json_key] = value

        return obj


def emit_catui(program: CatUIProgram, clean: bool = True) -> str:
    """Emit a CatUIProgram as CatWeb UI JSON."""
    emitter = CatUIEmitter(clean=clean)
    return emitter.emit(program)
