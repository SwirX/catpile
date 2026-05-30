# CatLang: Expressions & Interpolation

## String Interpolation

Variables inside strings are interpolated automatically using `\{name\}` syntax:

```python
on loaded:
    name = "SwirX"
    score = 3200

    # Simple interpolation
    log("Hello \{name\}!")

    # Multiple vars
    log("\{name\} has {score} points")

    # With surrounding text - auto-generates STR_CONCAT chains
    settext("label", "You scored {score} points on \{name\}'s board")
```

### How It Works

The compiler detects `{...}` inside string literals and:

1. **Single `\\{var\\}` with no surrounding text** - resolves to a direct variable reference (no concat): `log("\\{name\\}")` → `LOG` with value `\\{name\\}`
2. **`\\{var\\}` with surrounding text** - generates `STR_CONCAT` chains: `log("Hello \\{name\\}!")` → `CONCAT("Hello ", \\{name\\}, "!")`
3. **Multiple `\\{var\\}` references** - generates multi-concat chains: `log("{a}.{b}")` → `CONCAT(CONCAT(\\{a\\}, "."), \\{b\\})`


### Interpolation in Action Arguments

String interpolation works anywhere a string is expected:

```python
on loaded:
    look_set_prop("Size", o_frame, "0, {ITEM_SIZE}, 0, {ITEM_SIZE}")
    look_set_prop("Position", o_element, "{o_xpos}, 0, {o_ypos}, 0")
    log("Pos: {label} @ {index}")
```

## Math Expressions

CatLang supports compile-time math with **constant folding** and runtime math via variable actions.

### Constant Expressions

Numbers only - evaluated at compile time:

```python
on loaded:
    n = 2 + 3 * 4         # → n = 14 (folded to constant)
    n = (10 - 2) / 2      # → n = 4
    n = 100 % 3           # → n = 1
```

### Variable Expressions

When variables are involved, the compiler generates runtime actions:

```python
on loaded:
    n = {CONTAINER_SIZE} / 2    # → DIV CONTAINER_SIZE, 2
    n = {x} * {ITEM_SIZE}   # → MUL x, ITEM_SIZE
    n = {x} + {y} + {z}    # → INC x, y → INC x, z
```

Supported operators:
- `+` (add/inc)
- `-` (subtract/dec)
- `*` (multiply)
- `/` (divide)
- `%` (modulo)
- `^` (power - if available in CatWeb)

```python
on loaded:
    ITEM_SIZE = HEIGHT / 10
    PANEL_XPOS = HEIGHT / 2
    PANEL_YPOS = HEIGHT * .1
    o_xpos = o_xpos * ITEM_SIZE
    o_xpos = o_xpos + PANEL_XPOS
```

## The `Colors` Class

Named color constants:

```python
on loaded:
    # Using Colors class
    look_set_prop("Background Color", frame, Colors.navy)
    look_set_prop("Background Color", button, Colors.red)

    # Or mixing with hex
    look_set_prop("Background Color", tile, "#f0c060")
```

Available color names include:
- `Colors.white`, `Colors.black`, `Colors.red`, `Colors.orange`, `Colors.yellow`, `Colors.green`, `Colors.cyan`, `Colors.blue`, `Colors.magenta`
- `Colors.lightRed`, `Colors.darkRed`, `Colors.lightGreen`, `Colors.darkGreen`, `Colors.lightBlue`, `Colors.darkBlue`
- `Colors.brown`, `Colors.navy`, `Colors.purple`, `Colors.crimson`, `Colors.midnight`, `Colors.teal`, `Colors.forestGreen`
- `Colors.gray`, `Colors.lightGray`, `Colors.darkGray`, `Colors.dark`
- `Colors.snow`, `Colors.silver`

See [Color Reference](../guides/05-colors.md) for the full palette.

## Dict Literals

Tables can be created inline using dict syntax:

```python
on loaded:
    # Create table "default" and populate it
    colors = {"bg": "1a1a2e", "fg": "eaeaea"}
    # Insert into parent table
    table_set("colors", "app_config", colors)

    # Multiple nested dicts
    alt = {"bg": "16213e", "fg": "f5f5f5"}
    table_set("alt", "app_config", alt)
```

This compiles to:
```
TABLE_CREATE "default"
TABLE_SET "bg", "colors", "1a1a2e"
TABLE_SET "fg", "colors", "eaeaea"
TABLE_SET "colors", "app_config", colors
```

The decompiler detects this pattern and outputs the dict literal form.

## List Literals

Arrays are created inline:

```python
on loaded:
    ITEM_OFFSETS = [-3, -2, -1, 0, 1, 2, 3]
```

Compiles to `TABLE_CREATE` + `TABLE_INSERT` for each element.

## Variable References in Expressions

Use `\{var\}` inside strings to interpolate. In expressions, bare variable names are references:

```python
# These are equivalent:
look_set_prop("Size", o_frame, "0, {ITEM_SIZE}, 0, {ITEM_SIZE}")
look_set_prop("Size", o_frame, "0, {ITEM_SIZE}, 0, {ITEM_SIZE}")
```

## Path References (Page Elements)

UI elements can be referenced by path:

```python
on loaded:
    # Path-based reference (from .catui)
    hide(page.LoadingScreen)
    show(page.HomeButton)

    # Nested path
    set_prop("Background Color", page.SearchBox.Input, Colors.white)
```

These resolve to global IDs at compile time via the UI linker.
