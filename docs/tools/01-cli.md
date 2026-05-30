# Tools: CLI Reference

The `cpile` command-line tool compiles `.cat` files to CatWeb JSON.

## Basic Usage

```bash
# Compile a single file
cpile script.cat

# Output to file
cpile script.cat -o output.json

# Compile and print
cpile script.cat --stdout
```

## Command Line

```
usage: cpile [-h] [-o OUTPUT] [-t TASTE] [--stdout] [--debug] 
             [--catui CATUI] [-O {0,1,2,3}]
             [file]

Compile CatLang (.cat) to CatWeb JSON.

positional arguments:
  file                  .cat file to compile (default: stdin)

options:
  -h, --help            Show help message
  -o, --output OUTPUT   Output file (default: stdout)
  -t, --taste TASTE     Syntax taste: indent (default) or bracket
  --stdout              Print compiled JSON to stdout
  --debug               Print full AST before emitting
  --catui CATUI         Path to .catui file for UI path resolution
  -O {0,1,2,3}          Optimization level (default: 1)
```

### Examples

```bash
# Compile with bracket syntax
cpile --taste bracket script.cat -o output.json

# Compile with optimization level 2
cpile -O2 script.cat -o output.json

# Compile with .catui for path references
cpile --catui page.catui script.cat -o output.json

# Pipe from stdin
echo 'on loaded: log("hello")' | cpile

# Debug output
cpile --debug script.cat
```

## Programmatic Usage

```python
from catpile.parser import parse
from catpile.emitter import Emitter
from catpile.optimizer import optimize

# Parse
program = parse(source_text, taste="indent")

# Optimize
program = optimize(program, level=1)

# Emit
emitter = Emitter()
output = emitter.emit(program)

# Save
import json
with open("output.json", "w") as f:
    json.dump(output, f, indent=2)
```

## Configuration File

Catpile reads `.catpilerc` from the project root for default settings:

```json
{
  "taste": "indent",
  "optimization": 1,
  "catui": "page.catui"
}
```

## Multi-File Projects

For projects with multiple `.cat` files:

```bash
cat scripts/*.cat | cpile -o combined.json
```

Or use the builder:

```python
from catpile.builder import Builder

builder = Builder()
builder.add_file("movement.cat")
builder.add_file("utils.cat")
builder.link_ui("page.catui")
builder.build("output.json")
```

## Error Messages

Compiler errors include script name and local line number:

```
[data_handler] Expected NUMBER, got IDENT='l_value' at line 14
```

Format: `[script_name] Error description at line line_number`
