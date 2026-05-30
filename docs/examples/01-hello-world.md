# Examples: Hello World

The simplest CatLang program — an introduction to events, logging, and variables.

## 1. Your First Script

```python
on loaded:
    log("Hello World!")
```

**What happens:**
- `on loaded:` runs when the page finishes loading
- `log(...)` prints text to the CatWeb console

## 2. Using Variables

```python
on loaded:
    name = "Alice"
    log(name)
```

Variables store values. `name = "Alice"` creates a variable and assigns it a string. The `log` action prints its value.

## 3. String Interpolation

```python
on loaded:
    name = "Alice"
    score = 95
    log("Player {name} scored {score} points")
```

Curly braces `{ }` inside strings insert variable values at runtime. This compiles to a `STR_CONCAT` chain automatically.

## 4. Multiple Actions

```python
on loaded:
    title = "Dashboard"
    version = 2.5
    log("Loading {title} v{version}")
    log("Ready!")
```

Actions run in order, top to bottom. You can use constants, variables, and interpolation in any combination.

## 5. Multi-Script Wrapper

For CatWeb import, wrap your script:

```python
script "main":
    on loaded:
        log("Hello from Catpile!")
```

The `script` directive names your script. When built through the project system, multiple scripts merge into a single page JSON.

## Summary

| Concept | Syntax | Purpose |
|---------|--------|---------|
| Event | `on loaded:` | Trigger code on page load |
| Log | `log("text")` | Print to console |
| Variable | `name = "value"` | Store values |
| Interpolation | `"Hello {name}"` | Insert variables into strings |
| Named script | `script "main":` | Wrap code for projects |
