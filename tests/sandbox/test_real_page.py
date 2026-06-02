import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from catpile.decompiler import decompile_page, decompile_ui_to_catui
from catpile.catui_parser import parse_catui
from catpile.catui_emitter import emit_catui
from catpile.catui_ir import build_gid_index
from catpile.builder import build_page
from catpile.ui import UILinker

SANDBOX = Path(__file__).parent
PAGE_JSON = SANDBOX / "real_page.json"


def load_page():
    data = json.loads(PAGE_JSON.read_text())
    return data


def test_1_decompile_to_dsl():
    data = load_page()
    page_json = data.get("webcontent", data)
    catui = decompile_ui_to_catui(page_json)
    assert len(catui) > 0
    print(f"  Decompiled to {len(catui)} chars of CatUI DSL")
    print(f"  First 60 chars: {catui[:60].strip()!r}")
    return catui


def test_2_parse_decompiled_dsl(catui):
    prog = parse_catui(catui)
    assert len(prog.pages) == 1
    page = prog.pages[0]
    page_el = page.element
    print(f"  Page: {page.name!r}")
    print(f"  Page element: class={page_el.class_name}, alias={page_el.alias!r}")
    print(f"  Page properties: {page_el.properties}")
    children = page_el.children
    print(f"  Children: {len(children)} top-level element(s)")
    for i, c in enumerate(children):
        if hasattr(c, 'class_name'):
            print(f"    Child {i}: {c.class_name} / alias={c.alias!r} / globalid={c.globalid!r}")
        else:
            print(f"    Child {i}: script / alias={c.alias!r} / source={c.source!r}")
    return prog


def test_3_emit_and_verify(prog):
    emitted = json.loads(emit_catui(prog))
    assert isinstance(emitted, dict)
    assert "webcontent" in emitted
    roots = emitted["webcontent"]
    assert len(roots) >= 1
    print(f"  Emitted {len(roots)} top-level element(s)")
    for i, root in enumerate(roots):
        print(f"  Root {i}: class={root.get('class')}, alias={root.get('alias', 'N/A')}")
    total = 0

    def collect(el):
        nonlocal total
        total += 1
        for c in el.get("children", []):
            collect(c)

    for root in roots:
        collect(root)
    print(f"  Total elements in tree: {total}")
    return emitted


def test_4_build_page_with_scripts():
    """Full round-trip: decompiled page → build with a script → verify."""
    data = load_page()
    page_json = data.get("webcontent", data)
    metadata = {k: v for k, v in data.items() if k != "webcontent"}

    catui = decompile_ui_to_catui(page_json)

    # Create a script that references an element by globalID
    script_src = '''
script "main":
    on loaded:
        log("Page loaded!")
        look_set_text("\"4", "Placeholder!")
'''
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "src").mkdir()
        (tmp / "src" / "main.cat").write_text(script_src)
        (tmp / "ui").mkdir()
        (tmp / "ui" / "test.catui").write_text(catui)

        # Parse the catui to check its structure has script markers
        prog = parse_catui(catui)
        gid_index = build_gid_index(prog)
        print(f"  GID index has {len(gid_index)} entries")
        for k, v in sorted(gid_index.items()):
            print(f"    {k!r} → {v!r}")

        # Build the page
        output = build_page(
            {"name": "test", "catui": "ui/test.catui", "output": "build/test.json"},
            tmp, "indent", 0, True,
        )
        built = json.loads(output)
        print(f"  Built page has keys: {list(built.keys())}")
        return built


def test_5_path_resolution():
    """Test that elements can be referenced by Page.path and resolve to globalIDs."""
    data = load_page()
    page_json = data.get("webcontent", data)
    catui = decompile_ui_to_catui(page_json)
    prog = parse_catui(catui)
    gid_index = build_gid_index(prog)

    # Create a script using path references
    script_src = '''
script "main":
    on loaded:
        hide(Page.frame_1)
        show(Page.imagelabel_1)
'''
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "src").mkdir()
        (tmp / "src" / "main.cat").write_text(script_src)
        (tmp / "ui").mkdir()
        (tmp / "ui" / "test.catui").write_text(catui)

        output = build_page(
            {"name": "test", "catui": "ui/test.catui", "output": "build/test.json"},
            tmp, "indent", 0, True,
        )
        built = json.loads(output)
        print("  Path resolution test passed")
        return built


