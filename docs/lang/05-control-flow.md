# CatLang: Control Flow

## If / Else

The `if` statement evaluates a condition. CatLang supports:

```python
# Basic if
if eq("{a}", "{b}"):
    log("They are equal")

# if / else
if eq(a, b):
    log("Equal")
else:
    log("Not equal")

# if / elseif / else
if eq(a, b):
    log("Equal")
else:
    if eq(a, c):
        log("Equal to C")
    else:
        log("Different")
```

### Condition Aliases

The condition goes in parentheses after `if`:

| Expression | Condition |
|---|---|
| `eq(a, b)` | Equal to |
| `neq(a, b)` | Not equal to |
| `gt(a, b)` | Greater than |
| `gte(a, b)` | Greater or equal |
| `lt(a, b)` | Less than |
| `lte(a, b)` | Less or equal |
| `exists("var")` | Variable exists |
| `contains(str, sub)` | String contains |

```python
if exists("user_prefs"):
    log("User preferences are ready")

if gt(score, 100):
    log("High score!")
```

## Repeat Loops

Execute a block a fixed number of times:

```python
repeat(5):
    log("Processing item")
    inc(idx, 1)

# With a variable for the count
repeat(l_value):
    log("Rows")
```

The `repeat` argument can be a number literal or a variable reference.

## Repeat Forever

Infinite loop - runs until `break`:

```python
repeat_forever:
    wait(.1)
    if eq(DATA_LOADED, 1):
        break
```

## Foreach Loops

Iterate through a table (dict/array):

```python
foreach("user_prefs"):
    # l_index is the key, l_value is the value
    o_value = table_get("val", l_value)
    log("{l_index}: {o_value}")

# With an explicit table variable
foreach(USER_DATA):
    log("{l_index}: {l_value}")
```

In the body, two loop variables are automatically available:
- `l_index` - the current key/index
- `l_value` - the current value

## Break

Exit a loop immediately:

```python
repeat_forever:
    wait(.1)
    if eq(DATA_LOADED, 1):
        break
    if eq(retries, 8):
        log("Timed out")
        redirect("fallback.rbx")
        break
```

## Return

Exit a function, optionally returning a value:

```python
fn GetRole(user):
    if contains("admin", l_user):
        return "admin"
    return "user"
```

`return` without a value returns nil.

## Nested Control Flow

Blocks can be nested arbitrarily:

```python
foreach(o_rows):
    o_items = str_split(l_value, "")
    foreach(o_items):
        if isNum(o_items):
            repeat(l_value):
                inc(item_idx, 1)
        else:
            func_run("ProcessItem", item_idx, l_value)
            inc(item_idx, 1)
```

The compiler handles the IR-to-JSON nesting correctly by tracking open blocks and emitting matching `end` (id 25) actions.

## Block Compilation

Control flow blocks compile to CatWeb's BEGIN/END structure:

```
if eq(a, b):          → IF_EQ a, b
    log("equal")      → LOG "equal"
else:                 → ELSE
    log("not equal")  → LOG "not equal"
                      → END
```

The decompiler reverse-engineers this structure back into CatLang's indented format.
