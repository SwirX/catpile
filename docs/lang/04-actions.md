# CatLang: Actions

Actions are the building blocks of CatLang — they map directly to CatWeb action IDs. Every action has a name, takes typed arguments, and may return output variables.

## Calling Actions

```python
action_name(arg1, arg2)
output = action_name(arg1)
out1, out2 = action_name(arg1)
```

## Console

Logging and debugging output.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `log(msg)` | LOG | 0 | Print to console |
| `warn(msg)` | WARN | 1 | Print warning |
| `error(msg)` | ERROR | 2 | Print error |
| `comment(text)` | COMMENT | 124 | No-op comment in action list |

```python
log("Hello world")
warn(l_score)
error("Something broke")
comment("TODO: optimize this")
```

## Logic

Conditions, comparisons, and flow control.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `wait(seconds)` | WAIT | 3 | Pause execution |
| `if eq(a, b):` | IF_EQ | 18 | If equal |
| `if neq(a, b):` | IF_NEQ | 19 | If not equal |
| `if gt(a, b):` | IF_GT | 20 | If greater than |
| `if lt(a, b):` | IF_LT | 21 | If lower than |
| `if gte(a, b):` | IF_GTE | 125 | If greater or equal |
| `if lte(a, b):` | IF_LTE | 126 | If lower or equal |
| `if contains(str, substr):` | IF_CONTAINS | 37 | If string contains |
| `if not_contains(str, substr):` | IF_NOT_CONTAINS | 38 | If doesn't contain |
| `if and(a, b):` | IF_AND | 44 | Logical AND |
| `if or(a, b):` | IF_OR | 45 | Logical OR |
| `if nor(a, b):` | IF_NOR | 46 | Logical NOR |
| `if xor(a, b):` | IF_XOR | 47 | Logical XOR |
| `if exists(var):` | IF_EXISTS | 92 | If variable exists |
| `if not_exists(var):` | IF_NOT_EXISTS | 93 | If doesn't exist |
| `if mouse_left:` | IF_MOUSE_LEFT | 79 | Left mouse button down |
| `if mouse_middle:` | IF_MOUSE_MIDDLE | 80 | Middle mouse button down |
| `if mouse_right:` | IF_MOUSE_RIGHT | 81 | Right mouse button down |
| `if key_down(key):` | IF_KEY_DOWN | 82 | Key held down |
| `if is_ancestor(a, b):` | IF_IS_ANCESTOR | 103 | If ancestor of |
| `if is_child(a, b):` | IF_IS_CHILD | 104 | If child of |
| `if is_descendant(a, b):` | IF_IS_DESCENDANT | 105 | If descendant of |
| `if dark_theme:` | IF_DARK_THEME | 108 | Dark mode enabled |

```python
if eq(l_score, 100):
    log("Perfect")

if exists(l_player):
    log("Player exists")

if key_down("Shift"):
    log("Sprinting")

wait(0.5)
```

## Loops

Repeated execution and iteration.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `repeat(n):` | REPEAT | 22 | Repeat n times |
| `repeat_forever:` | REPEAT_FOREVER | 23 | Loop indefinitely |
| `foreach(table):` | TABLE_ITER | 113 | Iterate over table |
| `break` | BREAK | 24 | Exit loop |

```python
repeat(10):
    inc(l_count, 1)

repeat_forever:
    if gt(l_lives, 0):
        wait(1)
    else:
        break

foreach(l_items):
    log("{l_index}: {l_value}")
```

`foreach` automatically provides `l_index` (key) and `l_value` (value) variables.

## Looks

