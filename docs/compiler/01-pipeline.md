# Compiler: Pipeline Overview

Catpile transforms `.cat` source code into CatWeb-compatible JSON through a multi-stage pipeline. Additionally, CatUI DSL (`.catui`) files are compiled to CatWeb UI JSON.

## Script Pipeline

```
.cat source
    │
    ▼
┌─────────────┐
│  Tokenizer   │  Character-by-character → tokens (IDENT, NUMBER, STRING, etc.)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Parser     │  Tokens → AST (Intermediate Representation)
│  (Taste)     │  Handles indent-based or bracket-based syntax
└──────┬──────┘
       │
       ▼
┌───────────────┐
│    RAWs       │  (Built-in symbol definitions)
│   Interning   │
└──────┬───────┘
       │
       ▼
┌─────────────┐
│  Optimizer   │  Dead code elimination, inlining, constant folding
│   (-O1/-O2)  │  Loop unrolling, peephole optimization
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  UI Linker   │  Resolves page. references → global IDs
│              │  Reads CatUI AST for path→globalID mapping
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Emitter    │  IR → CatWeb JSON actions
│              │  Coordinate grid, ID gen, slot filling
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Builder     │  Merges scripts with UI tree from CatUI DSL
│              │  Generates {background, webcontent, title, ...} output
└──────┬──────┘
       │
       ▼
   CatWeb JSON
```

## CatUI DSL Pipeline

```
.catui source
    │
    ▼
┌──────────────────┐
│ CatUI Tokenizer   │  Indentation-based → tokens (IDENT, STRING, ASSIGN, etc.)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CatUI Parser      │  Tokens → CatUI IR (PageDef, UIElement, etc.)
│                   │  Page properties → element properties, children → sub-elements
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CatUI Emitter     │  CatUI IR → CatWeb UI JSON array
│                   │  Unwraps page element: metadata + webcontent
│                   │  Resolves property/class aliases, assigns global IDs
└────────┬─────────┘
         │
         ▼
   CatWeb UI JSON (→ Builder merges with compiled scripts)
```

<PipelineViz />

## Stage Details

### 1. Tokenizer

The tokenizer reads source text character-by-character and produces a stream of tokens:

- `IDENT` - identifiers (`hello`, `l_count`, `page.Button`)
- `NUMBER` - numeric literals (`5`, `3.14`, `0.1`)
- `STRING` - string literals (`"hello"`)
- `LPAREN`, `RPAREN` - parentheses
- `COLON` - colon (`:`)
- `ASSIGN` - equals (`=`)
- `COMMA` - comma
- `OP` - math operators (`+`, `-`, `*`, `/`, `%`)
- `NEWLINE` - line endings
- `INDENT`, `DEDENT` - indentation changes
- `BLOCK_OPEN`, `BLOCK_CLOSE` - braces (`{`, `}`)

Dotted paths like `page.Button` are tokenized as a single IDENT token.

### 2. Parser

The parser consumes tokens and produces an AST (Abstract Syntax Tree). Two parsers exist:

- **Indent parser** (`parser.py`) - uses `:` and indentation to define blocks
- **Bracket parser** (`tastes/bracket.py`) - uses `{ }` and `;`

Both produce the same IR types.

### 3. Intermediate Representation (IR)

The IR is a set of Python dataclasses:

```python
@dataclass
class Program:
    scripts: list[ScriptDef]

@dataclass
class ScriptDef:
    name: str
    events: list[EventDef]
    functions: list[FunctionDef]

@dataclass
class ActionStmt:
    name: str      # Action type (e.g. "LOG", "VAR_SET")
    args: list[Arg]  # Typed arguments
```

### 4. Optimizer

Pass-based optimizer at three levels:

| Level | Flag | Optimizations |
|---|---|---|
| O0 | `-O0` | None |
| O1 | `-O1` | Dead code elimination, constant folding |
| O2 | `-O2` | Inlining, loop unrolling |
| O3 | `-O3` | Peephole, branch coalescing |

### 5. UI Linker

Resolves `page.Element.Path` references to CatWeb global IDs. Reads the `.catui` file's `paths` dictionary:

```python
UILinker("page.catui").link(program)
# page.HomeButton → "homeButtonGID"
```

### 6. Emitter

Walks the IR and produces CatWeb JSON actions. Handles:

