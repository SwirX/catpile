# Compiler: Schema Parser

The schema parser fetches and parses the CatWeb action schema from the upstream repository, providing accurate slot types and output variable positions for the compiler and decompiler.

## Module: `catpile/schema_parser.py`

### Source

The schema is fetched from:
```
https://raw.githubusercontent.com/quitism/catlua/main/docs/schema.md
```

This markdown file defines all CatWeb actions with their slot types.

### Schema Format

Each action is defined as:

```
## ID_0 | LOG

Action text: `Log {value:any}`

Output: ``

- `{value:any}`: ...
```

The parser extracts:
- **Action ID** (e.g., `0` for LOG)
- **Action name** (e.g., `LOG`)
- **Slots** with their names and types
- **Output slots** - slots marked after `→`

### Extracted Data

```python
@dataclass
class SlotInfo:
    name: str         # Slot name ("value", "entry", etc.)
    slot_type: str    # Type ("string", "number", "any", "object")
    optional: bool    # Whether the slot is optional
    is_output: bool   # Whether it's an output variable
```

### Usage

```python
from catpile.schema_parser import get_schema, get_output_slots

# Load schema
schema = get_schema()

# Get output slots for an action
outputs = get_output_slots(55, schema)  # TABLE_SET
# → [] (no output)

outputs = get_output_slots(56, schema)  # TABLE_GET
# → [2] (index 2 is output)

outputs = get_output_slots(84, schema)  # GET_VIEWPORT
# → [0, 1] (x and y are both outputs)
```

## Integration Points

### Decompiler

The decompiler uses the schema to:

1. **Detect output variables** - only slots marked as `is_output` trigger assignment syntax:
   ```python
   # TABLE_GET with output at index 2:
    o_bgColor = table_get("bg", app_config)
    # Not: default = table_set("default", app_config, default)
   ```

2. **Filter empty optional outputs** - optional outputs with `""` value are skipped:
   ```python
   func_run("function_name", arg)  # No assignment for empty optional
   ```

3. **Determine bare vs quoted output** - variable slots use bare names:
   ```python
    l_username = input_get_text("field")     # l_username is bare (variable slot)
   WIDTH, HEIGHT = get_viewport()      # Both bare (output slots)
   ```

### Emitter

The emitter uses the schema to:

1. **Determine `{}` wrapping** - object/variable slots get bare names:
   ```python
   # Variable slot: bare
    look_set_prop("Name", o_header, {l!index})
   # → "value": "o!board" (object slot, bare globalid)
   
   # Any slot: wrapped
   look_set_prop("Property", target, "{l!value}")
   # → "value": "{l!value}" (any slot, wrapped)
   ```

2. **Match arguments to slots** - each IR argument is matched to the correct schema slot

### Schema Cache

The parsed schema is cached in `catpile/schema.json` for fast loading without network requests. The live fetcher (`load_schema()`) updates the cache from the upstream repo.
