# CHANGELOG

## [1.1.0] - 2026-06-02 - CatUI DSL

### Added
- **CatUI DSL** — Declarative UI definition language (`.catui` files) for describing CatWeb UI element trees. Write `page "name":` blocks with element class names, aliases, annotations, properties, and nested children.
- **`cpile catui <page.json>` subcommand** — Decompile a CatWeb page export to CatUI DSL and `.cat` scripts in one command.
- **Page-level metadata in CatUI DSL** — Page properties (`background`, `title`, `description`) appear as inline properties in the `page` block and round-trip through compile/decompile.
- **23 UI element classes supported** — Frame, TextLabel, TextButton, TextBox, ImageLabel, ScrollingScrollFrame, TextButton?link, TextButton?transfer, TextButton?avataritem, Folder, UICorner, UIStroke, UIGradient, UIPadding, UIListLayout, UIGridLayout, UIAspectRatioConstraint, UISizeConstraint, UITextSizeConstraint, and more.
- **Property aliases** — Short names in DSL (`bg` → `background_color`, `corner` → `uicorner`, etc.) with full bidirectional mapping.
- **Element class aliases** — Short names in DSL (`button` → `TextButton`, `input` → `TextBox`, `image` → `ImageLabel`, etc.).
- **Page-as-element IR model** — `PageDef.element: UIElement` (class="Page") unifies page metadata and children into a single tree. Recursive walks work uniformly across all containers.
- **Multiple root elements per page** — CatWeb pages with multiple top-level elements are fully supported. All roots appear as children of the page element.
- **Script placeholders without alias** — Decompiler generates fallback aliases (`s1`, `s2`, ...) for script elements missing an alias field.
- **`build_gid_index()`** — Walks the CatUI AST to build alias→globalID and path→globalID index for UI linker resolution.
- **Full round-trip** — CatWeb JSON → decompile → CatUI DSL → edit → emit → CatWeb JSON preserves element order, nesting, properties, global IDs, and page metadata.

### Changed
- **PageDef IR** — `PageDef.roots: list[UIElement]` replaced with `PageDef.element: UIElement`. The page element holds page-level properties and its children are the top-level UI elements.
- **Builder** — `_build_from_dsl()` now returns page metadata alongside structure and script map. Metadata from the CatUI DSL is preserved and re-wrapped on compilation.
- **Emitter** — `emit_catui()` unwraps the page element: if page properties exist, emits `{...metadata..., "webcontent": [...children...]}`; if bare, emits just the children array.
- **Parser** — `page "name":` block body parsing now distinguishes page-level properties (key=value) from child elements, reusing `_parse_body()` for consistency.
- **Decompiler** — `decompile_ui_to_catui()` accepts optional `metadata` dict and emits page properties inline before child elements.
- **`decompile_page()`** — Passes page-level metadata (description, title, background, etc.) from the source JSON into the CatUI DSL output.
- **`build_gid_index()`** — Now iterates `page.element.children` with `Page.childname` paths (not `Page.page.childname`).

### Fixed
- **Parser script body handling** — Empty script blocks (no properties, no children) no longer cause parse errors. The parser correctly detects that the next token starts a sibling element.
- **Decompiler fallback aliases** — Script elements without an `alias` field now get generated fallback aliases (`s1`, `s2`, etc.) to produce valid CatUI DSL syntax.
- **GID index paths** — Paths like `Page.frame_1` (not `Page.page.frame_1`) by skipping the page element's own alias in path generation.
- **Builder backward compat** — Old-format `.catui` JSON files (with `"ui"` key) continue to work via format detection.
- **Sandbox tests** — Updated to use `page.element.children` instead of `page.roots`/`page.root` throughout.

## [1.0.0] - 2026-05-30 - Initial Release

### Added
- **PyPI publishing** - Full `pyproject.toml` with modern build metadata, classifiers, and long description. Package is ready for `pip install catpile`.
- **`.gitignore`** - Standard Python ignores for virtual environments, caches, build artifacts, and IDE files.
- **MIT LICENSE** - Formal license file accompanying the project.
- **GitHub preparation** - Repository structure finalized, docs updated, ready for push.