- **Coordinate placement** - events placed on a grid (450px spacing)
- **Action chunking** - splits events > 120 actions into multiple blocks
- **Nested control flow** - expands IF/REPEAT/FOREACH to condition + body + END
- **Global ID generation** - unique IDs for every action
- **Schema-based slot filling** - values placed in correct slot types
- **Auto braces** - `{}` wrapping based on slot type

### 7. Builder

Merges compiled scripts back into the UI tree, preserving page metadata and producing CatWeb-compatible JSON:

```json
{
  "favicon": "...",
  "webcontent": [{"class": "script", ...}, {"class": "Frame", ...}],
  "title": "...",
  "background": "..."
}
```

## Reverse Pipeline (Decompiler)

The decompiler reverses CatWeb JSON → `.cat` source:

```
CatWeb JSON → [Extract Scripts] → [Decompile Actions] → .cat
           → [Extract UI] → [Build Paths] → .catui
           → [Strip Scripts] → .json (preserved UI)
```

The decompiler:
1. Walks the JSON tree to find all scripts
2. Converts flat `END`-terminated action arrays to indented blocks
3. Resolves global IDs to page paths using the CatUI AST paths map
4. Outputs `.cat`, `.catui`, and `.catpilerc` files

### 8. CatUI DSL Parser & Emitter

The CatUI DSL pipeline runs alongside the script pipeline in the builder:

**.catui Tokenizer** (`catui_parser.py`):
- Indentation-based tokenizer similar to the indent taste
- Produces `IDENT`, `STRING`, `NUMBER`, `ASSIGN`, `COLON`, `LBRACKET`, `RBRACKET`, `INDENT`, `DEDENT`, `KEYWORD`, `EOF` tokens

**.catui Parser** (`catui_parser.py`):
- `page "name":` blocks containing properties and child elements
- Element syntax: `class_name alias [annotations]:`
- Annotations: `[globalid: "value"]`
- Properties: `key = value`
- Styling elements (UICorner, UIStroke, etc.) nested inside parents
- Script placeholders: `script alias:`

**CatUI IR** (`catui_ir.py`):
- `CatUIProgram` — list of `PageDef`
- `PageDef` — `name` + `element: UIElement` (class="Page")
- `UIElement` — `class_name`, `alias`, `globalid`, `properties`, `children`
- `UIStylingElement` — styling elements with `class_name`, `alias`, `properties`
- `ScriptPlaceholder` — `alias`, `source`, `enabled`

**.catui Emitter** (`catui_emitter.py`):
- Walks CatUI IR → CatWeb UI JSON
- Page element unwrapped: properties → metadata, children → webcontent
- Property alias resolution (`bg` → `background_color`)
- Element class alias resolution (`button` → `TextButton`)
- Auto global ID generation
- Script markers emitted as `{"class": "script", "alias": "..."}`

**UI Elements Schema** (`ui_elements.json`):
- 23 element classes with property definitions and type info
- Property aliases (DSL ↔ JSON) for bidirectional mapping
- Element class aliases (`textbutton` → `TextButton`, `transfer` → `TextButton?transfer`, etc.)

## File Type Handling — No Auto-Deduction

The CLI uses explicit subcommands, not extension-based dispatch:

| Command | Input | Handles |
|---------|-------|---------|
| `cpile compile script.cat` | `.cat` | CatLang → script JSON |
| `cpile decompile page.json` | `.json` | CatWeb page → `.cat` + `.catui` + `.catpilerc` |
| `cpile catui page.json` | `.json` | CatWeb page → `.catui` only |
| `cpile build` | `.catpilerc` | Project config → compiled page JSON |

There is no `cpile mypage.catui` that auto-detects and emits JSON, because `.catui` files need the full builder pipeline (script compilation, UI linking, metadata wrapping) — not a simple file-in/JSON-out conversion. Inside `build`, the builder does auto-detect `.catui` DSL vs old JSON format via `_detect_catui_format()`.

## No Header Files

Catpile has no header/include system. Scripts and UI definitions are fully self-contained:

- **`.cat` scripts** declare their own `script "alias":` wrapper. Functions are defined and used within the same file or across files at runtime — no forward declarations needed.
- **`.catui` files** declare the complete element tree. Path-based references (`Page.myButton`) are resolved at compile time by the UI linker using an index built from the CatUI AST, not from headers.
- **The builder** orchestrates: reads `.catui`, discovers referenced `.cat` sources, compiles each independently, resolves paths via the linker, and merges everything.

Adding headers would require duplicating function signatures or element declarations with no benefit — everything needed for compilation is already discoverable from the source files.
