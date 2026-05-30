# CatLang: Snippets & Patterns

Common CatLang patterns with explanations. Click the copy button on each to use in your project.

## 1. Page Initialization

```python
on loaded:
    DATA_LOADED = 0
    log("Initializing...")
    WIDTH, HEIGHT = input_get_viewport()
    func_run("InitializeSizes")
    func_run("PrecomputeValues")
    log("Loading User Preferences")
    func_run("LoadThemes")
    log("Preloading Decals")
    func_run("PreloadImages")
    log("Loading Initial Application State")
    func_run("SetupUI")
    DATA_LOADED = 1
    log("All Data Have Been Loaded")
```

This pattern waits for viewport, initializes sizes, loads themes/preferences, then sets up the UI. `DATA_LOADED` signals completion to other scripts.

## 2. Wait Until Loaded

```python
on loaded:
    repeat_forever:
        wait(.1)
        if eq(DATA_LOADED, 1):
            break
    log("Proceeding - data ready")
```

A polling loop that blocks until `DATA_LOADED` is set to 1.

## 3. Theme Button Duplication

```python
fn CreateThemeButton(theme_name):
    o_button = look_duplicate("theme_template")
    look_set_prop("Name", o_button, l_theme_name)
    look_set_prop("Tooltip", o_button, l_theme_name)
    set_prop("Visible", o_button, true)
    return o_button
```

Duplicates a UI template element for each theme, setting name and tooltip properties.

## 4. Table as Dictionary

```python
app_config = {
    "theme": "dark",
    "lang": "en",
    "version": "2.1"
}
```

Compiles to a `TABLE_CREATE` + `TABLE_SET` chain. The decompiler converts these back to dict literals.

## 5. ForEach + If Chain

```python
foreach(UI_ELEMENTS):
    o_ename = get_prop("Name", l_value)
    if eq(o_ename, "active"):
        set_prop("Background Color", l_value, ACTIVE_COLOR)
    else:
        if eq(o_ename, "inactive"):
            set_prop("Background Color", l_value, INACTIVE_COLOR)
```

Iterates through a table, branching on each element's Name property.

## 6. String Interpolation

```python
on loaded:
    name = "Admin"
    role = "editor"
    log("Logged in as {name} with role {role}")
    look_set_prop("Position", o_element, "0, {ITEM_SIZE}, 0, {ITEM_SIZE}")
```

Strings with `{...}` are auto-interpolated to STR_CONCAT chains. No manual concatenation needed.

## 7. Multi-Return Function

```python
fn SplitCoords(pos):
    o_parts = str_split(l_pos, ",")
    o_x = table_get(1, o_parts)
    o_y = table_get(2, o_parts)
    return "{o_x}.{o_y}"
```

Returns a dot-separated string from comma-separated input, ready for further split operations.

## 8. Email Validation

```python
fn ValidateEmail(email):
    l_lower = str_lower(l_email)
    if not contains(l_lower, "@"):
        return ""
    o_parts = str_split(l_lower, "@")
    o_domain = table_get(2, o_parts)
    if contains(o_domain, "."):
        IS_VALID_EMAIL = 1
```

Checks if an email address contains an `@` symbol and the domain includes a dot, marking it as valid.

## 9. Split + Index Access

```python
fn GetSegment(path):
    o_parts = func_run("SplitCoords", l_path)
    o_parts = str_split(o_parts, ".")
    o_segment = table_get(2, o_parts)
    o_idx = l_path / 2
    o_segment = o_segment / 2
    o_idx = o_idx + o_segment
    return l_path
```

Splits a coordinate string into parts, parses row/column segments, and returns the original path.

## 10. UI Path Reference

```python
on loaded:
    hide(page.LoadingScreen)
    set_prop("Text", page.HomeButton, "Play Now")
    settext(page.StatusLabel, "Ready")
```

Using `page.` paths instead of raw global IDs. The compiler resolves these to global IDs at compile time.