UI element visibility, text, properties, and images.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `show(target)` | LOOK_SHOW | 9 | Make visible |
| `hide(target)` | LOOK_HIDE | 8 | Make invisible |
| `set_text(target, text)` | LOOK_SET_TEXT | 10 | Set text content |
| `set_prop(prop, target, value)` | LOOK_SET_PROP | 31 | Set element property |
| `get_prop(prop, target)` → `value` | LOOK_GET_PROP | 39 | Get element property |
| `duplicate(target)` → `clone` | LOOK_DUPLICATE | 49 | Clone element |
| `delete(target)` | LOOK_DELETE | 50 | Destroy element |
| `set_image(target, id)` | LOOK_SET_IMG | 106 | Set image |
| `set_avatar(target, userid, res?)` | LOOK_SET_AVATAR | 107 | Set to avatar image |
| `tween(prop, target, value, time, style, dir)` | LOOK_TWEEN | 88 | Animate property |
| `get_at_pos(x, y)` → `array` | LOOK_GET_AT_POS | 127 | Get objects at position |
| `get_asset_info(info, id)` → `value` | LOOK_GET_ASSET_INFO | 129 | Get asset metadata |

```python
hide(page.LoadingScreen)
show("gameArea")
set_text(l_label, "Score: 100")
set_prop("Background Color", l_frame, Colors.navy)
l_bg = get_prop("Background Color", l_frame)
l_clone = duplicate(page.Template)
tween("Position", l_box, "0,200", 0.5, "Quad", "Out")
```

## Hierarchy

Element tree navigation and reparenting.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `parent(child, new_parent)` | HIER_PARENT | 58 | Reparent element |
| `get_parent(child)` → `parent` | HIER_GET_PARENT | 97 | Get parent element |
| `find_ancestor(name, obj)` → `ancestor` | HIER_FIND_ANCESTOR | 98 | Find ancestor by name |
| `find_child(name, parent)` → `child` | HIER_FIND_CHILD | 99 | Find child by name |
| `find_descendant(name, parent)` → `desc` | HIER_FIND_DESCENDANT | 100 | Find descendant by name |
| `get_children(parent)` → `table` | HIER_GET_CHILDREN | 101 | Get all children |
| `get_descendants(parent)` → `table` | HIER_GET_DESCENDANTS | 102 | Get all descendants |

```python
parent(l_drag, l_dropZone)
l_root = get_parent(l_child)
l_btn = find_child("SubmitBtn", l_form)
l_all = get_children(l_container)
```

## Navigation

Page redirection and URL handling.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `redirect(url)` | NAV_REDIRECT | 4 | Navigate to URL |
| `get_query(param)` → `value` | NAV_GET_QUERY | 67 | Get query string param |
| `get_url()` → `url` | NAV_GET_URL | 117 | Get current URL |

```python
redirect("https://example.com")
l_page = get_query("page")
l_current = get_url()
```

## Math & Variables

Variable arithmetic, rounding, and math functions.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `set(var, value)` | VAR_SET | 11 | Set variable |
| `inc(var, amount)` | VAR_INC | 12 | Increment |
| `dec(var, amount)` | VAR_DEC | 13 | Decrement |
| `mul(var, factor)` | VAR_MUL | 14 | Multiply |
| `div(var, divisor)` | VAR_DIV | 15 | Divide |
| `mod(var, divisor)` | VAR_MOD | 41 | Modulo |
| `pow(var, exponent)` | VAR_POW | 40 | Raise to power |
| `round(var)` | VAR_ROUND | 16 | Round to nearest |
| `floor(var)` | VAR_FLOOR | 17 | Round down |
| `ceil(var)` | VAR_CEIL | 78 | Round up |
| `random(var, min, max)` | VAR_RANDOM | 27 | Random number |
| `del(var)` | VAR_DEL | 96 | Delete variable |
| `set_attr(prop, var, value)` | AVAR_SET | 94 | Set attribute on variable |
| `get_attr(prop, var)` → `value` | AVAR_GET | 95 | Get attribute of variable |
| `math_run(func, args...)` → `result` | MATH_RUN | 114 | Run math function |