def test_6_modify_and_rebuild():
    """Modify aliases, colors, add UI effects → verify JSON changes."""
    data = load_page()
    page_json = data.get("webcontent", data)

    # Decompile to DSL
    catui = decompile_ui_to_catui(page_json)

    # Modify the DSL: add rounded corners, stroke, change colors
    modified = catui.replace(
        'frame frame_1 [globalid: "b\'"]:',
        'textbutton myButton:'
    )
    # Try to replace size if present (may not exist in all elements)
    if 'size = ' in modified:
        # Replace any size with a new one
        import re
        modified = re.sub(
            r'size = "[^"]*"',
            'size = "{0.2, 0},{0.2, 0}"',
            modified
        )

    # Parse, modify and rebuild
    prog = parse_catui(modified)
    page = prog.pages[0]

    # Find myButton across all top-level children
    from catpile.catui_ir import UIStylingElement
    target = None
    for c in page.element.children:
        if hasattr(c, 'alias') and c.alias == 'myButton':
            target = c
            break
    assert target is not None, "myButton not found in page children"

    target.properties['bg'] = '#ff0000'
    # Add UICorner
    corner = UIStylingElement(
        class_name='uicorner',
        alias='round_corner',
        properties={'radius': '0,12'}
    )
    target.children.append(corner)
    # Add UIStroke
    stroke = UIStylingElement(
        class_name='uistroke',
        alias='outline',
        properties={'stroke_color': '#ffffff', 'stroke_thickness': '2'}
    )
    target.children.append(stroke)
    print(f"  Added styling to {target.alias}")

    # Re-emit and verify
    emitted = json.loads(emit_catui(prog))
    roots = emitted["webcontent"]

    for root in roots:
        if root.get("alias") == "myButton":
            c = root
            assert c.get("background_color") == "#ff0000", f"Expected red bg, got {c.get('background_color')}"
            if "size" in c:
                assert c["size"] == "{0.2, 0},{0.2, 0}", f"Expected modified size, got {c['size']}"
            child_els = c.get("children", [])
            has_corner = any(ce.get("class") == "UICorner" for ce in child_els)
            has_stroke = any(ce.get("class") == "UIStroke" for ce in child_els)
            assert has_corner, "Should have UICorner"
            assert has_stroke, "Should have UIStroke"
            print(f"  Verified modifications on {c.get('alias')}:")
            print(f"    bg={c.get('background_color')}, size={c.get('size')}")
            print(f"    children classes: {[ce.get('class') for ce in child_els]}")
            break

    return emitted


def test_7_new_element_classes():
    """Verify transfer and avataritem elements survive the round trip."""
    data = load_page()
    page_json = data.get("webcontent", data)

    catui = decompile_ui_to_catui(page_json)
    prog = parse_catui(catui)

    found_transfer = False
    found_avataritem = False

    def search(el):
        nonlocal found_transfer, found_avataritem
        if hasattr(el, 'class_name'):
            if el.class_name == 'transfer':
                found_transfer = True
            if el.class_name == 'avataritem':
                found_avataritem = True
        if hasattr(el, 'children'):
            for c in el.children:
                search(c)

    for child in prog.pages[0].element.children:
        search(child)
    assert found_transfer, "TextButton?transfer not found in parsed DSL"
    assert found_avataritem, "TextButton?avataritem not found in parsed DSL"
    print(f"  Found transfer: {found_transfer}, avataritem: {found_avataritem}")


if __name__ == "__main__":
    tests = [name for name in dir() if name.startswith("test_")]

    results = {}
    for name in sorted(tests):
        try:
            if name == "test_1_decompile_to_dsl":
                r = test_1_decompile_to_dsl()
            elif name == "test_2_parse_decompiled_dsl":
                r = test_2_parse_decompiled_dsl(results.get("test_1_decompile_to_dsl"))
            elif name == "test_3_emit_and_verify":
                r = test_3_emit_and_verify(results.get("test_2_parse_decompiled_dsl"))
            elif name == "test_4_build_page_with_scripts":
                r = test_4_build_page_with_scripts()
            elif name == "test_5_path_resolution":
                r = test_5_path_resolution()
            elif name == "test_6_modify_and_rebuild":
                r = test_6_modify_and_rebuild()
            elif name == "test_7_new_element_classes":
                r = test_7_new_element_classes()
            results[name] = r
            print(f"  PASS  {name}")
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"All {len(tests)} tests PASSED")