### Changed
- **Version bump** - 0.16.1 -> 1.0.0, marking the first stable release.
- **`setup.py`** - Added `long_description`, `classifiers`, `project_urls`, and full PyPI metadata.
- **README.md** - Fixed install path, removed stale references, updated project structure.
- **All docs** - Reviewed and updated for consistency.
- **VS Code extension** - Version bumped to 1.0.0.

### Removed
- **Stale `catpile-vscode/` reference** - Directory never existed; removed from README.

## [0.16.1] - 2026-04-22 - Bugfix Release

### Fixed
- **Tuple value format in FUNC_RUN/MATH_RUN actions** - Tuple slot `value` was emitted as a bare string (`"value": "{l!fen}"`) instead of an array of param objects (`"value": [{"value": "{l!fen}", "t": "string", "l": "any"}]`). CatWeb's import iterates over tuple values with `ipairs()`, causing "attempt to iterate over a string value" at import time. Multi-arg function calls also had args bleeding into the wrong slots.
- **Decompiler overwrites original input JSON** - `decompile_page()` produced a `{stem}.json` output containing the stripped page structure, overwriting the user's original CatWeb export when output was written to the same directory (the default). The `.catui` file already serves the reconstruction purpose for the builder. Removed the redundant `{stem}.json` output to preserve the original file.

## [0.16.0] - 2026-04-16 - Roundtrip & CLI

### Added
- **`cpile decompile` subcommand** - New `cpile decompile page.json` replaces the separate `cpile-decompile` script (kept as alias for backward compat). `cpile decompile -o dir/` outputs all files to a directory.
- **`.catpilerc` auto-generation** - Decompiler now produces a `.catpilerc` project config alongside `.cat` and `.catui` files, ready for `cpile build`.
- **Class-based UI element naming** - Unnamed UI elements (no `alias`/`name`) get class-based names with index (`Frame_1`, `TextButton_1`) instead of raw global IDs.
- **Empty script block parsing** - Parser now accepts `script "Name":` blocks with no events/functions. Empty named scripts are preserved in the output.
- **`cpile decompile` docs** - CLI reference, projects guide, decompiling guide, and quickstart updated with new commands.

### Changed
- **Page structure preservation** - `_strip_scripts` now replaces scripts with position markers (`{"class": "script", "alias": "..."}`) instead of removing them entirely. The builder walks this structure during recompilation, replacing markers with compiled scripts. This preserves original element order and nesting (scripts nested under Frames, etc.).
- **Wrapper metadata roundtrip** - `decompile_page` accepts both list and dict input. Dict wrappers (`{"background":"...", "webcontent": [...]}`) have their metadata preserved in `.catui` under `"metadata"` and re-wrapped by the builder on compilation.
- **`_gid_to_path` made explicit** - Removed module-level global state. `gid_to_path` is now passed as a parameter through `_escape_str`, `_extract_values`, `decompile_actions`, `decompile_event`, and `decompile_script`.
- **Builder uses structure reconstruction** - `build_page` walks the marker-based structure from `.catui`, replacing script markers with compiled JSON via `_reconstruct_from_structure`. Falls back to flat concatenation for old-style `.catui` files.
- **`load_ui` handles `.catui` format** - `UILinker.load_ui` now extracts the `"ui"` field from `.catui` dicts instead of crashing on the unexpected format.

### Fixed
- **Bracket parser ObjectRef** - Dotted paths (`page.Button`) in bracket taste now produce `ObjectRef` nodes matching the indent taste, instead of `VarRef`.
- **Missing ObjectRef import in ui.py** - `ObjectRef` was used in `UILinker._resolve_arg` but not imported, causing `NameError` at link time.
- **Pre-existing test assertion** - `test_parse_repeat` checked `times == 10` (int) but `RepeatStmt.times` is `str | None`. Fixed to `times == "10"`.

## [0.15.0] - 2026-03-26