```python
set(l_score, 0)
inc(l_score, 10)
mul(l_score, 2)
div(l_score, 100)
random(l_damage, 1, 20)
floor(l_avg)
l_result = math_run("sqrt", 144)
```

## Audio

Playback control for sounds and music.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `play_audio(id)` → `variable` | AUDIO_PLAY | 5 | Play audio once |
| `play_audio_loop(id)` → `variable` | AUDIO_PLAY_LOOP | 26 | Play looped audio |
| `stop_all_audio()` | AUDIO_STOP_ALL | 7 | Stop all sounds |
| `stop_audio(variable)` | AUDIO_STOP | 74 | Stop specific audio |
| `pause_audio(variable)` | AUDIO_PAUSE | 75 | Pause audio |
| `resume_audio(variable)` | AUDIO_RESUME | 76 | Resume audio |
| `set_volume(variable, vol)` | AUDIO_SET_VOL | 73 | Set volume (0-1) |
| `set_speed(variable, speed)` | AUDIO_SET_SPEED | 77 | Set playback speed |

```python
l_music = play_audio("rbxassetid://12345")
play_audio_loop("rbxassetid://67890")
set_volume(l_music, 0.5)
pause_audio(l_music)
```

## Input

User input and viewport information.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `get_text(input)` → `text` | INPUT_GET_TEXT | 30 | Get text from input field |
| `get_viewport()` → `w, h` | INPUT_GET_VIEWPORT | 84 | Get viewport dimensions |
| `get_cursor()` → `x, y` | INPUT_GET_CURSOR | 85 | Get cursor position |
| `get_username()` → `name` | USER_GET_NAME | 51 | Get local username |
| `get_user_id()` → `id` | USER_GET_ID | 52 | Get local user ID |
| `get_display_name()` → `name` | USER_GET_DISPLAY | 53 | Get display name |

```python
l_input = get_text(page.NameField)
l_w, l_h = get_viewport()
l_x, l_y = get_cursor()
l_user = get_username()
```

## Network

Broadcasting and messaging across the page, site, or cross-site.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `broadcast_page(message)` | NET_BROADCAST_PAGE | 32 | Broadcast across page |
| `broadcast_site(message)` | NET_BROADCAST_SITE | 33 | Broadcast across site |
| `broadcast_crosssite(message, url)` | NET_BROADCAST_CROSSSITE | 130 | Broadcast to another page |

```python
broadcast_page("player_joined")
broadcast_site("score_updated")
broadcast_crosssite("item_purchased", "https://example.com/shop")
```

## Cookies

Persistent key-value storage.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `set_cookie(name, value)` | COOKIE_SET | 34 | Set cookie |
| `inc_cookie(name, amount)` | COOKIE_INC | 35 | Increment cookie |
| `get_cookie(name)` → `value` | COOKIE_GET | 36 | Get cookie |
| `del_cookie(name)` | COOKIE_DEL | 62 | Delete cookie |

```python
set_cookie("highscore", 5000)
l_score = get_cookie("highscore")
inc_cookie("visits", 1)
del_cookie("temp_data")
```

## Time

Timestamps, formatting, and server time.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `get_unix()` → `timestamp` | TIME_GET_UNIX | 68 | Get local unix timestamp |
| `get_server_unix()` → `timestamp` | TIME_GET_SERVER_UNIX | 116 | Get server unix timestamp |
| `get_tick()` → `tick` | TIME_GET_TICK | 83 | Get tick count |
| `get_timezone()` → `tz` | TIME_GET_TIMEZONE | 118 | Get timezone |
| `format_now(format)` → `str` | TIME_FORMAT_NOW | 71 | Format current date/time |
| `format_unix(ts, format)` → `str` | TIME_FORMAT_UNIX | 72 | Format from unix timestamp |

```python
l_now = get_unix()
l_date = format_now("%Y-%m-%d")
l_formatted = format_unix(l_timestamp, "%H:%M:%S")
l_tz = get_timezone()
```

## Color

