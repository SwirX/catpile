# CatUI DSL Language Reference

CatUI is an indentation-based DSL for declaring CatWeb UI element trees in `.catui` files. It is the UI counterpart to CatLang (`.cat`): CatLang defines *behavior* (events, actions, scripts), while CatUI defines *layout* (frames, text, buttons, styling).

## File Format

CatUI files use the `.catui` extension. Each file describes one page layout.

## Page Block

Every `.catui` file starts with a `page` block:

```python
page "page_name":
    # page-level properties (optional)
    # child elements
```

The page name is a string that identifies the page for path references.

### Page-Level Properties

Properties at the top of the page block become page metadata in the compiled JSON:

```python
page "main":
    background = "#202020"
    title = "My App"
    description = "A sample application"
```

Common page-level properties:

| DSL Key | JSON Key | Example |
|---------|----------|---------|
| `background` | `background` | `"#202020"` |
| `title` | `title` | `"My App"` |
| `description` | `description` | `"Sample app"` |
| *any key* | *same key* | Arbitrary page metadata |

Page-level properties round-trip: they are preserved through decompilation → edit → recompilation.

## Element Syntax

```python
class_name alias [annotations]:
    property = value
    child_element...
```

| Part | Description | Required |
|------|-------------|----------|
| `class_name` | DSL alias or full CatWeb class name | Yes |
| `alias` | Unique name for path references | Yes |
| `[annotations]` | Square-bracketed key/value pairs | No |
| `:` | Colon marks the element header | Yes |
| `property = value` | Element properties (indented) | No |
| `child_element...` | Nested sub-elements (indented) | No |

### Element Class Names

Use the short DSL alias or the full CatWeb class name:

```python
# DSL aliases (recommended)
frame main_frame:
textlabel title:
textbutton submit:

# Full class names also work
Frame main_frame:
TextLabel title:
TextButton submit:
```

Full element alias table:

| DSL Alias(es) | CatWeb Class | Category |
|---------------|-------------|----------|
| `frame` | `Frame` | Container |
| `scrollingframe`, `scrollframe` | `ScrollingScrollFrame` | Container |
| `folder` | `Folder` | Organizational |
| `textlabel`, `label` | `TextLabel` | Text |
| `textbutton`, `button` | `TextButton` | Text |
| `textbox`, `input` | `TextBox` | Text |
| `imagelabel`, `image` | `ImageLabel` | Image |
| `link` | `TextButton?link` | Link |
| `donation` ⚠️ | `TextButton?donation` | Donation [^deprecated](#Footnotes) |
| `transfer` | `TextButton?transfer` | Transfer |
| `avataritem` | `TextButton?avataritem` | Avatar Item |
| `uicorner`, `corner` | `UICorner` | Styling |
| `uistroke`, `stroke` | `UIStroke` | Styling |
| `uigradient`, `gradient` | `UIGradient` | Styling |
| `uipadding`, `padding` | `UIPadding` | Styling |
| `uilistlayout`, `listlayout` | `UIListLayout` | Layout |
| `uigridlayout`, `gridlayout` | `UIGridLayout` | Layout |
| `uiaspectratioconstraint`, `aspectratioconstraint` | `UIAspectRatioConstraint` | Constraint |
| `uisizeconstraint`, `sizeconstraint` | `UISizeConstraint` | Constraint |
| `uitextsizeconstraint`, `textsizeconstraint` | `UITextSizeConstraint` | Constraint |

### Aliases

The alias is a unique name used to reference the element in CatLang scripts via path notation:

```python
# In .catui:
page "main":
    textbutton myButton [globalid: "abc123"]:
        text = "Click"

# In .cat script:
on pressed("myButton"):
    hide(Page.myButton)
```

Paths follow the pattern: `Page.{alias}` for top-level elements, `Page.{parent}.{child}` for nested elements.

### Annotations

Annotations are key-value pairs wrapped in square brackets after the alias:

```
textbutton submit [globalid: "btn_main"]:
```

The only built-in annotation is `globalid`, which sets an explicit global ID. If omitted, the emitter auto-generates one:

```python
textbutton submit:  # globalid auto-generated
textbutton submit [globalid: "my_gid"]:  # explicit globalid
```

### Properties

Properties are `key = value` pairs, one per line, indented under the element:

```python
frame container:
    size = "{1,0},{1,0}"
    bg = "#1a1a2e"
    position = "{0,0},{0,0}"
    visible = "true"
```

#### Property Aliases

Many properties have shorter DSL aliases:

| DSL Alias | JSON Property | Used On |
|-----------|--------------|---------|
| `bg` | `background_color` | All visible elements |
| `bgcolor`, `bg_col`, `bg_color` | `background_color` | All visible elements |
| `bg_transparency` | `background_transparency` | All visible elements |
| `bgtransparency`, `bg_trans` | `background_transparency` | All visible elements |
| `font_color` | `font_color` | Text elements |
| `fontcolor`, `font_col`, `textcolor`, `text_col` | `font_color` | Text elements |
| `font_size` | `font_size` | Text elements |
| `fontsize` | `font_size` | Text elements |
| `font_weight` | `font_weight` | Text elements |
| `fontweight` | `font_weight` | Text elements |
| `font_style` | `font_style` | Text elements |
| `fontstyle` | `font_style` | Text elements |
| `font_transparency` | `font_transparency` | Text elements |
| `fonttransparency` | `font_transparency` | Text elements |
| `align_x` | `align_x` | Text elements |
| `alignx`, `text_align` | `align_x` | Text elements |
| `align_y` | `align_y` | Text elements |
| `aligny` | `align_y` | Text elements |
| `img` | `image` | ImageLabel |
| `imageid` | `image_id` | ImageLabel |
| `image_trans` | `image_transparency` | ImageLabel |
| `imagecolor`, `img_color` | `image_color` | ImageLabel |
| `imgtransparency` | `image_transparency` | ImageLabel |
| `radius`, `corner_radius` | `radius` | UICorner |
| `border_color`, `outline_color` | `stroke_color` | UIStroke |
| `border_thickness`, `outline_thickness` | `stroke_thickness` | UIStroke |
| `border_transparency` | `stroke_transparency` | UIStroke |
| `border_mode` | `stroke_mode` | UIStroke |
| `border_type` | `stroke_type` | UIStroke |
| `scroll_thickness` | `scrollbar_thickness` | ScrollingFrame |
| `scroll_color` | `scrollbar_color` | ScrollingFrame |
| `scroll_transparency`, `scrollbartransparency` | `scrollbar_transparency` | ScrollingFrame |
| `list_direction`, `direction` | `direction` | UIListLayout |
| `list_padding`, `padding` | `padding` | UIListLayout/UIGridLayout |
| `grid_padding` | `padding` | UIGridLayout |
| `padding_top`, `top` | `top` | UIPadding |
| `padding_left`, `left` | `left` | UIPadding |
| `padding_right`, `right` | `right` | UIPadding |
| `padding_bottom`, `bottom` | `bottom` | UIPadding |
| `ratio`, `aspect_ratio` | `ratio` | UIAspectRatioConstraint |
| `min_size` | `min_size` | UISizeConstraint |
| `max_size` | `max_size` | UISizeConstraint |
| `min_text` | `min_text_size` | UITextSizeConstraint |
| `max_text` | `max_text_size` | UITextSizeConstraint |

#### Common Properties (all elements)

Most container and text elements share these:

| Property | Type | Example |
|----------|------|---------|
| `position` | UDim2 | `"{0,0},{0,0}"` |
| `size` | UDim2 or auto | `"{1,0},{1,0}"`, `"auto"` |
| `anchor` | Vector2 | `"0.5,0.5"` |
| `width` | UDim | `"{0,200}"` |
| `height` | UDim | `"{0,100}"` |
| `background_color` | Color | `"#1a1a2e"` |
| `background_transparency` | Number | `"0"` (opaque) to `"1"` (invisible) |
| `visible` | Bool | `"true"` or `"false"` |
| `rotation` | Number | `"45"` |
| `z_index` | Number | `"10"` |
| `clips_descendants` | Bool | `"true"` |
| `active` | Bool | `"true"` |

#### Text Element Properties

TextLabel, TextButton, and TextBox share these:

| Property | Type | Example |
|----------|------|---------|
| `text` | String | `"Welcome"` |
| `font` | Font | `"GothamBold"` |
| `font_size` | FontSize | `"30"` or `"scaled"` |
| `font_color` | Color | `"#ffffff"` |
| `font_weight` | FontWeight | `"Bold"` |
| `font_style` | FontStyle | `"Italic"` |
| `font_transparency` | Number | `"0"` to `"1"` |
| `align_x` | AlignX | `"Left"`, `"Center"`, `"Right"` |
| `align_y` | AlignY | `"Top"`, `"Center"`, `"Bottom"` |
| `line_height` | Number | `"1.5"` |
| `rich` | Bool | `"true"` |
| `wrap` | Bool | `"true"` |
| `truncate` | Truncate | `"AtEnd"`, `"None"`, `"SplitWord"` |
| `text_auto_resize` | Bool | `"true"` |

TextBox additionally:

| Property | Type | Example |
|----------|------|---------|
| `placeholder` | String | `"Enter name"` |
| `placeholder_color` | Color | `"#b2b2b2"` |
| `editable` | Bool | `"true"` |
| `multiline` | Bool | `"false"` |
| `clear_on_focus` | Bool | `"true"` |

TextButton additionally:

| Property | Type | Example |
|----------|------|---------|
| `auto_color` | Bool | `"true"` |

#### ImageLabel Properties

| Property | Type | Example |
|----------|------|---------|
| `image` | String | `"rbxassetid://70877710889686"` |
| `image_id` | String | `"107783162934966"` |
| `image_transparency` | Number | `"0"` to `"1"` |
| `image_color` | Color | `"#ffffff"` |
| `scale_type` | ScaleType | `"Crop"`, `"Fit"`, `"Slice"`, `"Stretch"`, `"Tile"` |
| `resample_mode` | Resample | `"Default"`, `"Pixelated"` |
| `slice_center` | Rect | `"10,10,10,10"` |

#### Frame / ScrollingFrame Properties

ScrollingFrame inherits all Frame properties plus:

| Property | Type | Example |
|----------|------|---------|
| `canvassize` | UDim2 | `"{0,0},{2,0}"` |
| `scrollbar_thickness` | Number | `"12"` |
| `scrollbar_color` | Color | `"#c8c8c8"` |
| `scrollbar_transparency` | Number | `"0"` to `"1"` |
| `elastic` | Bool | `"true"` |
| `scrolling_enabled` | Bool | `"true"` |
| `scrolling_direction` | Enum | `"Vertical"` |

#### Special Element Properties

**TextButton?link** additionally:

| Property | Type | Example |
|----------|------|---------|
| `href` | String | `"swirx.rbx"` |
| `new_tab` | Bool | `"true"` |

**TextButton?transfer** additionally:

| Property | Type | Example |
|----------|------|---------|
| `product` | String | `"Donation"` |
| `product_type` | String | `"GamePass"`, `"Asset"`, `"Product"` |
| `amount` | String | `"10"` |
| `recipient` | String | `"user123"` |

**TextButton?avataritem** additionally:

| Property | Type | Example |
|----------|------|---------|
| `product` | String | `"Hat"` |
| `product_type` | String | `"GamePass"`, `"Asset"`, `"Product"` |

**TextButton?donation**[^deprecated] additionally:

| Property | Type | Example |
|----------|------|---------|
| `product` | String | `"Donation"` |
| `product_type` | String | `"GamePass"`, `"Asset"`, `"Product"` |
| `thanks_href` | String | `"swirx.rbx/thanks"` |

### Property Value Types

| Type | DSL Format | Examples |
|------|-----------|---------|
| **String** | `"value"` | `"Hello"`, `"#1a1a2e"`, `"GothamBold"` |
| **Number** | `"value"` or bare number | `"12"`, `"3.14"`, `"0"` |
| **Bool** | `"true"` or `"false"` | `"true"` |
| **UDim2** | `"{scale,offset},{scale,offset}"` | `"{1,0},{1,0}"`, `"{0.5,0},{0,100}"` |
| **UDim** | `"{scale,offset}"` | `"{0,12}"`, `"{0.5,0}"` |
| **Vector2** | `"x,y"` | `"0.5,0.5"`, `"0,0"` |
| **Color** | `"#rrggbb"` or `"#rgb"` | `"#1a1a2e"`, `"#fff"` |
| **Font** | Font name string | `"GothamBold"`, `"Roboto"`, `"SourceSans"` |
| **Transparency** | `"0"` to `"1"` | `"0"` (fully opaque), `"1"` (invisible) |

## Nested Children

Elements with children indent them under the parent:

```python
page "main":
    frame container:
        size = "{1,0},{1,0}"

        textlabel header:
            text = "Title"
            font_size = "30"

        textbutton submit:
            text = "Click"
            uicorner round:
                radius = "0,8"
```

### Container Elements

These elements can have children:

- **Frame** — standard container, most common
- **ScrollingScrollFrame** — scrollable container with `canvassize`
- **Folder** — organizational container (invisible at runtime)

## Styling Elements

Styling elements are nested directly inside the element they modify. They have no children.

### UICorner

Rounds the corners of a parent element:

```python
textbutton btn:
    text = "Click"
    uicorner corner:
        radius = "0,8"      # UDim: {scale,offset}
```

### UIStroke

Adds a border/outline:

```python
frame panel:
    bg = "#ffffff"
    uistroke outline:
        stroke_color = "#333333"
        stroke_thickness = "2"
        stroke_transparency = "0"
```

### UIGradient

Applies a color gradient:

```python
frame gradient_bg:
    size = "{1,0},{1,0}"
    uigradient grad:
        rotation = "90"
        gradient_color = "[[0,\"#ff0000\"],[1,\"#0000ff\"]]"
        gradient_transparency = "[[0,0],[1,0.5]]"
```

### UIPadding

Adds padding inside the parent:

```python
frame padded:
    uipadding pad:
        padding_top = "0,10"
        padding_left = "0,15"
        padding_right = "0,15"
        padding_bottom = "0,10"
```

### UIListLayout

Arranges children in a list:

```python
frame list_container:
    uilistlayout layout:
        direction = "Vertical"
        padding = "0,5"
        alignment_horizontal = "Center"
        alignment_vertical = "Top"
```

### UIGridLayout

Arranges children in a grid:

```python
frame grid_container:
    uigridlayout grid:
        size = "{0.3,0},{0.3,0}"
        padding = "0,10"
        fill_direction_max_cells = "3"
```

### Constraints

**UIAspectRatioConstraint** — maintains aspect ratio:

```python
imagelabel avatar:
    image = "rbxassetid://..."
    uiaspectratioconstraint aspect:
        ratio = "1.77"
```

**UISizeConstraint** — limits minimum/maximum size:

```python
frame resizable:
    uisizeconstraint limit:
        min_size = "100,100"
        max_size = "500,500"
```

**UITextSizeConstraint** — limits text size range:

```python
textlabel title:
    text = "Responsive Text"
    uitextsizeconstraint txt:
        min_text_size = "12"
        max_text_size = "48"
```

## Script Placeholders

Script placeholders mark where compiled `.cat` scripts will be injected:

```python
script alias:
    source = "path/to/script.cat"
```

- **alias** — matches the `script "alias":` directive in the `.cat` file
- **source** — optional, relative path to the `.cat` source file

Scripts without a `source` are preserved as position markers (useful when decompiling pages where the original `.cat` source is unknown):

```python
page "main":
    textbox input:
        text = "Hello"
    script my_script:      # from decompilation, source unknown
```

During `cpile build`, the builder finds script elements with `source`, compiles the referenced `.cat` file, and merges the compiled script JSON into the placeholder position.

## Complete Example

```python
page "profile":
    background = "#1a1a2e"
    title = "User Profile"

    frame container:
        size = "{1,0},{1,0}"
        bg = "#16213e"

        textlabel header:
            text = "Welcome back!"
            font_size = "36"
            font_color = "#ffffff"
            align_x = "Center"
            position = "{0,0},{0,20}"

        frame card [globalid: "profile_card"]:
            size = "{0.8,0},{0.6,0}"
            bg = "#0f3460"
            position = "{0.1,0},{0.15,0}"
            uicorner round:
                radius = "0,12"
            uistroke border:
                stroke_color = "#e94560"
                stroke_thickness = "2"

            imagelabel avatar:
                size = "{0.2,0},{0.4,0}"
                image = "rbxassetid://70877710889686"
                position = "{0.05,0},{0.05,0}"
                uicorner circ:
                    radius = "0,999"

            textlabel username:
                text = "PlayerName"
                font_size = "24"
                font_color = "#ffffff"
                position = "{0.3,0},{0.1,0}"

            textbutton edit_btn:
                text = "Edit Profile"
                bg = "#e94560"
                font_color = "#ffffff"
                size = "{0.3,0},{0.12,0}"
                position = "{0.35,0},{0.7,0}"
                uicorner btn_round:
                    radius = "0,6"

            script profile_logic:
                source = "src/profile.cat"

    textbox search_input:
        size = "{0.3,0},{0.06,0}"
        position = "{0.7,0},{0.02,0}"
        placeholder = "Search..."
        placeholder_color = "#b2b2b2"
        editable = "true"
        bg = "#0f3460"
        font_color = "#ffffff"
        uicorner search_round:
            radius = "0,20"

    script main:
```

## Compiling CatUI DSL

### Via Project Build

Create `.catpilerc`:

```json
{
  "taste": "indent",
  "pages": [
    {
      "name": "profile",
      "catui": "ui/profile.catui",
      "output": "build/profile.json"
    }
  ]
}
```

Run:

```bash
cpile build
```

### Via Python API

```python
from catpile.catui_parser import parse_catui
from catpile.catui_emitter import emit_catui

# Parse CatUI DSL
with open("ui/profile.catui") as f:
    program = parse_catui(f.read())

# Emit to JSON string
json_str = emit_catui(program)
# json_str is either a JSON array (no page properties)
# or {"background": "...", "webcontent": [...]} (with page properties)
```

## Decompiling CatWeb JSON to CatUI DSL

```bash
# Full round-trip: scripts + UI layout + project config
cpile decompile page.json -o output-dir/

# UI layout only: just the CatUI DSL, no scripts
cpile catui page.json -o layout.catui
```

`decompile` is the full path — it extracts scripts as `.cat` files, the UI layout as `.catui`, and generates a `.catpilerc` for recompilation. `catui` is narrower — it only extracts the UI layout. Use `catui` when you already have your scripts and just want to inspect or edit the UI element tree.

### Programmatic Decompilation

This produces:
- `page.catui` — CatUI DSL
- One `.cat` file per script
- `.catpilerc` — ready-to-use project config

### Programmatic Decompilation

```python
from catpile.decompiler import decompile_ui_to_catui, decompile_page
import json

# From raw UI elements list
with open("page.json") as f:
    data = json.load(f)

elements = data.get("webcontent", data)

# Without page metadata:
catui = decompile_ui_to_catui(elements)

# With page metadata (round-trip):
catui = decompile_ui_to_catui(elements, metadata={
    "background": data.get("background"),
    "title": data.get("title"),
})

# Full page decompilation:
outputs = decompile_page(data, "page")
# outputs = {"main.cat": "...", "page.catui": "...", ".catpilerc": "..."}
```

## Footnotes

[^deprecated]: The `donation` element class (`TextButton?donation`) is deprecated in favor of `transfer` (`TextButton?transfer`) and `avataritem` (`TextButton?avataritem`). Use `transfer` for general donation/payment buttons and `avataritem` for avatar item purchase buttons. `donation` is still supported for backward compatibility but will be removed in a future release.
