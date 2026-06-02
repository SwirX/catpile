# Migrating from Old JSON-Format `.catui` Files

**Version 1.1.0** replaces the old JSON-based `.catui` format with a clean indentation-based DSL. The old format still works in `cpile build` but is **deprecated** and will be removed in a future release.

## What Changed

**Before (old JSON format):**

```json
{
    "ui": [
        {
            "class": "Frame",
            "globalid": "root",
            "alias": "root",
            "size": "{1,0},{1,0}",
            "children": [
                { "class": "TextLabel", "globalid": "title", "text": "Hello" }
            ]
        }
    ],
    "metadata": { "description": "My page" }
}
```

**After (new DSL format):**

```python
page "page":

    description = "My page"

    frame root [globalid: "root"]:
        size = "{1,0},{1,0}"
        textlabel title:
            text = "Hello"
```

## Migrate Automatically

Run the built-in migration command:

```bash
cpile migrate path/to/page.catui
```

This converts the file in-place. Use `-o <output>` to write to a different path:

```bash
cpile migrate path/to/page.catui -o path/to/page_converted.catui
```

## Manual Migration via Rebuild + Decompile

If your project uses a `.catpilerc` config file, rebuild the output JSON and decompile it back:

```bash
cpile build
cpile decompile build/page.json
```

This regenerates all sources (scripts + UI) in the current format.

## What About Scripts?

The old format handled scripts through the `"scripts"` key in the project config:

```json
{
    "name": "main",
    "ui": "ui/main.catui",
    "scripts": ["src/main.cat"],
    "output": "build/main.json"
}
```

The new format embeds script **references** directly in the `.catui` DSL and discovers script aliases from the file:

```json
{
    "name": "main",
    "catui": "ui/main.catui",
    "output": "build/main.json"
}
```

The scripts themselves (`.cat` files) do not change — only how they are declared.

## Timeline

| Version | Status |
|---------|--------|
| ≤ 1.0.0 | Old JSON format only |
| 1.1.0   | Both formats supported; old format emits deprecation warning |
| Future  | Old format removed entirely — only DSL accepted |
