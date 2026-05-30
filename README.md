# Catpile

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)

A Pythonic DSL → **CatWeb JSON** compiler. Write Roblox CatWeb scripts in a clean, readable language - compile to the JSON format CatWeb expects.

```
.cat source → [Parser] → IR (AST) → [Emitter] → CatWeb JSON
```

## Quick Start

```bash
# Install
pip install catpile

# Compile a script
cpile script.cat -o output.json

# Or as module
python3 -m catpile.cli script.cat

# Web service (localhost:8788)
python3 -m catpile.web
```

## Documentation

Full documentation is in the [`docs/`](docs/) directory:

| Section | Covers |
|---------|--------|
| **CatLang Reference** - [docs/lang/](docs/lang/) | Syntax, variables, scopes, events, actions, control flow, expressions - everything about the language |
| **Compiler** - [docs/compiler/](docs/compiler/) | Pipeline, IR, emitter, optimizer, taste system, schema parser - how Catpile works under the hood |
| **Tools** - [docs/tools/](docs/tools/) | CLI reference, Web API, VSCode extension guide |
| **Guides** - [docs/guides/](docs/guides/) | Installation, quickstart, project system, decompiling, color reference |
| **Examples** - [docs/examples/](docs/examples/) | Step-by-step with full explanations and snippets |

## CatLang at a Glance

```python
# One-script example
on loaded:
    log("Hello World!")

# With variables, conditions, and loops
on pressed("myButton"):
    count = 0
    repeat(10):
        inc(count, 1)
    if eq(count, 10):
        log("Done!")

# Multi-script project
script "movement":
    on loaded:
        initBoard()

script "utils":
    fn initBoard():
        createTable("pieces")
        setentry("king", "pieces", "e1")
```

## Key Features

- **Indentation-based syntax** (Python-like) and **bracket syntax** (JS-like) via the taste system
- **Schema-based compilation** - every action knows its slot types (variable, object, any), so braces `{}` are handled automatically
- **Dict literals** - `pieces = {"king": "e1", "queen": "d1"}` compiles to CREATE_TABLE + SET_ENTRY chains
- **String interpolation** - `"Hello {name}!"` auto-generates STR_CONCAT
- **Math expressions** - constant folding at compile time, VAR_* chains at runtime for variables
- **Multi-return actions** - `x, y = getCursor()`
- **Scope-prefixed variables** - `l_count` → `l!count` (local), `o_board` → `o!board` (object), `g_score` → `g!score` (global)
- **Path-based UI references** - `page.button` instead of raw global IDs
- **Auto-indentation** (for both tastes), **auto-complete**, **code color preview**
- **Web editor** at `cpile.bouyakhsass.com` with project import/export

## Project Structure

```
catpile/
├── catpile/
│   ├── __init__.py          # Package init + scope_var_name()
│   ├── schema.json          # 122 actions, 14 events
│   ├── schema_parser.py     # CatWeb schema fetcher (from quitism/catlua)
│   ├── mappings.py          # Schema loader, aliases, make_action()
│   ├── ir.py                # IR types (VarRef, StrLit, MathExpr, …)
│   ├── emitter.py           # IR → CatWeb JSON
│   ├── parser.py            # Indent taste tokenizer + parser
│   ├── decompiler.py        # CatWeb JSON → .cat source + .catui
│   ├── cli.py               # CLI entry point
│   ├── web.py               # WSGI web API
│   ├── lsp.py               # LSP server (stdio)
│   ├── ui.py                # UI element linker
│   ├── optimizer.py         # -O1/-O2/-O3 optimizations
│   ├── builder.py           # Project build system
│   └── tastes/
│       ├── __init__.py      # Abstract Taste base class
│       ├── v1.py            # "indent" taste
│       ├── bracket.py       # "bracket" taste
│       └── registry.py      # Taste discovery
├── vscode-catpile/          # VSCode extension (syntax highlighting)
├── examples/
├── tests/
├── docs/                    # Full documentation
├── CHANGELOG.md
└── README.md
```

## License

Distributed under the **GNU General Public License v3.0**. See [`LICENSE`](LICENSE) for details.
