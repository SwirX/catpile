from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catui_ir import CatUIProgram, UIElement, ScriptPlaceholder, UIStylingElement, build_gid_index


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
    """Walk structure tree, replacing script markers with compiled script JSON."""
    result: list[dict] = []
    for el in structure:
        if el.get("class") == "script":
            alias = el.get("alias", "")
            compiled = compiled_scripts.get(alias)
            if compiled is not None:
                script_copy = dict(compiled)
                child_structure = el.get("children", [])
                if child_structure:
                    compiled_children = _reconstruct_from_structure(
                        child_structure, compiled_scripts
                    )
                    if compiled_children:
                        script_copy["children"] = compiled_children
                result.append(script_copy)
            else:
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


def _collect_scripts_from_ui_elements(elements: list[dict]) -> list[dict]:
    """Recursively find all script markers in a UI JSON structure."""
    found: list[dict] = []
    for el in elements:
        if el.get("class") == "script":
            found.append(el)
        children = el.get("children", [])
        if children:
            found.extend(_collect_scripts_from_ui_elements(children))
    return found


def _collect_scripts_from_prog(program: CatUIProgram) -> dict[str, str]:
    """Walk CatUI AST and return {alias: source_path} for all ScriptPlaceholders."""
    scripts: dict[str, str] = {}
    for page in program.pages:
        if page.element:
            _walk_scripts(page.element, scripts)
    return scripts


def _walk_scripts(
    el: UIElement | ScriptPlaceholder | UIStylingElement,
    scripts: dict[str, str],
) -> None:
    if isinstance(el, ScriptPlaceholder):
        if el.source:
            scripts[el.alias] = el.source
        return
    if isinstance(el, UIElement):
        for child in el.children:
            _walk_scripts(child, scripts)


def _detect_catui_format(content: str) -> tuple[bool, Any]:
    """Detect if a .catui file is JSON (old, deprecated) or DSL (new) format.

    Returns (is_dsl, parsed_data) where parsed_data is None for DSL
    or the parsed JSON data for old format.
    """
    try:
        data = json.loads(content)
        import sys
        print(
            "Warning: JSON-format .catui files are deprecated and will be removed in a future release. "
            "Run 'cpile migrate <file>.catui' to convert to the new DSL format.",
            file=sys.stderr,
        )
        return False, data
    except (json.JSONDecodeError, ValueError):
        return True, None


def build_page(
    page_cfg: dict,
    project_root: Path,
    taste_name: str,
    optimize: int = 0,
    clean: bool = True,
) -> str:
    """Build a single page from CatUI + CatLang sources.

    Supports two formats:

    **New format** (``catui`` key):
    .. code-block:: json

        {"name": "main", "catui": "ui/main.catui", "output": "build/main.json"}

    Scripts are discovered from ``script`` elements in the .catui file.

    **Old format** (``ui`` + ``scripts`` keys):
    .. code-block:: json

        {"name": "main", "ui": "ui/main.catui", "scripts": ["src/main.cat"], "output": "build/main.json"}
    """
    from .tastes.registry import get_taste
    from .emitter import Emitter
    from .optimizer import Optimizer
    from .ir import Program
    from .catui_emitter import emit_catui
    from .catui_parser import parse_catui
    from .ui import UILinker

    catui_rel = page_cfg.get("catui") or page_cfg.get("ui", "")
    structure: list[dict] = []
    metadata: dict[str, Any] = {}
    script_map: dict[str, dict] = {}

    if catui_rel:
        catui_path = (project_root / catui_rel).resolve()
        if catui_path.exists():
            raw = catui_path.read_text()
            is_dsl, json_data = _detect_catui_format(raw)

            if is_dsl:
                structure, script_map, meta = _build_from_dsl(
                    raw, project_root, taste_name, optimize, clean
                )
                metadata.update(meta)
            else:
                structure, script_map, metadata = _build_from_json(
                    json_data, page_cfg, catui_path, project_root,
                    taste_name, optimize, clean
                )
    else:
        # No .catui at all — compile scripts directly as the page content
        taste = get_taste(taste_name, config={})
        merged = Program()
        for script_rel in page_cfg.get("scripts", []):
            script_path = (project_root / script_rel).resolve()
            if not script_path.exists():
                raise FileNotFoundError(f"Script not found: {script_path}")
            source = script_path.read_text()
            prog = taste.compile(source)
            merged.scripts.extend(prog.scripts)
        if optimize:
            opt = Optimizer(merged, level=optimize)
            merged = opt.run()
        emitter = Emitter(clean=clean)
        script_map = {
            s.get("alias", ""): s
            for s in json.loads(emitter.emit(merged))
            if s.get("alias")
        }

    if structure:
        page_json = _reconstruct_from_structure(structure, script_map)
    else:
        page_json = list(script_map.values())

    from .catui_emitter import DEFAULT_PAGE_METADATA
    full_metadata = dict(DEFAULT_PAGE_METADATA)
    full_metadata.update(metadata)
    full_metadata["webcontent"] = page_json
    return json.dumps(full_metadata, indent=2)


