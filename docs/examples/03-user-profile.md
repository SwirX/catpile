# Examples: User Profile Manager

A multi-script project demonstrating tables, foreach loops, multi-return actions, and the project build system.

## Project Structure

```
profile_app/
├── .catpilerc              # Project config
├── data.cat                # User data and initialization
├── display.cat             # Rendering and UI updates
└── page.catui              # UI hierarchy
```

## 1. Data Management Script

```python
script "data":
    on loaded:
        init_database()

    fn init_database():
        users = {
            "alice": {"age": 28, "role": "admin"},
            "bob": {"age": 22, "role": "editor"},
            "charlie": {"age": 35, "role": "viewer"},
        }
        log("Database initialized with {users}")

    fn add_user(name, age, role):
        o_entry = create_table()
        table_set(age, "age", o_entry)
        table_set(role, "role", o_entry)
        table_set(o_entry, name, users)
        log("Added user {name}")

    fn get_user(name):
        return table_get(name, users)
```

**Key concepts:**
- `script "name":` — names this script in the multi-script project
- `create_table()` — creates an empty table at runtime
- `table_set` and `table_get` — read and write table entries
- `return` — returns a value from a function

## 2. Display Script

```python
script "display":
    on loaded:
        render_userlist()

    fn render_userlist():
        foreach(users):
            o_name = l_index
            o_data = l_value
            o_role = table_get("role", o_data)
            log("{o_name} - {o_role}")
            settext("user_{o_name}", "{o_name} ({o_role})")

    fn show_user_detail(name):
        o_data = table_get(name, users)
        o_age = table_get("age", o_data)
        o_role = table_get("role", o_data)
        settext("detailName", "Name: {name}")
        settext("detailAge", "Age: {o_age}")
        settext("detailRole", "Role: {o_role}")
        show("detailPanel")
```

**Key concepts:**
- `foreach(users):` — iterates over a table; `l_index` is the key, `l_value` is the value
- Cross-script function calls via `func_run`

## 3. Interactive Profile Panel

```python
script "ui_handlers":
    on pressed("addUserBtn"):
        o_name = input_get_text("nameInput")
        o_age = input_get_text("ageInput")
        o_role = input_get_text("roleInput")
        func_run("add_user", o_name, o_age, o_role)
        func_run("render_userlist")

    on pressed("refreshBtn"):
        func_run("render_userlist")

    on pressed("clearBtn"):
        settext("nameInput", "")
        settext("ageInput", "")
        settext("roleInput", "")
        hide("detailPanel")
```

**Key concepts:**
- `input_get_text("field")` — reads a text input value
- `func_run("name", args...)` — calls a function defined in another script
- Multiple return values: `WIDTH, HEIGHT = input_get_viewport()`

## 4. Multi-Return Example

```python
on loaded:
    WIDTH, HEIGHT = input_get_viewport()
    log("Viewport: {WIDTH} x {HEIGHT}")
```

Some CatWeb actions return multiple values. Assign them with comma-separated variables.

## 5. Project Config (.catpilerc)

The project system uses a `.catpilerc` file to know which page to build:

```json
{
    "page": "page.json",
    "taste": "indent",
    "default_scope": "local"
}
```

Build with:
```bash
cpile build
```

This compiles all scripts, resolves UI references, and outputs the final page JSON.

## Summary

| Concept | Example | Purpose |
|---------|---------|---------|
| Named script | `script "data":` | Organize multi-file projects |
| Create table | `create_table()` | New empty table |
| Table set/get | `table_set(k, v, t)` | Read/write table entries |
| Foreach | `foreach(t):` | Iterate over all entries |
| Multi-return | `a, b = fn()` | Capture multiple outputs |
| Cross-call | `func_run("fn", arg)` | Call function in another script |
| Read input | `input_get_text("id")` | Get UI text field value |
| Project build | `cpile build` | Compile full project |
