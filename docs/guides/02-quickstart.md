# Guides: Quickstart Tutorial

Build your first Catpile project in 10 minutes.

## Step 1: Write a Script

Create `hello.cat`:

```python
on loaded:
    log("Hello World!")
    DATA_LOADED = 0
    WIDTH, HEIGHT = input_get_viewport()
    CONTAINER_SIZE = HEIGHT * .9
    ITEM_SIZE = CONTAINER_SIZE / 10
    log("Container size: {CONTAINER_SIZE}")
    DATA_LOADED = 1
```

## Step 2: Compile

```bash
python3 -m catpile.cli hello.cat -o hello.json
```

Output (`hello.json`):
```json
[
  {
    "class": "script",
    "globalid": "aB",
    "content": [
      {
        "text": ["When website loaded..."],
        "actions": [
          {"id": 0, "text": [{"value": "Hello World!", "t": "any"}]},
          {"id": 11, "text": [{"value": "DATA_LOADED", "l": "variable", "t": "string"}, "to", {"value": "0", "t": "any"}]},
          {"id": 84, "text": [{"value": "WIDTH", "l": "x", "t": "string"}, {"value": "HEIGHT", "l": "y", "t": "string"}]},
          ...
        ]
      }
    ],
    "alias": "hello",
    "enabled": "true"
  }
]
```

## Step 3: Add a Function

Edit `hello.cat`:

```python
on loaded:
    init_game()

fn init_game():
    log("Initializing application")
    USERS = create_table()
    SESSION_LOG = create_table()
    DATA_LOADED = 0
    WIDTH, HEIGHT = get_viewport()
    CONTAINER_SIZE = HEIGHT * .9
    ITEM_SIZE = CONTAINER_SIZE / 10
    log("Ready")
    DATA_LOADED = 1
```

## Step 4: Add UI Interaction

```python
on loaded:
    hide(page.LoadingScreen)
    log("Page ready")

on pressed("startButton"):
    if eq(DATA_LOADED, 1):
        show("gameArea")
        hide("menu")
        log("App started")
```

## Step 5: Use the Web Editor

Open [cpile.bouyakhsass.com](https://cpile.bouyakhsass.com):

1. Click **Import** and paste a CatWeb JSON file
2. Scripts are decompiled and shown in the Explorer
3. Click a script to edit it in the code editor
4. Click a UI element to see/edit its properties
5. Click **Full Project** to compile everything
6. Download `compiled.json` for CatWeb import

## Step 6: Multi-Script Project

```python
script "loading":
    on loaded:
        init_game()

script "game":
    on loaded:
        show(gameArea)
        update_ui()

script "utils":
    fn init_game():
        log("Init")
    
    fn update_ui():
        log("UI updated")
```

## Step 7: Using the Colors Class

```python
on loaded:
    look_set_prop("Background Color", frame, Colors.navy)
    look_set_prop("Background Color", button, Colors.red)
    look_set_prop("Background Color", tile, Colors.white)
```

## Step 8: Compile the Project

```bash
# Compile all scripts
cat *.cat | cpile -o project.json

# Or use the web editor's Full Project button
# to compile and download in one click
```
