# Guides: Project System

Catpile builds complete CatWeb pages from CatUI DSL (`.catui`) files and CatLang (`.cat`) scripts.

## Project Structure

```
project/
├── ui/
│   └── main.catui        # UI layout in CatUI DSL
├── src/
│   ├── loading.cat       # Compiled scripts
│   ├── game.cat
│   └── utils.cat
├── build/
│   └── main.json         # Compiled output
└── .catpilerc            # Project config
```

## The `.catpilerc` Config File

```json
{
  "taste": "indent",
  "pages": [
    {
      "name": "main",
      "catui": "ui/main.catui",
      "output": "build/main.json"
    }
  ]
}
```

| Key | Description |
|-----|-------------|
| `name` | Page name (used in build output) |
| `catui` | Path to `.catui` DSL file (new format) |
| `output` | Where to write the compiled JSON |

### Old Format (Backward Compatible)

```json
{
  "name": "old",
  "ui": "ui/old.catui",
  "scripts": ["src/main.cat"],
  "output": "build/old.json"
}
```

The `ui` + `scripts` keys together specify the UI JSON and script files separately. Automatic format detection distinguishes old vs new format.

## Building a Page

```bash
cpile build
```

Reads `.catpilerc`, walks all pages, and for each:

1. **Parse CatUI DSL** — tokenizes and parses `.catui` into a `CatUIProgram` AST
2. **Collect scripts** — finds `script` placeholder elements that reference `.cat` sources
3. **Compile scripts** — compiles each `.cat` file to CatWeb JSON
4. **Build GID index** — walks UI tree to build alias→globalID and path→globalID maps
5. **Link UI references** — resolves `page.Element.Path` references in scripts to global IDs
6. **Reconstruct structure** — merges compiled scripts into the UI tree at their placeholder positions
7. **Emit** — outputs the complete page JSON with metadata and `webcontent`

```bash
# Build all pages
cpile build

# Build a single page
cpile build --page main

# Output to custom directory
cpile build --out-dir dist/
```

## Programmatic Usage

```python
from catpile.builder import build_page
from pathlib import Path

page_cfg = {
    "name": "main",
    "catui": "ui/main.catui",
    "output": "build/main.json",
}
result = build_page(page_cfg, project_root=Path("."),
                    taste_name="indent")
# result is a JSON string of the compiled page
```

## CatUI DSL Format

The `.catui` file uses an indentation-based syntax to declare UI elements:

```python
page "main":
    background = "#202020"
    title = "My App"

    frame container [globalid: "rootGID"]:
        size = "{1,0},{1,0}"
        bg = "#1a1a2e"

        textlabel header:
            text = "Welcome"
            font_size = "30"

        textbutton submit:
            text = "Click Me"
            bg = "#4e9bff"
            uicorner corner:
                radius = "0,8"

        script game_logic:
            source = "src/game.cat"

    textbox input:
        editable = "true"
        placeholder = "Enter name"
```

### Page-Level Properties

Properties at the top of the `page` block become page metadata:

| DSL Key | JSON Key | Description |
|---------|----------|-------------|
| `background` | `background` | Page background color |
| `title` | `title` | Browser tab title |
| `description` | `description` | Meta description |
| (any key) | (same key) | Arbitrary page metadata |

### Element Syntax

```
class_name alias [annotations]:
    properties...
    children...
```

- **class_name** — DSL alias or full CatWeb class name (`button`, `textlabel`, `Frame`, `TextButton?link`, etc.)
- **alias** — Unique name for path references (`page.container.header`)
- **annotations** — `[globalid: "value"]` for setting explicit global IDs
- **properties** — `key = value` pairs, with aliases (`bg` → `background_color`, `corner` → `uicorner`)
- **children** — Nested elements or styling elements

### Element Class Aliases

| DSL | CatWeb Class |
|-----|-------------|
| `frame` | `Frame` |
| `scrollingframe` / `scrollframe` | `ScrollingScrollFrame` |
| `textlabel` / `label` | `TextLabel` |
| `textbutton` / `button` | `TextButton` |
| `textbox` / `input` | `TextBox` |
| `imagelabel` / `image` | `ImageLabel` |
| `link` | `TextButton?link` |
| `donation` ⚠️ | `TextButton?donation` | Donation [^deprecated-donation](#page-metadata) |
| `transfer` | `TextButton?transfer` | Transfer |
| `avataritem` | `TextButton?avataritem` | Avatar Item |
| `folder` | `Folder` |
| `uicorner` / `corner` | `UICorner` |
| `uistroke` / `stroke` | `UIStroke` |
| `uigradient` / `gradient` | `UIGradient` |
| `uipadding` / `padding` | `UIPadding` |
| `uilistlayout` / `listlayout` | `UIListLayout` |
| `uigridlayout` / `gridlayout` | `UIGridLayout` |

### Styling Elements

Styling elements (UICorner, UIStroke, etc.) are nested directly inside the element they modify:

```python
textbutton submit:
    text = "Click"
    uicorner corner:
        radius = "0,8"
    uistroke outline:
        stroke_color = "#ffffff"
        stroke_thickness = "2"
```

### Script Placeholders

```python
script my_alias:
    source = "src/my_script.cat"
```

The `script` element marks where a compiled `.cat` script will be injected. The `source` path is relative to the project root. Scripts without a `source` are preserved as markers (for decompiled pages where the original `.cat` source is unknown).

## UI Linker

The UI linker resolves `page.` path references to CatWeb global IDs.

### How It Works

1. Parse `.catui` DSL → build element tree
2. Build index: `page.Path.Name` → `globalid`
3. Compile `.cat` scripts → IR → walk IR, find all `ObjectRef` nodes
4. Replace with resolved global IDs

```python
from catpile.ui import UILinker

linker = UILinker("ui/main.catui")  # or pass a dict
resolved = linker.link(program)
print(f"Resolved {resolved} references")
```

### Path Format

```
Page.container
Page.container.header
Page.container.submit
Page.input
```

The index is a flat dict mapping paths to global IDs:

```json
{
  "Page.container": "rootGID",
  "Page.container.header": "header123",
  "Page.input": "input456"
}
```

## Import → Edit → Compile Flow

```
CatWeb JSON → Import (decompile)
    ↓
Decompile to .cat files + .catui DSL
    ↓
Edit scripts & UI layout
    ↓
cpile build
    ↓
Parse CatUI DSL + compile scripts
    ↓
Merge into UI tree + resolve paths
    ↓
{background, webcontent, title, ...}
    ↓
Import to CatWeb
```

## Page Metadata

Page-level properties are preserved through the round trip:

| Field | Source | Round-Trip |
|-------|--------|-----------|
| `background` | CatUI DSL `background = "..."` | ✓ |
| `title` | CatUI DSL `title = "..."` | ✓ |
| `description` | CatUI DSL `description = "..."` | ✓ |
| Any other property | CatUI DSL `key = value` | ✓ |

During decompilation, metadata from the CatWeb JSON wrapper (e.g. `{"background": "#202020", "webcontent": [...]}`) becomes page-level properties in the CatUI DSL. During compilation, these properties are re-wrapped in the output JSON.

[^deprecated-donation]: The `donation` element class is deprecated in favor of `transfer` and `avataritem`. Use `transfer` for donation/payment buttons and `avataritem` for avatar item purchases. See the [CatUI language reference footnote](../catui/01-language-reference.md#footnotes) for details.
