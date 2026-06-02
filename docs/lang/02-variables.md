# CatLang: Variables & Scopes

<SyntaxBreakdown pattern="var-scope" />

## Declaration and Assignment

Variables are created on first assignment. No explicit declaration is needed.

```python
on loaded:
    score = 0           # Variable "score" created and set to 0
    score = 100         # Overwrite
    msg = "hello"       # String
    data = table_get(1, o_parts)  # Output of an action
```

## Multi-Return Assignment

Some actions return multiple values. These can be captured in a comma-separated list:

```python
on loaded:
    WIDTH, HEIGHT = input_get_viewport()
    CURSOR_X, CURSOR_Y = input_get_cursor()
    x, y = get_position()
```

This maps to CatWeb's multi-output action syntax.

## Scope System

CatLang uses a prefix-based scope system that maps directly to CatWeb's `scope!name` notation:

### Local Scope (`l_` prefix)

Variables prefixed with `l_` are scoped to the current script execution. They do NOT persist between events.

```python
on loaded:
    l_username = input_get_text("username_input")
    l_parts = str_split(l_username, " ")
```

Compiles to: `l!username`, `l!parts`

### Object Scope (`o_` prefix)

Variables prefixed with `o_` are scoped to a specific UI element (the one that owns the event, or the element passed as a parameter). They DO persist.

```python
on pressed("myButton"):
    o_header = look_duplicate("T5")
    o_bgColor = table_get("bg", l_value)
```

Compiles to: `o!header`, `o!bgColor`

### No Prefix

Variables without a scope prefix are global by default:

```python
on loaded:
    USERS = create_table()
    DATA_LOADED = 0
```

These are good for constants and page-wide state.

## Scope Keywords (Optional)

You can also use `local` and `obj` keywords for clarity:

```python
on loaded:
    local temp = 5       # Same as l_temp
    obj myButton = ...   # Same as o_myButton
```

These keywords are optional - the prefix convention is the primary mechanism.

## Scope Variable Name Roundtrip

The `scope_var_name()` function in Catpile ensures that scope-prefixed variables roundtrip correctly:

- `l_count` → `l!count` (local)
- `o_header` → `o!header` (object)
- `l__var` → `l_var` (literal underscore - double underscore escape)

When decompiling CatWeb JSON back to `.cat`, `l!count` becomes `l_count`.

## Variable References in Action Calls

When passing a variable to an action, **Catpile automatically handles the `{}` wrapping** based on the action's slot type:

- **Variable/object slots** - bare name: `log(o_header)` → `{o!header}`
- **String/any slots** - the whole string is used: `log("Value: {n}")` → concatenation
- **Output slots** - variables are captured: `o_parts = str_split(...)` → output assignment

You don't need to think about `{var}` vs bare `var` - the compiler handles it based on the schema.

## Constants vs Variables

CatLang does not have a `const` keyword. However, variables that are assigned a literal value once and never modified are constant-folded at compile time:

```python
on loaded:
    ITEM_SIZE = CONTAINER_SIZE / 5   # Constant folded
    EMPTY_STRING = ""            # Constant
```

## Predefined Constants

### HEIGHT and WIDTH

These are automatically available when `get_viewport()` is called:

```python
on loaded:
    WIDTH, HEIGHT = input_get_viewport()
    CONTAINER_SIZE = HEIGHT * .9
```

### Colors

The `Colors` class provides named color constants:

```python
on loaded:
    log(Colors.red)     # → "#ff0000"
    log(Colors.black)   # → "#000000"
    log(Colors.navy)    # → "#0f3460"
```

Available colors include: `white`, `black`, `red`, `orange`, `yellow`, `green`, `cyan`, `blue`, `magenta`, `lightGray`, `gray`, `darkGray`, `brown`, `purple`, `navy`, `crimson`, `teal`, and more.

See [Color Reference](../guides/05-colors.md) for the full palette.