### Added
- **Schema-based output variable detection** - Decompiler now uses CatWeb schema (quitism/catlua) to know which action slots are output variables. Actions with outputs use assignment syntax (`l_fen = input_get_text("field")`). Optional output vars (empty `""`) are not assigned.
- **Schema-based braces wrapping** - Emitter now uses slot types to decide `{}` wrapping. Variable/object slots get bare names (`l!count`), any/string slots get `{l!count}`. Users don't need to think about braces - the compiler handles it.
- **Dict literal decompilation** - `TABLE_CREATE` + consecutive `TABLE_SET` patterns are detected and emitted as `name = {"key": value, ...}`. Dictionaries of dictionaries are preserved with parent inserts.
- **Schema parser module** (`catpile/schema_parser.py`) - Fetches and parses CatWeb schema from quitism/catlua, extracting slot types, output positions, and optional flags.

### Changed
- **`RepeatStmt.times`** - Changed from `int | None` to `str | None` to support variable references in `repeat(l_value)`.
- **`_parse_repeat_stmt`** (both parsers) - Now accepts IDENT and VARIABLE tokens in addition to NUMBER.

### Fixed
- **Empty block bodies** - `if`, `repeat`, `foreach`, `on` blocks with no body are now valid (decompiled output may contain empty blocks).
- **Multi-part interpolation roundtrip** - `"{a}.{b}"` no longer lost on recompilation. `_render_arg` reconstructs multi-part InterpolatedStr.
- **`{icy-tea}` variable roundtrip** - Dashes in variable names converted to underscores (`icy_tea`) in decompiled output and back to `icy-tea` on recompilation.
- **`foreach("table")` parsing** - Parser accepts both bare IDENT and quoted STRING for table names.
- **`repeat(variable)` parsing** - Both parsers accept variable references for repeat count.
- **Empty output variables** - `func_run` with optional output no longer produces `"" = func_run(...)`.
- **Empty args in function calls** - Trailing `""` arguments are stripped from decompiled output.
- **`.1` number normalization** - Decompiler normalizes `.1` to `0.1` for valid Catpile syntax.
- **`_collect_if_body` bug** - IF body was always empty when no ELSE block. Fixed body collection.
- **Decompiler output variable heuristics** - Replaced with schema-based detection. No more false positives for `TABLE_SET`, `TABLE_INSERT`, etc.
- **Variable vs string distinction** - Decompiler uses slot type (`t: variable`, `t: object`, schema output markers) to decide bare vs quoted.
- **`_escape_str` scope-prefix** - Only strips `{...}` for single-brace values, not `"{a}.{b}"`.
- **Nested `script` directives** - Editor's `compileAll` strips existing `script` wrappers to prevent double-nesting.
- **Editor API endpoint** - Corrected from OAuth server to Catpile API.
- **Editor error line numbers** - Now show local line within script, not global combined line.
- **Editor auto-indentation** - Works for both indent (`:`) and bracket (`{ }`) tastes.
- **Editor UI element properties** - Clicking UI nodes in the Explorer tree now displays properties (Class, GlobalID, path, children count).
- **Compiled page structure** - Full Project output now merges compiled scripts into the UI tree, preserving original CatWeb page structure with scripts nested under their parent UI elements.
- **UI property preservation** - Import now stores all UI element properties (position, size, colors, fonts, etc.) and includes them in compiled output.

## [0.14.0] - 2026-03-05 - Color Update

### Added
- **Custom color picker** - Two-mode color selector for UI elements. Presets mode has 70+ swatches. Advanced mode: hue slider + saturation/value square + hex input.
- **Code editor color decorations** - Hex/RGB/HSV values show a color square. Click opens the picker and replaces the value.
- **`Colors` class** - `Colors.black`, `Colors.red`, etc. Decompiled scripts auto-convert matching preset colors.

## [0.13.0] - 2026-02-20

