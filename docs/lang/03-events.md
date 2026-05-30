# CatLang: Events

Events are the entry points for code execution. They trigger when a specific thing happens - page load, button press, mouse hover, etc.

<SyntaxBreakdown pattern="event-handler" />

<SymbolCard name="loaded" />
<SymbolCard name="pressed" />
<SymbolCard name="key_press" />

## Event Structure

```python
on <event_name>[(<target>)]:
    <body>
```

- `on` keyword
- Event name (check table below)
- Optional target in parentheses (a UI element globalid or path)
- Colon `:`
- Indented body (one or more statements)

## Event Table

| Event Name | ID | Alias | Parameters | Description |
|---|---|---|---|---|
| `loaded` | 0 | `LOADED` | - | When website/script loads |
| `pressed` | 1 | `PRESSED` | `button` (object) | When a button is clicked |
| `mouse_enter` | 2 | `MOUSE_ENTER` | `object` | Mouse enters element |
| `mouse_leave` | 3 | `MOUSE_LEAVE` | `object` | Mouse leaves element |
| `changed` | 4 | `CHANGED` | `object` | Element value changed |
| `focused` | 5 | `FOCUSED` | `object` | Element gained focus |
| `unfocused` | 6 | `UNFOCUSED` | `object` | Element lost focus |
| `key_press` | 7 | `KEY_PRESS` | - | Key pressed |
| `key_release` | 8 | `KEY_RELEASE` | - | Key released |
| `value_changed` | 9 | `VALUE_CHANGED` | `object` | Slider value changed |
| `input_began` | 10 | `INPUT_BEGAN` | `object` | Touch input began |
| `input_ended` | 11 | `INPUT_ENDED` | `object` | Touch input ended |
| `input_changed` | 12 | `INPUT_CHANGED` | `object` | Touch position changed |
| `player_added` | 13 | `PLAYER_ADDED` | `name` | Player joined the server |

## Events with Targets

Events that act on a specific UI element use the target parameter:

```python
on pressed("@<"):                  # Button with globalid @<
    log("Clicked!")

on pressed(page.FileLoader.Load):   # Path-based reference
    log("Clicked!")

on changed("textInput"):
    log("Input changed")
```

### Using Path References

Instead of raw global IDs, you can use paths from the `.catui` file:

```python
on pressed(page.FileLoader.Load):
    l_text = input_get_text(page.FileLoader.FileInput)
```

The compiler resolves these to global IDs at compile time.

## `loaded` Event - Special Case

`loaded` fires when the page loads. It takes no parameters:

```python
on loaded:
    log("Page loaded")
    init_ui()
    load_data()
```

This is equivalent to CatWeb's "When website loaded..." block.

## Multiple Events in One Script

A script can have multiple events:

```python
on loaded:
    DATA_LOADED = 0
    init_settings()

on pressed("startButton"):
    run_game()
```

## Event Parameter: `(parent)`

The special target `(parent)` refers to the parent element of the script:

```python
on pressed(page.Element.Button):
    # (parent) is the element that owns this script
    hide("(parent)")
```

This is a CatWeb built-in that resolves to the script's container.

## Function Definitions

Functions are reusable blocks of code with parameters:

```python
fn function_name(param1, param2):
    <body>
```

Example with parameters:

```python
fn CreateElement(position, color):
    o_element = look_duplicate("T5")
    look_set_prop("Position", o_element, position)
    look_set_prop("Name", o_element, color)

fn GetFirst(val):
    o_x = l_val
    o_x = o_x / 10
    return o_x
```

Functions can return values with `return`:

```python
fn add(a, b):
    return a + b

on loaded:
    result = func_run("add", 3, 5)
```

Functions are called via the `func_run` action internally.
