# Tastes — Different Ways to Write the Same Thing

Ever had to write a school essay in two different languages? The story is the same, just the words change. That's what **tastes** do for CatLang.

A taste is just a different "accent" for writing CatLang code. You pick whichever one feels most comfortable to you. They all produce the same CatWeb JSON at the end — no difference in what your buttons do, how your scripts run, or what your page looks like.

**In simple terms:** It's like choosing between British and American spelling. "Colour" vs "color" — different letters, same meaning. CatLang has two accents: **indent** (Python style) and **bracket** (JS style). Pick the one that looks right to you.

---

## How It Works (For The Curious)

```
Your Code → [Taste Reader] → Middle Step → [Output Builder] → CatWeb JSON
```

The "taste reader" takes whatever style you wrote in and turns it into a middle format. The "output builder" doesn't care which style you used — it just builds the JSON from that middle format. This means **all tastes are equally powerful**. Nothing is locked behind one style.

## The Two Tastes

### Indent Taste (default — recommended for beginners)

Uses colons `:` and indentation (like Python). Clean, easy to read:

```python
script "game":
    on loaded:
        l_username = input_get_text("username")
        log("{l_username}")

    fn setup():
        create_table("items")
        log("Ready")
```

If you've never coded before, start here. It's the simplest to read and write.

### Bracket Taste

Uses curly braces `{ }` and semicolons `;` (like JavaScript, C++, C#):

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

If you're already comfortable with JS or C-style languages, this'll feel like home.

## How to Switch

Pick your taste when you run Catpile:

```bash
cpile --taste indent my_script.cat
cpile --taste bracket my_script.cat
```

Or save it in your project config so you don't have to type it every time:

```json
{"taste": "bracket"}
```

---

## For Developers: Adding a New Taste

Want to add your own style? Each taste is just a class that reads code and spits out the same middle format.

### 1. Create the reader file

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

### 2. Register it

```python
# catpile/tastes/registry.py
from .lua import LuaTaste

TASTES = {
    "indent": "catpile.parser.CatpileParser",
    "bracket": "catpile.tastes.bracket.BracketTaste",
    "lua": LuaTaste,  # Add yours
}
```

### 3. What your reader must handle

- Script headers (`script "name":`)
- Event handlers (`on loaded:`, `on pressed("btn"):`)
- Function definitions (`fn name(params):`)
- Control flow (`if/else`, `repeat`, `foreach`, `break`, `return`)
- Variables and scope prefixes
- String interpolation (`{var}` inside strings)
- Dict/list literals (`{key: val}`, `[item, item]`)
- Math expressions (`x + y * 2`)

### Key Patterns

```python
# Function detection
if token.kind == "IDENT" and token.value == "fn":
    # function: fn {name}({params}): {body}

# Event detection
if token.kind == "IDENT" and token.value == "on":
    # event: on {name}["("{target}")"]: {body}

# Statement dispatch
if token.value in ("if", "elseif", "else"):
    # conditionals
elif token.value == "repeat":
    # loops
elif token.value == "foreach":
    # foreach loops
elif token.value == "break":
    # break
else:
    # action call
```

## Adding VSCode Syntax Highlighting

See [VSCode Extension Guide](../tools/03-vscode.md).
