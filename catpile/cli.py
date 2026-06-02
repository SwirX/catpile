#!/usr/bin/env python3
"""Catpile CLI - compile SXS files to CatWeb JSON."""

import argparse
import json
import sys
from pathlib import Path

from .emitter import Emitter, EmitError
from .tastes.registry import get_taste, list_tastes
from .builder import find_project_root as _find_root


def _load_config(input_paths: list[Path]) -> dict:
    """Load the ``.catpilerc`` config file.

    Checks (in order):
      1. ``.catpilerc`` JSON file in the same directory as the first input
      2. ``.catpilerc`` in the current working directory

    Returns a dict (possibly empty).
    """
    dirs = set()
    for p in input_paths:
        if p.parent:
            dirs.add(p.parent.resolve())
    dirs.add(Path.cwd().resolve())

    for d in sorted(dirs):
        config_file = d / ".catpilerc"
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except (json.JSONDecodeError, OSError):
                print(f"Warning: could not parse {config_file}", file=sys.stderr)
    return {}


def _resolve_taste(args_taste: str | None, config: dict) -> str:
    """Resolve taste name: CLI flag > config file > ``\"indent\"``."""
    if args_taste:
        return args_taste
    taste = config.get("taste", "")
    if taste in list_tastes():
        return taste
    return "indent"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Catpile - Pythonic DSL → CatWeb JSON compiler",
    )
    sub = parser.add_subparsers(dest="command", help="Subcommands")

    # Version / update notices (non-blocking)
    try:
        from ._version_check import check_for_updates, _show_whats_new
        _show_whats_new()
        check_for_updates()
    except Exception:
        pass

    # --- build subcommand ---
    build_parser = sub.add_parser("build", help="Build CatWeb page from project config")
    build_parser.add_argument("--page", default=None,
                              help="Build a single page by name")
    build_parser.add_argument("-O", "--optimize", type=int, default=0,
                              choices=[0, 1, 2, 3],
                              help="Optimization level")
    build_parser.add_argument("--no-clean", action="store_true",
                              help="Disable label cleaning")

    # --- compile subcommand ---
    compile_parser = sub.add_parser("compile", help="Compile .cat or .catui files to JSON")
    compile_parser.add_argument("input", nargs="+", type=Path,
                                help=".cat or .catui input files")
    compile_parser.add_argument("-o", "--output", type=Path,
                                help="Output file (default: stdout)")
    compile_parser.add_argument("--minify", action="store_true",
                                help="Minify JSON output")
    compile_parser.add_argument("--taste", default=None,
                                choices=list_tastes(),
                                help="Syntax variant")
    compile_parser.add_argument("--no-clean", action="store_true",
                                help="Disable label cleaning")
    compile_parser.add_argument("--ui", type=Path, default=None,
                                help="CatWeb UI JSON file for element resolution")

    # --- decompile subcommand ---
    decompile_parser = sub.add_parser("decompile",
                                      help="Decompile CatWeb JSON → .cat + .catui")
    decompile_parser.add_argument("input", type=Path,
                                  help="CatWeb page JSON file")
    decompile_parser.add_argument("-o", "--output-dir", type=Path, default=None,
                                  help="Output directory (default: same as input)")

    # --- catui subcommand ---
    catui_parser = sub.add_parser("catui",
                                  help="Extract CatUI DSL from page JSON")
    catui_parser.add_argument("input", type=Path,
                              help="CatWeb page JSON file")
    catui_parser.add_argument("-o", "--output", type=Path, default=None,
                              help="Output .catui file (default: stdout)")

    # --- migrate subcommand ---
    migrate_parser = sub.add_parser("migrate",
                                    help="Migrate old JSON-format .catui to new DSL format")
    migrate_parser.add_argument("input", type=Path,
                                help="Old JSON-format .catui file")
    migrate_parser.add_argument("-o", "--output", type=Path, default=None,
                                help="Output .catui file (default: same path, overwrite)")

    args = parser.parse_args()

    # --- build mode ---
    if args.command == "build":
        root = _find_root()
        if not root:
            print("Error: no .catpilerc found in current or parent directories",
                  file=sys.stderr)
            sys.exit(1)
        from .builder import build_project
        written = build_project(
            root,
            page_filter=args.page,
            optimize=args.optimize,
            clean=not args.no_clean,
        )
        if written:
            print(f"Built {len(written)} page(s)")
        return

    # --- decompile mode ---
    if args.command == "decompile":
        from .decompiler import decompile_page
        if not args.input.exists():
            print(f"Error: {args.input} not found", file=sys.stderr)
            sys.exit(1)
        data = json.loads(args.input.read_text())
        out_dir = args.output_dir or args.input.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = decompile_page(data, args.input.stem)
        if not outputs:
            print("  (no scripts or UI elements found)")
            return
        for name, content in outputs.items():
            out_path = out_dir / name
            out_path.write_text(content)
            print(f"  wrote {out_path}")
        return

    # --- catui mode ---
    if args.command == "catui":
        from .decompiler import decompile_ui_to_catui
        if not args.input.exists():
            print(f"Error: {args.input} not found", file=sys.stderr)
            sys.exit(1)
        data = json.loads(args.input.read_text())
        # Handle metadata wrapper
        page_json = data.get("webcontent", data) if isinstance(data, dict) else data
        if not isinstance(page_json, list):
            page_json = [page_json]
        result = decompile_ui_to_catui(page_json)
        if args.output:
            args.output.write_text(result)
            print(f"Written to {args.output}")
        else:
            print(result, end="")
        return

    # --- migrate mode ---
    if args.command == "migrate":
        from .decompiler import decompile_ui_to_catui
        if not args.input.exists():
            print(f"Error: {args.input} not found", file=sys.stderr)
            sys.exit(1)
        raw = args.input.read_text()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Already new DSL format
            print(f"Error: {args.input} is already in new DSL format", file=sys.stderr)
            sys.exit(1)
        if isinstance(data, dict):
            ui_elements = data.get("ui", [])
            metadata = data.get("metadata", {})
        elif isinstance(data, list):
            ui_elements = data
            metadata = {}
        else:
            print(f"Error: unrecognized format in {args.input}", file=sys.stderr)
            sys.exit(1)
        if not ui_elements:
            print(f"Error: no UI elements found in {args.input}", file=sys.stderr)
            sys.exit(1)
        dsl = decompile_ui_to_catui(ui_elements, metadata=metadata)
        out_path = args.output or args.input
        out_path.write_text(dsl)
        print(f"Migrated to {out_path}")
        return

    # --- compile mode ---
    if not getattr(args, "input", None):
        parser.print_help()
        sys.exit(1)

    # Load config file
    config = _load_config(args.input)

    # Resolve taste: CLI flag > config file > default
    taste_name = _resolve_taste(args.taste, config)

    # Instantiate the taste with config
    try:
        taste = get_taste(taste_name, config=config)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Read and compile each input file
    from .ir import Program
    merged = Program()
    catui_outputs: list[str] = []
    has_catui = False

    for path in args.input:
        if not path.exists():
            print(f"Error: {path} not found", file=sys.stderr)
            sys.exit(1)
        try:
            if path.suffix.lower() == ".catui":
                has_catui = True
                from .catui_parser import parse_catui
                from .catui_emitter import emit_catui
                source = path.read_text()
                prog = parse_catui(source)
                catui_outputs.append(emit_catui(prog))
            else:
                source = path.read_text()
                prog = taste.compile(source)
                merged.scripts.extend(prog.scripts)
        except (SyntaxError, Exception) as e:
            print(f"Error in {path}: {e}", file=sys.stderr)
            sys.exit(1)

    # If only .catui files were given, output the emitted UI JSON
    if has_catui and not merged.scripts:
        indent = None if args.minify else 2
        output = json.dumps(
            json.loads(catui_outputs[0]) if len(catui_outputs) == 1
            else [json.loads(o) for o in catui_outputs],
            indent=indent,
        )
        if args.output:
            args.output.write_text(output)
            print(f"Written to {args.output}")
        else:
            print(output)
        return

    # Optimize
    if args.optimize:
        from .optimizer import Optimizer
        opt = Optimizer(merged, level=args.optimize)
        merged = opt.run()
        print(opt.report(), file=sys.stderr)

    # Resolve UI element references
    if args.ui:
        if not args.ui.exists():
            print(f"Error: UI file {args.ui} not found", file=sys.stderr)
            sys.exit(1)
        from .ui import UILinker
        linker = UILinker(args.ui)
        resolved = linker.link(merged)
        print(linker.report(), file=sys.stderr)

    # Emit
    try:
        emitter = Emitter(clean=not args.no_clean)
        result = emitter.emit(merged)
    except EmitError as e:
        print(f"Emit error: {e}", file=sys.stderr)
        sys.exit(1)

    indent = None if args.minify else 2
    output = json.dumps(json.loads(result), indent=indent)

    if args.output:
        args.output.write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
