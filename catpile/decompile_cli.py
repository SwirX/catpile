#!/usr/bin/env python3
"""Catpile Decompiler - standalone JSON → .cat decompiler for the editor.

Usage:
    cpile-decompile page.json -o output-dir/

Takes a CatWeb page export JSON, splits it into:
  - One .cat file per script (aliased or indexed)
  - One .catui file with UI hierarchy and path mappings
  - One .json file with the original UI elements (scripts removed)
"""

import argparse
import json
import sys
from pathlib import Path

from .decompiler import decompile_page


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Catpile Decompiler - CatWeb JSON → .cat source + .catui hierarchy",
    )
    parser.add_argument("input", type=Path,
                        help="CatWeb page export JSON file")
    parser.add_argument("-o", "--output-dir", type=Path, default=None,
                        help="Output directory (default: same as input)")

    args = parser.parse_args()

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


if __name__ == "__main__":
    main()
