<p align="center">
  <img src="assets/icon.png" alt="Catpile" width="200">
</p>

# Catpile

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)

A Pythonic DSL → **CatWeb JSON** compiler. Write Roblox CatWeb scripts in a clean, readable language — and define your UI layout with a declarative indentation-based DSL. Compile both to the JSON format CatWeb expects.

```
.cat  source → [Parser] → IR (AST) → [Emitter] → CatWeb JSON
.catui source → [CatUI Parser] → CatUI IR → [CatUI Emitter] → CatWeb UI JSON
```

## Quick Start

```bash
# Install
pip install catpile

# Compile a script
cpile script.cat -o output.json

# Decompile a full CatWeb page to scripts + UI layout + project config
cpile decompile page.json -o output-dir/

# Or extract just the UI layout as CatUI DSL (no scripts)
cpile catui page.json -o layout.catui

# Compile a full page from .catui DSL
# (see docs/guides/03-projects.md)

# Web service (localhost:8788)
python3 -m catpile.web
```

## Documentation

Online: [catpile-docs.vercel.app](https://catpile-docs.vercel.app)

Full source is also in the [`docs/`](docs/) directory:

| Section | Covers |
|---------|--------|
| **CatLang Reference** - [docs/lang/](docs/lang/) | Syntax, variables, scopes, events, actions, control flow, expressions - everything about the language |
| **CatUI DSL Reference** - [docs/catui/](docs/catui/) | Declarative UI layout: element classes, property aliases, annotations, styling, compilation |
| **Compiler** - [docs/compiler/](docs/compiler/) | Pipeline, IR, emitter, optimizer, taste system, schema parser, CatUI DSL compiler - how Catpile works under the hood |
| **Tools** - [docs/tools/](docs/tools/) | CLI reference, Web API, VSCode extension guide |
| **Guides** - [docs/guides/](docs/guides/) | Installation, quickstart, project system, decompiling, CatUI DSL, color reference |
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
    if gte(count, 10):
        log("Max reached!")
        hide("myButton")

# Multi-script project
script "display":
    on loaded:
        render_list()

script "data":
    fn render_list():
        foreach(items):
            log("{l_index}: {l_value}")
```

## CatUI DSL at a Glance

```python
# Declarative UI layout for a CatWeb page
page "main":
    background = "#202020"
    title = "My App"

    frame root [globalid: "rootGID"]:
        size = "{1,0},{1,0}"
        bg = "#1a1a2e"

        textlabel title:
            text = "Welcome"
            font = "GothamBold"

        textbutton submit:
            text = "Click Me"
            uicorner corner:
                radius = "0,8"

    script main:
```

Compile with the builder — scripts from `.cat` files merge into the UI tree automatically.

## Key Features

- **Indentation-based syntax** (Python-like) and **bracket syntax** (JS-like) via the taste system
- **CatUI DSL** — Declare UI layouts with `page "name":` blocks, element class/alias/annotations/properties/children, property aliases (`bg` → `background_color`), and full round-trip decompilation
- **Schema-based compilation** - every action knows its slot types (variable, object, any), so braces `{}` are handled automatically
- **Dict literals** - `config = {"theme": "dark", "volume": 0.8}` compiles to CREATE_TABLE + SET_ENTRY chains
- **String interpolation** - `"Hello {name}!"` auto-generates STR_CONCAT
- **Math expressions** - constant folding at compile time, VAR_* chains at runtime for variables
- **Multi-return actions** - `x, y = getCursor()`
- **Scope-prefixed variables** - `l_count` → `l!count` (local), `o_board` → `o!board` (object), bare names are global by default
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
│   ├── emitter.py           # IR → CatWeb JSON (scripts)
│   ├── parser.py            # Indent taste tokenizer + parser
│   ├── decompiler.py        # CatWeb JSON → .cat source + .catui DSL
│   ├── cli.py               # CLI entry point
│   ├── decompile_cli.py     # Decompile CLI entry point
│   ├── web.py               # WSGI web API
│   ├── lsp.py               # LSP server (stdio)
│   ├── ui.py                # UI element linker
│   ├── optimizer.py         # -O1/-O2/-O3 optimizations
│   ├── builder.py           # Project build system
│   ├── catui_ir.py          # CatUI DSL AST types (PageDef, UIElement, …)
│   ├── catui_parser.py      # CatUI DSL tokenizer + parser
│   ├── catui_emitter.py     # CatUI IR → CatWeb UI JSON
│   ├── ui_elements.json     # 23 UI element classes, aliases, property mappings
│   ├── tastes/
│   │   ├── __init__.py      # Abstract Taste base class
│   │   ├── v1.py            # "indent" taste
│   │   ├── bracket.py       # "bracket" taste
│   │   └── registry.py      # Taste discovery
├── examples/
├── tests/
├── docs/                    # Full documentation
├── pyproject.toml           # Build config
├── LICENSE
├── CHANGELOG.md
├── .gitignore
└── README.md
```

## License

Distributed under the **GNU General Public License v3.0**. See [`LICENSE`](LICENSE) for details.