Color space conversion and interpolation.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `hex_to_rgb(hex)` → `RGB` | COLOR_HEX_TO_RGB | 119 | Hex to RGB string |
| `hex_to_hsv(hex)` → `HSV` | COLOR_HEX_TO_HSV | 120 | Hex to HSV string |
| `rgb_to_hex(RGB)` → `hex` | COLOR_RGB_TO_HEX | 121 | RGB to hex |
| `hsv_to_hex(HSV)` → `hex` | COLOR_HSV_TO_HEX | 122 | HSV to hex |
| `lerp_color(hex1, hex2, alpha)` → `hex` | COLOR_LERP | 123 | Interpolate between colors |

```python
l_rgb = hex_to_rgb("#1a1a2e")
l_hex = rgb_to_hex("255, 128, 64")
l_mid = lerp_color("#ff0000", "#0000ff", 0.5)
```

## Strings

String manipulation and inspection.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `str_len(str)` → `length` | STR_LEN | 48 | Get string length |
| `str_sub(var, start, end)` → `result` | STR_SUB | 42 | Substring |
| `str_replace(old, var, new)` → `result` | STR_REPLACE | 43 | Replace substring |
| `str_split(str, sep)` → `table` | STR_SPLIT | 57 | Split into table |
| `str_lower(str)` → `result` | STR_LOWER | 69 | Convert to lowercase |
| `str_upper(str)` → `result` | STR_UPPER | 70 | Convert to uppercase |
| `str_concat(a, b)` → `result` | STR_CONCAT | 109 | Concatenate two strings |

```python
l_len = str_len("hello")
l_greeting = str_concat("Hello, ", l_name)
l_parts = str_split("a,b,c", ",")
l_lower = str_lower("HELLO")
l_sub = str_sub(l_text, 0, 5)
```

String interpolation `"Hello {name}!"` is syntax sugar that compiles to `STR_CONCAT` chains automatically.

## Tables

Dictionary and array operations.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `create_table(name)` | TABLE_CREATE | 54 | Create empty table |
| `table_set(entry, table, value)` | TABLE_SET | 55 | Set entry by key |
| `table_set_obj(entry, table, obj)` | TABLE_SET_OBJ | 66 | Set entry to object |
| `table_get(entry, table)` → `value` | TABLE_GET | 56 | Get entry by key |
| `table_del(entry, table)` | TABLE_DEL | 90 | Delete entry by key |
| `table_insert(value, pos?, array)` | TABLE_INSERT | 89 | Insert into array |
| `table_remove(pos, array)` | TABLE_REMOVE | 91 | Remove at position |
| `table_len(array)` → `length` | TABLE_LEN | 59 | Get array length |
| `table_join(array, sep)` → `string` | TABLE_JOIN | 110 | Join array to string |

```python
create_table(l_settings)
table_set("volume", l_settings, 0.8)
l_vol = table_get("volume", l_settings)
table_insert("new_item", 1, l_list)
table_remove(1, l_list)
l_count = table_len(l_list)
l_csv = table_join(l_list, ",")
```

Dict literals `{"key": value}` compile to `TABLE_CREATE` + `TABLE_SET` chains automatically.

## Functions

Defining and calling reusable logic.

| CatLang | Schema Name | ID | Description |
|---|---|---|---|
| `func_run(name, args...)` → `result` | FUNC_RUN | 87 | Run function synchronously |
| `func_run_bg(name, args...)` | FUNC_RUN_BG | 63 | Run function in background |
| `func_run_protected(name, args...)` → `success, result` | FUNC_RUN_PROTECTED | 128 | Run protected (pcall-style) |
| `return value` | RETURN | 115 | Return from function |

```python
l_result = func_run("add", 5, 3)
func_run_bg("save_data", l_payload)
l_ok, l_data = func_run_protected("load", "file.json")
```

`func_run_protected` returns success as the first output and the actual result as the second.
