# Compiler: Taste System

Tastes are syntax variants - alternative ways to write CatLang that compile to the same JSON.

## Architecture

```
User Code → [Taste Parser] → IR → [Emitter] → CatWeb JSON
             ↕
        Taste Base Class
        (tastes/__init__.py)
```

Tastes implement a parser that produces the same IR types. The emitter and optimizer don't care which taste produced the IR.

## The Taste Base Class

```python
# catpile/tastes/__init__.py
class Taste(ABC):
    @abstractmethod
    def parse(self, source: str) -> Program:
        """Tokenize and parse source text → IR Program."""
        pass
```

Each taste implements `parse()` accepting source text, returning an IR `Program`.

## Built-in Tastes

### Indent Taste (default)

Python-style - uses `:` and indentation for blocks, newlines for statement separation:

```python
script "game":
    on loaded:
        l_username = input_get_text("username")
        log("{l_username}")

    fn setup():
        create_table("items")
        log("Ready")
```

**Files:**
- `catpile/parser.py` - Tokenizer + parser
- Includes: `_parse_script()`, `_parse_event()`, `_parse_function()`, `_parse_body()`, `_parse_if_stmt()`, `_parse_repeat_stmt()`, `_parse_foreach_stmt()`, `_parse_action_call()`

### Bracket Taste

JS-like - uses `{ }` for blocks and semicolons for statement separation:

```python
script "game" {
    on loaded {
        l_username = input_get_text("username");
        log("{l_username}");
    }

    fn setup() {
        create_table("items");
        log("Ready");
    }
}
```

**Files:**
- `catpile/tastes/bracket.py` - Tokenizer + parser
- Same IR output as indent taste

## Choosing a Taste

```bash
cpile --taste indent script.cat
cpile --taste bracket script.cat
```

Or set in `.catpilerc`:

```json
{"taste": "bracket"}
```

## Adding a New Taste

### 1. Create the parser file

```python
# catpile/tastes/lua.py
from catpile.tastes import Taste
from catpile.ir import Program

class LuaTaste(Taste):
    def parse(self, source: str) -> Program:
        # Your tokenizer + parser here
        # Must return IR Program
        pass
```

### 2. Register the taste

```python
# catpile/tastes/registry.py
from .lua import LuaTaste

TASTES = {
    "indent": "catpile.parser.CatpileParser",
    "bracket": "catpile.tastes.bracket.BracketTaste",
    "lua": LuaTaste,  # Add yours
}
```

### 3. Implement the parser

Your parser must:
- Tokenize the source text
- Produce a `Program` with `ScriptDef`s containing `EventDef`s and `FunctionDef`s
- Use IR types from `catpile.ir`

### Key Parsing Patterns

```python
# Function detection
if token.kind == "IDENT" and token.value == "fn":
    # Parse function definition:
    # fn {name}({params}):
    #     {body}

# Event detection
if token.kind == "IDENT" and token.value == "on":
    # Parse event handler:
    # on {name}["("{target}")"]:
    #     {body}

# Statement dispatch
if token.value in ("if", "elseif", "else"):
    # Parse conditionals
elif token.value == "repeat":
    # Parse repeat loops
elif token.value == "foreach":
    # Parse foreach loops
elif token.value == "break":
    # Parse break statements
else:
    # Parse as action call
```

## Adding VSCode Syntax Highlighting

See [VSCode Extension Guide](../tools/03-vscode.md).

## Taste Compatibility

All tastes must support:
- Script directives (`script "name":`)
- Event handlers (`on loaded:`, `on pressed("btn"):`)
- Function definitions (`fn name(params):`)
- Control flow (`if/else`, `repeat`, `foreach`, `break`, `return`)
- Variables and scope prefixes
- String interpolation
- Dict/list literals
- Math expressions