### Added
- **Path-based element references** - UI elements can be referenced by their page path (`page.FenLoader.Load`) instead of raw global IDs. The tokenizer supports dotted paths, the parser creates ObjectRef for them, and the UI linker resolves them to global IDs at compile time.
- **`.catui` generation on compile** - Full Project compilation now generates a `.catui` file with paths -> globalID mappings and UI hierarchy tree alongside the compiled page JSON.
- **Decompiler path-based references** - Decompiled scripts now use page paths (`page.Button.Name`) instead of raw CatWeb global IDs when a `.catui` path map is available.
- **VFS search** - Search bar in the Explorer panel filters UI elements and scripts by name.
- **Style element folding** - Layout/styling elements (UICorner, UIStroke, UIPadding, UIListLayout, UIGridLayout, UIGradient) are hidden from the VFS tree and shown in their parent's properties instead.
- **UI element properties in VFS** - Clicking a UI node displays its stored properties (Class, GlobalID, path, and all original CatWeb properties).

### Fixed
- **Import preserves UI hierarchy** - Scripts are now nested under their parent UI elements (Folders, Frames) matching the original CatWeb structure.
- **UI property preservation** - Import now stores all UI element properties (position, size, colors, fonts, etc.) and includes them in compiled output.
- **Compiled page structure** - Full Project output now merges compiled scripts into the reconstructed UI tree.
- **CatWeb-compatible JSON output** - Compiled output no longer includes CatWeb-incompatible fields (`name`, `note`, `_alias`). Uncompiled scripts are skipped instead of emitting placeholder objects.
- **Separate page + .catui export** - Download button exports only the page array. Copy button copies clean page JSON. `.catui` file is auto-downloaded alongside.
- **UI element selection state** - Clicking a UI node highlights it in the tree and shows it as active.
- **UI element tabs** - UI elements appear in the editor tab bar (marked "UI") for easy switching between scripts and properties.
- **Editor cleanup on tab close** - Closing the last tab properly clears the editor view and shows the placeholder.

## [0.12.0] - 2026-02-03

### Added
- **Schema-based output variable detection**
- **Decompiler empty arguments** - Action slots with empty values no longer produce `, ,` gaps in decompiled output.
- **Decompiler indentation** - Event body actions now properly indent under event headers. Fixed `level=0` -> `level=1` in `decompile_event`.
- **Web API error handling** - Python `SyntaxError` from tokenizer is now caught and returned as 400 instead of 500 Internal Server Error.
- **Editor API endpoint** - `API_BASE` corrected from OAuth server (`api.bouyakhsass.com`) to Catpile API (`cpile.bouyakhsass.com/api`).
- **Editor full project compilation** - Fixed `s.name !== s.name` (always false) bug. Scripts now properly wrapped with `script "name":` directive and indented.
- **Editor UI element properties** - Clicking UI nodes in the Explorer tree now displays properties (Class, GlobalID, path, children count).
- **Editor auto-indentation** - Language configuration now handles both indent (`:`) and bracket (`{ }`) tastes simultaneously.

## [0.11.0] - 2026-01-22

### Added
- **Decompiler** - `cpile-decompile page.json` reverses CatWeb JSON -> `.cat` scripts + `.catui` hierarchy. One `.cat` file per script. Preserves UI JSON for re-compilation.
- **Project system** - `cpile build` reads `.catpilerc` with page definitions, compiles all scripts, links UI elements, outputs complete page JSON. Auto-detects project root.
- **Builder module** (`builder.py`) - Orchestrates compile -> optimize -> link -> emit pipeline for multi-script projects.
- **UI path autocomplete** - `.catui` files map `Page.element.path` -> globalID for editor completions.
- **CLI subcommands** - `cpile build` and `cpile compile` subcommands. Backward compatible.

### Changed
- CLI now uses argparse subparsers: `cpile build`, `cpile compile`.
- Decompiler outputs separate `.cat` files per script (not monolithic).

## [0.10.0] - 2025-12-26

