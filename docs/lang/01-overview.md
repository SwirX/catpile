# CatLang: Overview & Syntax

CatLang is the human-readable DSL (Domain-Specific Language) that Catpile compiles to CatWeb JSON. It is designed to be familiar to Python developers while mapping directly to CatWeb's action/event system.

<SyntaxBreakdown pattern="event-handler" />

<SyntaxBreakdown pattern="action-call" />

## File Format

CatLang files use the `.cat` extension. Each file contains one or more **scripts**, where a script is defined by events and functions.

```
.cat → Catpile → CatWeb JSON
```

## Indentation Rules

CatLang uses **indentation to define blocks**, like Python. Tabs or spaces work, but **4 spaces** is the convention.

```python
on loaded:               # Level 0
    log("hello")          # Level 1 - body of "loaded"
    if eq(x, 1):          # Level 1
        log("equal")      # Level 2 - body of "if"
```

A block ends when the next line is dedented (less indentation) than the block opener. **Blank lines are ignored** for indentation purposes.

## Empty Blocks

Blocks with no body are valid:

```python
if exists("table"):
# body is empty - parser handles gracefully
```

## Comments

```python
# Everything after # is a comment

on loaded:
    log("hello")  # Inline comment
```

## Identifiers

Identifiers are names for variables, functions, event handlers, and parameters.

- Must start with a letter or underscore
- Can contain letters, digits, underscores
- **Dots** are allowed for UI path references: `page.FileLoader.Load`

```python
my_var = 5
o_header = look_duplicate("T5")
page.ThemesSelect.Button = hide()  # Dotted path reference
```

## Strings

Strings use double quotes:

```python
msg = "hello world"
log("Hello!")
```

Strings support **variable interpolation** (see Expressions):

```python
on loaded:
    name = "SwirX"
    log("Welcome {name}!")  # → STR_CONCAT: "Welcome " + {name} + "!"
```

## Numbers

Numbers can be integers or decimals:

```python
count = 5
wait(1.5)
repeat(8):
```

Floats without a leading digit are normalized: `.1` becomes `0.1`

## Variable References

Variables in the CatWeb JSON format use `{varname}` syntax. In CatLang, you write them directly with scope prefixes or bare identifiers depending on the context.

**In action arguments:** bare identifiers are variable references

```python
log(my_var)     # LOG with value {my_var}
```

**In strings:** `{varname}` triggers interpolation

```python
log("Value is {my_var}")  # STR_CONCAT or direct {my_var}
```

**In statements:** bare names are variable assignments or references

```python
x = 5            # VAR_SET name="x" value="5"
inc(x, 1)        # VAR_INC name="x" amount="1"
```

## Scope Prefixes

Variables can have scope prefixes that map to CatWeb's `scope!name` format:

| Source | CatWeb | Scope |
|--------|--------|-------|
| `l_count` | `l!count` | Local - same script |
| `o_header` | `o!header` | Object - scoped to a UI element |
| `count` | `count` | No prefix = global (default) |

Double underscore escapes: `l__name` → `l_name` (literal)

## Tastes — Pick Your Style

Not everyone likes writing code the same way. Some people prefer Python style (colons and indentation), others prefer JS style (curly braces and semicolons). **Tastes** let you choose.

Think of it like writing a sentence in English vs. the same sentence in Spanish — the words are different, but the meaning is exactly the same. CatLang has two "accents" (we call them **tastes**):

| Taste | Looks like | Who it's for |
|-------|-----------|--------------|
| **indent** (default) | Colons `:` and indentation | People who like Python |
| **bracket** | Curly braces `{ }` and semicolons `;` | People who like JS / C++ / C# |

Both produce the exact same result. It's just whichever feels more natural to *you*.

### Switch between tastes

```bash
cpile --taste indent my_script.cat
cpile --taste bracket my_script.cat
```

Or set it in your project config so you don't have to type it every time. See [Tastes — Pick Your Style](09-tastes.md) for all the details.
