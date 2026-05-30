# CatLang: Events

Events are where code execution begins. They fire when something happens — page loads, button clicks, mouse movement, key presses, messages, etc.

## Event Structure

```python
on <event_name>[(<target>)]:
    <body>
```

- `on` keyword
- Event name
- Optional target in parentheses (a UI element, globalid, or page path)
- Colon `:`
- Indented body

## Event Table

| CatLang | ID | Schema Name | Parameters | Description |
|---|---|---|---|---|
| `on loaded:` | 0 | LOADED | — | Page or script loads |
| `on pressed(target):` | 1 | PRESSED | `target` (object) | Element is clicked |
| `on key_pressed(key):` | 2 | KEY_PRESSED | `key` (key code) | Key is pressed |
| `on mouse_enter(target):` | 3 | MOUSE_ENTER | `target` (object) | Mouse enters element |
| `on mouse_leave(target):` | 5 | MOUSE_LEAVE | `target` (object) | Mouse leaves element |
| `on changed(target):` | 10 | CHANGED | `target` (object) | Element value changes |
| `on mouse_down(target):` | 11 | MOUSE_DOWN | `target` (object) | Mouse pressed on element |
| `on mouse_up(target):` | 12 | MOUSE_UP | `target` (object) | Mouse released on element |
| `on right_click(target):` | 13 | RIGHT_CLICKED | `target` (object) | Element is right-clicked |
| `on donation(target):` | 7 | DONATION | `target` (object) | Gamepass/product bought |
| `on submit(target):` | 8 | INPUT_SUBMIT | `target` (object) | Input form submitted |
| `on message:` | 9 | MSG_RECEIVED | — | Broadcast message received |
| `on crosssite_message:` | 14 | CROSSSITE_MSG | — | Cross-site message received |

## Function Definitions

Functions are reusable blocks defined with `fn`:

```python
fn <name>(<params>):
    <body>
```

| CatLang | ID | Schema Name | Parameters | Description |
|---|---|---|---|---|
| `fn name(args):` | 6 | FUNC_DEF | `name` (string), `args` | Define a callable function |

```python
fn add(a, b):
    return a + b

on loaded:
    result = func_run("add", 3, 5)
```

## Events with Targets

Events that act on a specific UI element take a target parameter:

```python
on pressed(page.FileLoader.Load):
    log("Clicked!")

on changed("textInput"):
    log("Input changed")

on key_pressed("Enter"):
    log("Enter pressed")
```

Targets can be:
- **Raw global IDs**: `on pressed("@<"):`
- **Page paths**: `on pressed(page.FileLoader.Load):` (resolved via `.catui`)
- **Strings**: `on changed("textInput"):`

## `loaded` — Special Case

`loaded` fires when the page/script loads and takes no parameters:

```python
on loaded:
    log("Page ready")
    init_game()
```

Equivalent to CatWeb's "When website loaded..." block.

## Multiple Events

A script can have any number of events:

```python
on loaded:
    DATA_LOADED = 0

on pressed("startButton"):
    run_game()

on message:
    handle_signal()
```

## `(parent)` Target

The special target `(parent)` refers to the element containing the script:

```python
on pressed(page.Element.Button):
    hide("(parent)")
```

A CatWeb built-in that resolves to the script's container element.
