# Examples: Interactive Button

Learn events with parameters, conditions, loops, and functions.

## 1. Button Click Counter

```python
on loaded:
    clicks = 0
    settext("label", "Clicked 0 times")

on pressed("incrementBtn"):
    inc(clicks, 1)
    settext("label", "Clicked {clicks} times")
```

**What happens:**
- Page loads: counter starts at 0, label shows "Clicked 0 times"
- Button pressed: counter increments, label updates

Key concepts:
- `on pressed("btnId")` — event triggered by clicking a specific UI element
- `inc(var, amount)` — increments a variable
- `settext("element", "text")` — updates a UI element's text

## 2. Adding a Condition

```python
on loaded:
    clicks = 0
    settext("label", "Clicked 0 times")

on pressed("incrementBtn"):
    inc(clicks, 1)
    if gte(clicks, 10):
        settext("label", "Max reached!")
        hide("incrementBtn")
    else:
        settext("label", "Clicked {clicks} times")
```

When clicks reaches 10, the label changes to "Max reached!" and the button disappears. The `if`/`else` block uses CatWeb's condition actions (`gte`, `eq`, etc.).

## 3. Using Functions

```python
on loaded:
    reset_counter()

on pressed("incrementBtn"):
    inc(clicks, 1)
    update_label()

on pressed("resetBtn"):
    reset_counter()

fn reset_counter():
    clicks = 0
    update_label()

fn update_label():
    settext("label", "Clicked {clicks} times")
```

Functions (`fn name():`) group reusable logic. They can be called from events and other functions.

## 4. Loops and Delay

```python
on pressed("autoBtn"):
    repeat(5):
        inc(clicks, 1)
        update_label()
        wait(0.5)

fn update_label():
    settext("label", "Count: {clicks}")
```

`repeat(n)` runs a block `n` times. `wait(seconds)` pauses between iterations.

## 5. Theme Switcher (Using Dicts)

```python
themes = {
    "light": {"bg": "#ffffff", "fg": "#000000"},
    "dark": {"bg": "#1a1a2e", "fg": "#e0e0e0"},
}

on loaded:
    current = "light"

on pressed("themeLight"):
    current = "light"
    apply_theme()

on pressed("themeDark"):
    current = "dark"
    apply_theme()

fn apply_theme():
    colors = table_get(current, themes)
    bg = table_get("bg", colors)
    fg = table_get("fg", colors)
    set_prop("Background Color", "pageBg", bg)
    set_prop("Text Color", "pageText", fg)
```

Demonstrates dict literals (`{key: value, ...}`) which compile to `TABLE_CREATE` + `TABLE_SET` chains, and `table_get` for runtime lookup.

## Summary

| Concept | Example | Purpose |
|---------|---------|---------|
| Button event | `on pressed("btn"):` | React to UI clicks |
| Increment | `inc(x, 1)` | Add to a variable |
| Condition | `if gte(x, 10):` | Branch on comparison |
| Show/hide | `hide("btn")` | Toggle UI visibility |
| Function | `fn name():` | Define reusable logic |
| Loop | `repeat(5):` | Repeat a block |
| Dict literal | `data = {"k": "v"}` | Create tables inline |
