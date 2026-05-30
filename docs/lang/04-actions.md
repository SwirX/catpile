# CatLang: Actions

Actions are the basic building blocks of CatLang - they map directly to CatWeb actions (IDs 0-121). Every action has a name, takes arguments, and may return output variables.

<SyntaxBreakdown pattern="action-call" />

<SymbolCard name="log" />
<SymbolCard name="show" />
<SymbolCard name="hide" />
<SymbolCard name="set" />
<SymbolCard name="inc" />
<SymbolCard name="wait" />
<SymbolCard name="func_run" />

## Calling Actions

Actions are called like functions:

```python
action_name(arg1, arg2)
action_name(arg1, arg2) → target_var
output1, output2 = action_name(arg1)
```

## Action Names (Aliases)

Actions have English aliases for readability:

```python
log("hello")         # LOG (id 0)
hide("element")      # LOOK_HIDE (id 8)
show("element")      # LOOK_SHOW (id 9)
wait(1.5)            # WAIT (id 3)
set(score, 100)      # VAR_SET (id 11)
inc(score, 1)        # VAR_INC (id 12)
dec(score, 1)        # VAR_DEC (id 13)
mul(score, 2)        # VAR_MUL (id 14)
div(score, 2)        # VAR_DIV (id 15)
```

## Actions by Category

### Console & Debug

| Action | Alias | ID | Description |
|---|---|---|---|
| `log(msg)` | LOG | 0 | Print to console |
| `warn(msg)` | WARN | - | Print warning |
| `error(msg)` | ERROR | - | Print error |

### Control Flow

| Action | Alias | ID | Description |
|---|---|---|---|
| `wait(seconds)` | WAIT | 3 | Pause execution |
| `break` | BREAK | 24 | Exit loop |
| `if_eq(a, b)` | IF_EQ | 18 | The `if` statement handles this |

### Variables

| Action | Alias | ID | Description |
|---|---|---|---|
| `set(name, value)` | VAR_SET | 11 | Set variable |
| `inc(name, amount)` | VAR_INC | 12 | Increment |
| `dec(name, amount)` | VAR_DEC | 13 | Decrement |
| `mul(name, factor)` | VAR_MUL | 14 | Multiply |
| `div(name, divisor)` | VAR_DIV | 15 | Divide |
| `mod(name, divisor)` | VAR_MOD | 41 | Modulo |
| `random(min, max)` → `result` | MATH_RANDOM | 17 | Random number |
| `round(value)` → `result` | MATH_ROUND | 16 | Round |

### UI Elements (Looks)

| Action | Alias | ID | Description |
|---|---|---|---|
| `show(target)` | LOOK_SHOW | 9 | Make visible |
| `hide(target)` | LOOK_HIDE | 8 | Hide |
| `settext(target, text)` | LOOK_SET_TEXT | 10 | Set text label |
| `set_prop(prop, target, value)` | SET_PROP | 31 | Set element property |
| `get_prop(prop, target)` → `value` | GET_PROP | 39 | Get element property |
| `tween(prop, target, value, time, style, dir)` | TWEEN | 88 | Animate property |
| `duplicate(source)` → `clone` | DUPLICATE | 49 | Clone element |
| `delete(target)` | DELETE | 50 | Destroy element |
| `find_child(name, parent)` → `child` | FIND_CHILD | 99 | Find nested element |
| `get_children(parent)` → `table` | GET_CHILDREN | 101 | Get all children |
| `get_parent(child)` → `parent` | GET_PARENT | 97 | Get parent element |
| `set_img(target, image_id)` | SET_IMAGE | 106 | Set image |
| `set_bg(target, color)` | SET_BG | - | Set background |

### Tables

| Action | Alias | ID | Description |
|---|---|---|---|
| `create_table(name)` | TABLE_CREATE | 54 | Create table |
| `table_set(key, table, value)` | TABLE_SET | 55 | Set entry |
| `table_get(key, table)` → `value` | TABLE_GET | 56 | Get entry |
| `table_insert(value, pos, table)` | TABLE_INSERT | 89 | Insert into array |
| `table_remove(pos, table)` | TABLE_REMOVE | - | Remove entry |

