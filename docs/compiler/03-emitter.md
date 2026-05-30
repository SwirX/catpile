# Compiler: Emitter

The emitter converts IR to CatWeb JSON actions. It's the final compilation stage before the builder.

## Schema-Based Compilation

The emitter uses `schema.json` to know how to format each action. For each action:

1. Load the action's schema from `schema.json`
2. Map each IR argument to the correct schema slot
3. Handle `{}` wrapping based on slot type
4. Generate global IDs

### Slot Types and Braces

The schema defines slot types (`t` field) that control `{}` wrapping:

| Slot Type | Example | Wrapping |
|---|---|---|
| `variable` | `l!count` | Bare | 
| `object` | `@<` (globalid) | Bare |
| `string` | `"hello"` | Quoted |
| `any` | `5` or `{var}` | String or `{var}` |
| `number` | `5` | Numeric |

When compiling, a `VarRef("l!count")` is emitted as:
- `l!count` (bare) for variable/object slots
- `{l!count}` for string/any slots

This is handled in `make_action()` in `mappings.py`:

```python
# For variable/object slots: strip {}
if param.get("t") == "object" or param.get("l") == "variable":
    value = v[1:-1]  # strip {braces}
```

## String Interpolation

`InterpolatedStr` with multiple parts generates `STR_CONCAT` chains:

```python
# "Hello {name}!" 
# → CONCAT("Hello ", {name}, "!")
```

A single `{var}` with no surrounding text produces a direct `VarRef` (no concat).

## Math Expressions

`MathExpr` generates variable math actions:

```python
# {x} * {ITEM_SIZE}
# → MUL x, ITEM_SIZE
```

## Dict Literals

`DictLiteral` expands to TABLE_CREATE + TABLE_SET chains:

```python
# {"l": "ebecd0", "d": "779556"}
# → TABLE_CREATE
# → TABLE_SET "l", table, "ebecd0"
# → TABLE_SET "d", table, "779556"
```

## Control Flow

IF, REPEAT, FOREACH statements expand to BEGIN → body → END:

```
IF a, b            →  IF action
    LOG "equal"    →  LOG "equal"
ELSE               →  ELSE
    LOG "diff"     →  LOG "diff"
                   →  END (id 25)
```

## Coordinate Placement

Events are placed on a virtual grid so they don't overlap in the CatWeb editor:

```python
BASE_X = 400
SPACING_X = 450
event_positions = {}
current_x = BASE_X
y_offset = 0

for event in script.events:
    x = current_x
    y = 100 + y_offset
    event_positions[event.id] = (x, y)
    y_offset += len(event.body) * 20
    current_x += SPACING_X
```

## Action Chunking

If an event has more than 120 actions (CatWeb limit), it's split:

```python
MAX_ACTIONS = 120

if len(actions) > MAX_ACTIONS:
    chunks = [actions[i:i+MAX_ACTIONS] 
              for i in range(0, len(actions), MAX_ACTIONS)]
    return [{"id": 0, "text": ["When website loaded..."], 
             "actions": chunk} 
            for chunk in chunks]
```

## Global ID Generation

Every action gets a unique 2-3 character global ID:

```python
import random, string
def new_id():
    chars = string.ascii_letters
    return ''.join(random.choices(chars, k=2))
```

IDs are short (2-3 chars) to minimize file size.

## Action Class Construction

The `make_action()` function in `mappings.py` handles slot filling:

```python
def make_action(action_name, *values, idgen=None):
    slots = schema[action_name]  # Load from schema.json
    text = []
    for slot in slots:
        if slot["type"] == "plain":
            text.append(slot["text"])
        else:
            param = dict(slot)
            param["value"] = next(values)  # Fill value
            text.append(param)
    return {"id": schema_id, "text": text, "globalid": idgen()}
```
