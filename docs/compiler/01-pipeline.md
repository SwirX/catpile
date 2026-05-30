# Compiler: Pipeline Overview

Catpile transforms `.cat` source code into CatWeb-compatible JSON through a multi-stage pipeline.

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
│              │  Reads .catui for path→globalID mapping
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
│  Builder     │  Merges scripts with UI tree
│              │  Generates {favicon, webcontent, ...} output
└──────┬──────┘
       │
       ▼
   CatWeb JSON
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
3. Resolves global IDs to page paths using the `.catui` paths map
4. Outputs `.cat`, `.catui`, and `.json` files