### Strings

| Action | Alias | ID | Description |
|---|---|---|---|
| `str_split(str, sep)` → `table` | STR_SPLIT | 57 | Split string |
| `str_concat(a, b)` → `result` | STR_CONCAT | 109 | Concatenate |
| `str_lower(str)` → `result` | STR_LOWER | 69 | Lowercase |
| `str_upper(str)` → `result` | STR_UPPER | - | Uppercase |
| `str_len(str)` → `result` | STR_LEN | - | Length |
| `str_sub(str, start, end)` → `result` | STR_SUB | - | Substring |
| `str_replace(str, old, new)` → `result` | STR_REPLACE | - | Replace |
| `str_join(table, sep)` → `result` | STR_JOIN | 110 | Join array |
| `contains(str, substr)` → `bool` | STR_CONTAINS | 37 | Check substring |

### Input

| Action | Alias | ID | Description |
|---|---|---|---|
| `input_get_text(input)` → `text` | INPUT_GET_TEXT | 30 | Get text from input |
| `input_get_viewport()` → `w, h` | INPUT_GET_VIEWPORT | 84 | Get viewport |
| `input_get_cursor()` → `x, y` | INPUT_GET_CURSOR | 85 | Get cursor position |
| `user_get_id()` → `id` | USER_GET_ID | 52 | Get user ID |

### Network

| Action | Alias | ID | Description |
|---|---|---|---|
| `redirect(url)` | NAV_REDIRECT | 4 | Navigate to URL |
| `play(audio_id)` | AUDIO_PLAY | 5 | Play sound |
| `broadcast(signal)` | BROADCAST | - | Send signal |
| `get_url()` → `url` | GET_URL | - | Get current URL |
| `get_query(name)` → `value` | GET_QUERY | - | Get query param |

### Functions

| Action | Alias | ID | Description |
|---|---|---|---|
| `func_run(name, args...)` → `result` | FUNC_RUN | 87 | Run user-defined function |
| `return(value)` | RETURN_VAL | 115 | Return from function |

### Colors

| Action | Alias | ID | Description |
|---|---|---|---|
| `hex_to_rgb(hex)` → `r, g, b` | HEX_TO_RGB | - | Hex → RGB |
| `hex_to_hsv(hex)` → `h, s, v` | HEX_TO_HSV | - | Hex → HSV |
| `rgb_to_hex(r, g, b)` → `hex` | RGB_TO_HEX | - | RGB → Hex |

### Cookies

| Action | Alias | ID | Description |
|---|---|---|---|
| `set_cookie(name, value)` | COOKIE_SET | 34 | Set cookie |
| `get_cookie(name)` → `value` | COOKIE_GET | 36 | Get cookie |
| `del_cookie(name)` | COOKIE_DEL | - | Delete cookie |

## Multi-Return Actions

Some actions return multiple values:

```python
WIDTH, HEIGHT = input_get_viewport()     # 2 outputs
CURSOR_X, CURSOR_Y = input_get_cursor()  # 2 outputs
```

The compiler uses the CatWeb schema to know which arguments are output slots.

## Action Arguments

Arguments are typed. The schema defines three main types:

- **Variable/object slots** - expect bare variable names: `set(myVar, 5)`
- **String/any slots** - strings or interpolated strings: `settext("label", "Hello")`
- **Output slots** - variable names (bare) used in assignment

You don't need to worry about `{}` wrapping - the compiler handles it automatically.

## Conditions (IF Actions)

`if` is a statement, not a function call:

```python
if eq(a, b):        # IF_EQ
    log("equal")

if exists("var"):   # IF_EXISTS
    log("exists")

if gt(score, 100):  # IF_GREATER
    log("high")
```

Condition aliases:

| Alias | Action |
|---|---|
| `eq` | IF_EQ |
| `neq` | IF_NEQ |
| `gt` | IF_GREATER |
| `gte` | IF_GREATER_EQ |
| `lt` | IF_LESS |
| `lte` | IF_LESS_EQ |
| `exists` | IF_EXISTS |
| `contains` | STR_CONTAINS |
| `and` | IF_AND |
| `or` | IF_OR |