### Changed
- **`--clean` flag** - Debug fields (`_action`, `_event`) are now opt-in via `--clean`. Default output is pure CatWeb-compatible JSON. CatWeb's parser rejects unknown keys, so these fields must not appear in production output.
- **`Emitter(clean=...)`** - Default changed from `True` to `False`. Existing code using `Emitter()` without arguments now produces clean output.
- **Script-level `globalid`** - Scripts now include a required `globalid` and `enabled: "true"`. The `alias` field is only emitted when explicitly set.
- **Function definitions** - Now include `variable_overrides` array for function parameters, matching CatLua's output format.

## [0.9.0] - 2025-12-18

### Added
- **UI element linker** (`catpile/ui.py`) - Links script element references to their actual globalIDs from a CatWeb UI JSON file. Element names, aliases (via `name` field), and paths are all resolved at compile time. Usage: `cpile script.cat --ui page.json`.
- **`--ui` CLI flag** - Accepts a CatWeb UI JSON file. Before emission, all element references in the IR are resolved against the UI definition's globalID index.
- **Wiki documentation** (`docs/wiki/ui-linker.md`) - Full UI linker reference with examples.

### Changed
- **CLI pipeline** - Optimizer runs first, then UI linker, then emitter.

## [0.8.0] - 2025-12-08

### Added
- **JSON cleaner** - Emitted JSON now includes `_action` and `_event` debug fields alongside `id` fields, showing the human-readable action/event name. Makes debugging imports easier. On by default; disable with `--no-clean`.
- **UI element support** - Bare identifiers in `t: object` parameter slots (e.g., `hide(myFrame)`, `show(myBtn)`, `settext("label", myElement)`) are now treated as UI element globalids instead of variable references. Previously required quotes: `hide("myFrame")`. Both forms now work correctly.
- **`--no-clean` CLI flag** - Disables the JSON cleaner for raw CatWeb-compatible output.

### Changed
- **Emitter** - `Emitter.__init__` accepts `clean=True` parameter. `make_action` and `make_event` accept `clean` parameter.
- **`_emit_action`** - Resolves the canonical action name before slot counting; unwraps `{` `}` from VarRef renders in `t: object` slots, so element names are passed bare.

## [0.7.0] - 2025-11-28

### Added
- **IR optimization pipeline** (`catpile/optimizer.py`) - Three-tier optimizer with `-O1`/`-O2`/`-O3` CLI flags.
- **15 optimizer tests** covering all passes and edge cases.
- **Wiki documentation** (`docs/wiki/optimizer.md`).

### Changed
- **CLI** - Added `-O` / `--optimize` flag (0-3). Default is 0.

## [0.6.0] - 2025-11-10

### Added
- **Dict and list literals** in both tastes.
- **Example files** in `examples/`.

### Changed
- **Assignment** passes raw args through to emitter.
- **Indent tokenizer** - `[`, `]`, `{`, `}` support added.
- **Bracket tokenizer** - `{name}` detection cleaned up.

## [0.5.0] - 2025-10-27

### Added
- **Operator conditions** in bracket syntax (`==`, `!=`, `>`, `<`, `>=`, `<=`).

## [0.4.0] - 2025-10-20

### Added
- **Bracket syntax taste** (`bracket`).
- **Configurable default scope**.

### Changed
- **Taste renamed** from `sxscript_v1` to `indent`.
- **Changelog format** consolidated.

## [0.3.0] - 2025-10-08

### Added
- **Math expressions**, **plugin syntax system (tastes)**, **LSP server**, **VS Code extension**, **variable scoping**, **taste documentation**.

### Changed
- **Assignment syntax** from `->` to `=`.
- **CLI** with `--taste` flag.
- **Comment handling** improved.

### Fixed
- Comment-only event bodies, indentation issues.

## [0.2.0] - 2025-09-18

### Added
- **Multi-script projects**, **string interpolation**, **line numbers in errors**, **WSGI web API**, **common action aliases**.

### Changed
- Parser, emitter, IR improvements.

### Fixed
- `script` directive token consumption, if/else ELSE emission.

## [0.1.0] - 2025-09-04

### Added
- Initial release. 122 action mappings, Pythonic DSL parser, CLI, 14 tests.