def _build_from_dsl(
    dsl_source: str,
    project_root: Path,
    taste_name: str,
    optimize: int,
    clean: bool,
) -> tuple[list[dict], dict[str, dict], dict[str, Any]]:
    """Build page from CatUI DSL source."""
    from .tastes.registry import get_taste
    from .emitter import Emitter
    from .optimizer import Optimizer
    from .ir import Program
    from .catui_emitter import emit_catui
    from .catui_parser import parse_catui
    from .ui import UILinker

    catui_prog = parse_catui(dsl_source)
    scripts = _collect_scripts_from_prog(catui_prog)

    taste = get_taste(taste_name, config={})
    merged = Program()
    for alias, source_rel in scripts.items():
        script_path = (project_root / source_rel).resolve()
        if not script_path.exists():
            raise FileNotFoundError(
                f"Script {source_rel!r} (referenced by {alias!r}) not found: {script_path}"
            )
        source = script_path.read_text()
        prog = taste.compile(source)
        merged.scripts.extend(prog.scripts)

    if optimize:
        opt = Optimizer(merged, level=optimize)
        merged = opt.run()

    gid_index = build_gid_index(catui_prog)
    if gid_index:
        linker = UILinker(gid_index)
        linker.link(merged)

    emitter = Emitter(clean=clean)
    script_map = {
        s.get("alias", ""): s
        for s in json.loads(emitter.emit(merged))
        if s.get("alias")
    }

    ui_json_str = emit_catui(catui_prog, clean=clean)
    raw_structure = json.loads(ui_json_str)
    page_metadata: dict[str, Any] = {}
    structure: list[dict] = []
    if isinstance(raw_structure, dict):
        page_metadata = {k: v for k, v in raw_structure.items() if k != "webcontent"}
        structure = raw_structure.get("webcontent", [])
    else:
        structure = raw_structure if isinstance(raw_structure, list) else [raw_structure]

    return structure, script_map, page_metadata


def _build_from_json(
    json_data: Any,
    page_cfg: dict,
    catui_path: Path,
    project_root: Path,
    taste_name: str,
    optimize: int,
    clean: bool,
) -> tuple[list[dict], dict[str, dict], dict[str, Any]]:
    """Build page from old-format .catui JSON."""
    from .tastes.registry import get_taste
    from .emitter import Emitter
    from .optimizer import Optimizer
    from .ir import Program
    from .ui import UILinker

    metadata: dict[str, Any] = {}
    structure: list[dict] = []
    if isinstance(json_data, dict):
        structure = json_data.get("ui", [])
        metadata = json_data.get("metadata", {})
    elif isinstance(json_data, list):
        structure = json_data

    taste = get_taste(taste_name, config={})
    merged = Program()
    for script_rel in page_cfg.get("scripts", []):
        script_path = (project_root / script_rel).resolve()
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        source = script_path.read_text()
        prog = taste.compile(source)
        merged.scripts.extend(prog.scripts)

    if optimize:
        opt = Optimizer(merged, level=optimize)
        merged = opt.run()

    linker = UILinker.from_file(catui_path)
    linker.link(merged)

    emitter = Emitter(clean=clean)
    script_map = {
        s.get("alias", ""): s
        for s in json.loads(emitter.emit(merged))
        if s.get("alias")
    }

    return structure, script_map, metadata


def build_project(
    project_root: Path | str,
    page_filter: str | None = None,
    optimize: int = 0,
    clean: bool = True,
) -> list[Path]:
    """Build all (or one) pages in the project."""
    root = Path(project_root)
    cfg = load_project(root)
    taste = cfg.get("taste", "indent")

    written: list[Path] = []
    for page in cfg.get("pages", []):
        name = page.get("name", "")
        if page_filter and name != page_filter:
            continue

        output_rel = page.get("output", f"build/{name}.json")
        output_path = (root / output_rel).resolve()

        print(f"  building {name}... ", end="", flush=True)
        try:
            result = build_page(page, root, taste, optimize, clean)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result)
            print(f"wrote {output_path}")
            written.append(output_path)
        except Exception as e:
            print(f"error: {e}")

    return written
