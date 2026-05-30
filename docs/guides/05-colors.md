# Guides: Color Reference

CatLang's `Colors` class provides named color constants for UI elements.

## Usage

```python
on loaded:
    # Set background to a named color
    look_set_prop("Background Color", myFrame, Colors.navy)
    look_set_prop("Background Color", myButton, Colors.red)
    look_set_prop("Background Color", myText, Colors.white)

    # Or use hex directly
    look_set_prop("Background Color", myLabel, "#81b64c")
```

## Color Names

### Grayscale

| Name | Hex | Preview |
|---|---|---|
| `Colors.white` | `#ffffff` | ⬜ |
| `Colors.snow` | `#f0f0f0` | ⬜ |
| `Colors.silver` | `#e0e0e0` | ⬜ |
| `Colors.lightGray` | `#c8c8c8` | ⬜ |
| `Colors.gray` | `#969696` | ⬜ |
| `Colors.darkGray` | `#646464` | ⬜ |
| `Colors.dark` | `#323232` | ⬜ |
| `Colors.black` | `#000000` | ⬜ |

### Reds

| Name | Hex |
|---|---|
| `Colors.red` | `#ff0000` |
| `Colors.lightRed` | `#ff5959` |
| `Colors.darkRed` | `#c80000` |
| `Colors.crimson` | `#e94560` |

### Oranges

| Name | Hex |
|---|---|
| `Colors.orange` | `#ff8000` |
| `Colors.lightOrange` | `#ffa459` |
| `Colors.darkOrange` | `#c86400` |
| `Colors.brown` | `#aa5500` |

### Yellows

| Name | Hex |
|---|---|
| `Colors.yellow` | `#ffff00` |
| `Colors.lightYellow` | `#ffff59` |
| `Colors.darkYellow` | `#c8c800` |

### Greens

| Name | Hex |
|---|---|
| `Colors.green` | `#00ff00` |
| `Colors.lightGreen` | `#59ff59` |
| `Colors.darkGreen` | `#00c800` |
| `Colors.forestGreen` | `#55aa55` |

### Cyans

| Name | Hex |
|---|---|
| `Colors.cyan` | `#00ffff` |
| `Colors.darkCyan` | `#00c8c8` |
| `Colors.teal` | `#00aaaa` |

### Blues

| Name | Hex |
|---|---|
| `Colors.blue` | `#0000ff` |
| `Colors.lightBlue` | `#5959ff` |
| `Colors.darkBlue` | `#0000c8` |
| `Colors.navy` | `#0f3460` |
| `Colors.indigo` | `#5555aa` |
| `Colors.midnight` | `#1a1a2e` |
| `Colors.deepPurple` | `#533483` |

### Magentas

| Name | Hex |
|---|---|
| `Colors.magenta` | `#ff00ff` |
| `Colors.darkMagenta` | `#c800c8` |
| `Colors.purple` | `#aa00aa` |

## Using Colors with the Color Picker

In the web editor:

1. **Properties panel** - Click the color swatch next to any color property to open the picker
2. **Code editor** - Hover a hex value (`#ff0000`) for 500ms to open the picker
3. **Presets tab** - Click a BrickColor hexagon to select instantly
4. **Advanced tab** - Drag the hue slider and saturation square for custom colors
5. **Hex input** - Type a hex value directly

## Code Autocomplete

Type `Colors.` in the Monaco editor to see all available color names.
