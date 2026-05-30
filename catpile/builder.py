"""Catpile project builder - compiles .cat files into CatWeb page JSON.

A Catpile project is defined in ``.catpilerc``:

.. code-block:: json

    {
        \"project\": \"my-app\",
        \"taste\": \"indent\",
        \"default_scope\": \"local\",
        \"pages\": [
            {
                \"name\": \"main\",
                \"ui\": \"ui/main.catui\",
                \"scripts\": [\"src/main.cat\", \"src/utils.cat\"],
                \"output\": \"build/main.json\"
            }
        ]
    }

Usage::

    cpile build            # Build all pages from .catpilerc
    cpile build --page main  # Build a single page
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk up from *start* looking for ``.catpilerc``."""
    start = start or Path.cwd()
    for parent in [start] + list(start.parents):
        cfg = parent / ".catpilerc"
        if cfg.exists():
            return parent
    return None


def load_project(root: Path) -> dict:
    """Load project config from ``.catpilerc`` in *root*."""
    cfg_path = root / ".catpilerc"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No .catpilerc found in {root}")
    cfg = json.loads(cfg_path.read_text())
    if "pages" not in cfg:
        raise ValueError(".catpilerc must have a 'pages' array")
    return cfg


def _reconstruct_from_structure(
    structure: list[dict],
    compiled_scripts: dict[str, dict],
) -> list[dict]:
    """Walk structure tree, replacing script markers with compiled script JSON.

    Script markers look like ``{"class": "script", "alias": "..."}`` and are
    produced by the decompiler's ``_strip_scripts``. This function replaces
    them with the fully compiled script dicts, preserving the original
    order and nesting of UI elements and scripts.
    """
    result: list[dict] = []
    for el in structure:
        if el.get("class") == "script":
            alias = el.get("alias", "")
            compiled = compiled_scripts.get(alias)
            if compiled is not None:
                script_copy = dict(compiled)
                # Preserve any nested scripts or elements as children
                child_structure = el.get("children", [])
                if child_structure:
                    compiled_children = _reconstruct_from_structure(
                        child_structure, compiled_scripts
                    )
                    if compiled_children:
                        script_copy["children"] = compiled_children
                result.append(script_copy)
            else:
                # Preserve marker as-is if no compiled script found
                result.append(dict(el))
            continue
        el_copy = dict(el)
        children = el.get("children", [])
        if children:
            el_copy["children"] = _reconstruct_from_structure(
                children, compiled_scripts
            )
        result.append(el_copy)
    return result


def build_page(page_cfg: dict, project_root: Path,
               taste_name: str, default_scope: str = "local",
               optimize: int = 0, clean: bool = True) -> str:
    """Build a single page: compile scripts → link UI → emit JSON.

    Args:
        page_cfg: Page config dict with ``ui``, ``scripts``, ``output``.
        project_root: Project root directory (for resolving relative paths).
        taste_name: Syntax variant name.
        default_scope: Default variable scope.
        optimize: Optimization level (0-3).
        clean: Whether to clean labels in output.

    Returns:
        Compiled CatWeb page JSON string.
    """
    from .tastes.registry import get_taste
    from .emitter import Emitter
    from .optimizer import Optimizer
    from .ir import Program

    taste = get_taste(taste_name, config={"default_scope": default_scope})
    merged = Program()

    # Compile each script
    for script_rel in page_cfg.get("scripts", []):
        script_path = (project_root / script_rel).resolve()
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        source = script_path.read_text()
        prog = taste.compile(source)
        merged.scripts.extend(prog.scripts)

    # Optimize
    if optimize:
        opt = Optimizer(merged, level=optimize)
        merged = opt.run()

    # Link UI elements
    ui_rel = page_cfg.get("ui", "")
    catui_data: dict[str, Any] = {}
    if ui_rel:
        ui_path = (project_root / ui_rel).resolve()
        if ui_path.exists():
            from .ui import UILinker
            linker = UILinker(ui_path)
            linker.link(merged)
            catui_data = json.loads(ui_path.read_text())

    # Emit
    emitter = Emitter(clean=clean)
    script_json = json.loads(emitter.emit(merged))

    # Build script map by alias
    script_map: dict[str, dict] = {}
    for s in script_json:
        alias = s.get("alias", "")
        if alias:
            script_map[alias] = s

    # Reconstruct full page from stored structure or fall back to concatenation
    structure = catui_data.get("ui", [])
    metadata = catui_data.get("metadata", {})

    if structure:
        page_json = _reconstruct_from_structure(structure, script_map)
    else:
        # Fallback: flat concatenation (for older .catui without markers)
        ui_elements = [el for el in structure if el.get("class") != "script"] if structure else []
        page_json = ui_elements + script_json

    # Re-wrap with metadata if present (e.g. {"background": "#202020", ...})
    if metadata:
        result = dict(metadata)
        result["webcontent"] = page_json
        return json.dumps(result, indent=2)

    return json.dumps(page_json, indent=2)


def build_project(project_root: Path | str,
                  page_filter: str | None = None,
                  optimize: int = 0,
                  clean: bool = True) -> list[Path]:
    """Build all (or one) pages in the project.

    Args:
        project_root: Project root with .catpilerc.
        page_filter: Optional page name to build (None = all).
        optimize: Optimization level.
        clean: Clean labels.

    Returns:
        List of output file paths written.
    """
    root = Path(project_root)
    cfg = load_project(root)
    taste = cfg.get("taste", "indent")
    scope = cfg.get("default_scope", "local")

    written: list[Path] = []
    for page in cfg.get("pages", []):
        name = page.get("name", "")
        if page_filter and name != page_filter:
            continue

        output_rel = page.get("output", f"build/{name}.json")
        output_path = (root / output_rel).resolve()

        print(f"  building {name}... ", end="", flush=True)
        try:
            result = build_page(page, root, taste, scope, optimize, clean)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result)
            print(f"wrote {output_path}")
            written.append(output_path)
        except Exception as e:
            print(f"error: {e}")

    return written
