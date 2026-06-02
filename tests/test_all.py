"""Tests for Catpile parser, emitter, and full pipeline."""

import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from catpile.parser import parse, ParseError
from catpile.emitter import Emitter, EmitError
from catpile.ir import (
    Program, ScriptDef, EventDef, FunctionDef, ActionStmt,
    InterpolatedStr, StrLit, VarRef,
)
from catpile.catui_ir import CatUIProgram, PageDef, UIElement, UIStylingElement, ScriptPlaceholder
from catpile.catui_parser import parse_catui, CatUIError
from catpile.catui_emitter import emit_catui
from catpile.decompiler import decompile_ui_to_catui


def test_parse_simple():
    source = """
on loaded:
    log("hello")
    """
    prog = parse(source)
    assert len(prog.scripts) == 1
    assert len(prog.scripts[0].events) == 1
    assert prog.scripts[0].events[0].type == "LOADED"


def test_parse_with_params():
    source = """
on pressed("myBtn"):
    log("click")
    """
    prog = parse(source)
    ev = prog.scripts[0].events[0]
    assert ev.type == "PRESSED"
    assert ev.params == ["myBtn"]


def test_parse_function():
    source = """
fn doThing():
    log("doing")
    """
    prog = parse(source)
    fn = prog.scripts[0].functions[0]
    assert fn.name == "doThing"


def test_parse_if_else():
    source = """
on loaded:
    if eq("a", "b"):
        log("equal")
    else:
        log("not equal")
    """
    prog = parse(source)
    ev = prog.scripts[0].events[0]
    assert len(ev.body) == 1
    if_stmt = ev.body[0]
    from catpile.ir import IfStmt
    assert isinstance(if_stmt, IfStmt)
    assert if_stmt.condition == "IF_EQ"
    assert if_stmt.else_body is not None


def test_parse_repeat():
    source = """
fn setup():
    repeat(10):
        log("x")
    """
    prog = parse(source)
    fn = prog.scripts[0].functions[0]
    from catpile.ir import RepeatStmt
    assert isinstance(fn.body[0], RepeatStmt)
    assert fn.body[0].times == "10"


def test_parse_assignment():
    source = """
on loaded:
    msg = "hello"
    """
    prog = parse(source)
    ev = prog.scripts[0].events[0]
    assert len(ev.body) == 1
    assert ev.body[0].name == "VAR_SET"


def test_emit_simple():
    source = """
on loaded:
    log("test")
    """
    prog = parse(source)
    emitter = Emitter()
    result = json.loads(emitter.emit(prog))
    assert isinstance(result, list)
    assert result[0]["class"] == "script"
    assert len(result[0]["content"]) == 1
    ev = result[0]["content"][0]
    assert ev["id"] == "0"  # LOADED
    assert len(ev["actions"]) == 1
    assert ev["actions"][0]["id"] == "0"  # LOG


def test_emit_if_else():
    source = """
on loaded:
    if eq("a", "b"):
        log("yes")
    else:
        log("no")
    """
    prog = parse(source)
    emitter = Emitter()
    result = json.loads(emitter.emit(prog))
    actions = result[0]["content"][0]["actions"]
    assert actions[0]["id"] == "18"    # IF_EQ
    assert actions[1]["id"] == "0"     # LOG (body)
    assert actions[2]["id"] == "112"   # ELSE
    assert actions[3]["id"] == "0"     # LOG (else body)
    assert actions[4]["id"] == "25"    # END


def test_emit_repeat():
    source = """
fn doit():
    repeat(5):
        log("x")
    """
    prog = parse(source)
    emitter = Emitter()
    result = json.loads(emitter.emit(prog))
    actions = result[0]["content"][0]["actions"]
    # Function def → actions start with REPEAT
    assert any(a["id"] == "22" for a in actions)  # REPEAT
    assert any(a["id"] == "25" for a in actions)  # END


def test_emit_var_set():
    source = """
on loaded:
    msg = "hello"
    """
    prog = parse(source)
    emitter = Emitter()
    result = json.loads(emitter.emit(prog))
    actions = result[0]["content"][0]["actions"]
    assert actions[0]["id"] == "11"  # VAR_SET


def test_multi_event_chunking():
    """More than ACTIONS_PER_EVENT actions → multiple event blocks."""
    source = "on loaded:\n"
    for i in range(125):  # 125 > 120 = need 2 blocks
        source += f"    log(\"msg{i}\")\n"

    prog = parse(source)
    emitter = Emitter()
    result = json.loads(emitter.emit(prog))
    blocks = result[0]["content"]
    assert len(blocks) >= 2, f"Expected ≥2 blocks, got {len(blocks)}"
    # Combined action count
    total = sum(len(b["actions"]) for b in blocks)
    assert total == 125


def test_unknown_action():
    """Unknown action should cause an error."""
    source = """
on loaded:
    nonexistent_action("arg")
    """
    try:
        prog = parse(source)
        emitter = Emitter()
        emitter.emit(prog)
        assert False, "Should have raised an error"
    except Exception:
        pass  # Expected


def test_inconsistent_indent():
    source = """
on loaded:
    log("a")
      log("b")
    """
    try:
        parse(source)
        assert False, "Should have raised SyntaxError"
    except (SyntaxError, ParseError):
        pass  # Expected


def test_empty_file():
    source = ""
    prog = parse(source)
    assert len(prog.scripts) == 0


def test_multi_script():
    source = """
script "movement":
    on loaded:
        log("init")

script "utils":
    fn doThing():
        log("working")
"""
    prog = parse(source)
    assert len(prog.scripts) == 2
    assert prog.scripts[0].alias == "movement"
    assert prog.scripts[1].alias == "utils"
    emitter = Emitter()
    result = json.loads(emitter.emit(prog))
    assert len(result) == 2
    assert result[0]["alias"] == "movement"
    assert result[1]["alias"] == "utils"


def test_string_interpolation():
    source = 'on loaded:\n    log("Hello {name}!")\n'
    prog = parse(source)
    ev = prog.scripts[0].events[0]
    arg = ev.body[0].args[0]
    assert isinstance(arg, InterpolatedStr)
    assert len(arg.parts) == 3  # "Hello ", name, "!"
    assert isinstance(arg.parts[1], VarRef)
    assert arg.parts[1].name == "name"
    # Emit should produce STR_CONCAT actions
    emitter = Emitter()
    result = json.loads(emitter.emit(prog))
    actions = result[0]["content"][0]["actions"]
    assert any(a["id"] == "109" for a in actions)  # STR_CONCAT
    assert actions[-1]["id"] == "0"  # LOG (last, after concat chain)


def test_string_no_interpolation():
    source = 'on loaded:\n    log("plain string")\n'
    prog = parse(source)
    arg = prog.scripts[0].events[0].body[0].args[0]
    assert isinstance(arg, StrLit)
    assert arg.value == "plain string"


def test_string_single_var():
    source = 'on loaded:\n    log("{name}")\n'
    prog = parse(source)
    arg = prog.scripts[0].events[0].body[0].args[0]
    assert isinstance(arg, InterpolatedStr)
    assert len(arg.parts) == 1
    assert isinstance(arg.parts[0], VarRef)


def test_scope_local():
    source = """
on loaded:
    local msg = "hello"
    """
    prog = parse(source)
    ev = prog.scripts[0].events[0]
    assert len(ev.body) == 1
    assert ev.body[0].name == "VAR_SET"


def test_scope_obj():
    source = """
on loaded:
    obj btn = myButton
    """
    prog = parse(source)
    ev = prog.scripts[0].events[0]
    assert len(ev.body) == 1
    assert ev.body[0].name == "VAR_SET"


# ---------------------------------------------------------------------------
# CatUI Tests
# ---------------------------------------------------------------------------

CATUI_SIMPLE = '''
page "main":
    frame root:
        size = "{1,0},{1,0}"
        bg = "#1a1a2e"
        textlabel title:
            text = "Welcome"
            font = "GothamBold"
        textbutton submit [globalid: "btn123"]:
            text = "Click Me"
            uicorner round:
                radius = "0,8"
        script sidebar:
            source = "src/sidebar.cat"
'''


def test_catui_parse_simple():
    prog = parse_catui(CATUI_SIMPLE)
    assert len(prog.pages) == 1
    page = prog.pages[0]
    assert page.name == "main"
    assert page.element.children[0].class_name == "frame"
    assert page.element.children[0].alias == "root"
    assert page.element.children[0].properties["size"] == "{1,0},{1,0}"
    assert page.element.children[0].properties["bg"] == "#1a1a2e"
    children = page.element.children[0].children
    assert len(children) == 3

    title = children[0]
    assert isinstance(title, UIElement)
    assert title.class_name == "textlabel"
    assert title.alias == "title"

    submit = children[1]
    assert isinstance(submit, UIElement)
    assert submit.class_name == "textbutton"
    assert submit.globalid == "btn123"
    assert len(submit.children) == 1
    corner = submit.children[0]
    assert isinstance(corner, UIStylingElement)
    assert corner.class_name == "uicorner"
    assert corner.properties["radius"] == "0,8"

    script = children[2]
    assert isinstance(script, ScriptPlaceholder)
    assert script.alias == "sidebar"
    assert script.source == "src/sidebar.cat"


def test_catui_parse_no_page():
    """Raw elements without page keyword should still parse."""
    source = '''
frame root:
    size = "{1,0},{1,0}"
    textlabel title:
        text = "Hi"
'''
    prog = parse_catui(source)
    assert len(prog.pages) == 1


def test_catui_parse_empty():
    prog = parse_catui("")
    assert len(prog.pages) == 0


def test_catui_parse_styling():
    source = '''
frame root:
    uicorner c1:
        radius = "0,16"
    uistroke s1:
        stroke_color = "#ffffff"
    uigradient g1:
        rotation = "90"
    uipadding p1:
        padding_top = "0,10"
    uilistlayout l1:
        direction = "Vertical"
    uigridlayout gl1:
        size = "{0.3,0},{0.3,0}"
    uiaspectratioconstraint a1:
        ratio = "1.77"
    uisizeconstraint sc1:
        min_size = "100,100"
    uitextsizeconstraint tc1:
        min_text_size = "12"
'''
    prog = parse_catui(source)
    root = prog.pages[0].element.children[0]
    assert len(root.children) == 9
    for child in root.children:
        assert isinstance(child, UIStylingElement), f"{child.alias} is not UIStylingElement"


def test_catui_emit():
    from catpile.catui_emitter import emit_catui
    import json
    prog = parse_catui(CATUI_SIMPLE)
    result = json.loads(emit_catui(prog))
    assert isinstance(result, dict)
    assert set(result.keys()) == {"description", "title", "background", "webcontent"}
    root = result["webcontent"][0]
    assert root["class"] == "Frame"
    assert root["background_color"] == "#1a1a2e"  # alias resolution
    assert root["size"] == "{1,0},{1,0}"
    assert root["globalid"] is not None

    children = root.get("children", [])
    assert len(children) == 3

    title = children[0]
    assert title["class"] == "TextLabel"
    assert title["text"] == "Welcome"

    submit = children[1]
    assert submit["class"] == "TextButton"
    assert submit["globalid"] == "btn123"  # preserved explicit gid

    corner = submit.get("children", [None])[0]
    assert corner["class"] == "UICorner"
    assert corner["radius"] == "0,8"

    script = children[2]
    assert script["class"] == "script"
    assert script["alias"] == "sidebar"
    assert "globalid" not in script


def test_catui_decompile_to_dsl():
    elements = [
        {
            "class": "Frame",
            "globalid": "root_gid",
            "alias": "root",
            "size": "{1,0},{1,0}",
            "background_color": "#1a1a2e",
            "children": [
                {"class": "TextLabel", "globalid": "t_gid", "alias": "title",
                 "text": "Welcome", "font": "GothamBold"},
                {"class": "UICorner", "globalid": "c_gid", "radius": "0,8"},
                {"class": "script", "alias": "my_script"},
            ]
        }
    ]
    catui = decompile_ui_to_catui(elements)
    prog = parse_catui(catui)
    assert len(prog.pages) == 1
    root = prog.pages[0].element.children[0]
    assert root.class_name == "frame"
    assert root.alias == "root"
    children = root.children
    assert len(children) == 3
    assert isinstance(children[0], UIElement)
    assert isinstance(children[1], UIStylingElement)
    assert isinstance(children[2], ScriptPlaceholder)


def test_catui_roundtrip():
    """Full round-trip: CatUI DSL → emit → decompile → parse again."""
    import json
    prog1 = parse_catui(CATUI_SIMPLE)
    ui_json = json.loads(emit_catui(prog1))
    # ui_json is now a dict with webcontent
    elements = ui_json.get("webcontent", ui_json) if isinstance(ui_json, dict) else ui_json
    catui2 = decompile_ui_to_catui(elements)
    prog2 = parse_catui(catui2)

    assert len(prog2.pages) == 1
    page2 = prog2.pages[0]
    assert page2.element.children[0].class_name == "frame"
    assert page2.element.children[0].properties.get("bg") == "#1a1a2e"


def test_catui_builder_new_format():
    """Test the builder with new-format CatUI DSL."""
    import json, tempfile
    from pathlib import Path
    from catpile.builder import build_page

    catui_src = '''
page "test":
    frame root:
        size = "{1,0},{1,0}"
        textlabel title:
            text = "Hello"
        script main_script:
            source = "src/main.cat"
'''
    script_src = '''
script "main_script":
    on loaded:
        log("test")
'''
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "src").mkdir()
        (tmp / "src" / "main.cat").write_text(script_src)
        (tmp / "ui").mkdir()
        (tmp / "ui" / "test.catui").write_text(catui_src)

        page_cfg = {
            "name": "test",
            "catui": "ui/test.catui",
            "output": "build/test.json",
        }
        result = build_page(page_cfg, tmp, "indent", 0, True)
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "webcontent" in data
        root = data["webcontent"][0]
        assert root["class"] == "Frame"
        children = root.get("children", [])
        scripts = [c for c in children if c.get("class") == "script"]
        assert len(scripts) == 1
        assert "content" in scripts[0]


def test_catui_builder_old_format():
    """Test the builder with old-format .catui JSON for backward compat."""
    import json, tempfile
    from pathlib import Path
    from catpile.builder import build_page

    catui_json = {
        "ui": [
            {
                "class": "Frame",
                "globalid": "root_f",
                "alias": "root",
                "size": "{1,0},{1,0}",
                "children": [
                    {"class": "TextLabel", "globalid": "lbl", "alias": "label",
                     "text": "Hi"},
                    {"class": "script", "alias": "old_script"},
                ]
            }
        ]
    }
    script_src = '''
script "old_script":
    on loaded:
        log("old")
'''
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "src").mkdir()
        (tmp / "src" / "old.cat").write_text(script_src)
        (tmp / "ui").mkdir()
        (tmp / "ui" / "old.catui").write_text(json.dumps(catui_json))

        page_cfg = {
            "name": "old",
            "ui": "ui/old.catui",
            "scripts": ["src/old.cat"],
            "output": "build/old.json",
        }
        result = build_page(page_cfg, tmp, "indent", 0, True)
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "webcontent" in data
        children = data["webcontent"][0].get("children", [])
        scripts = [c for c in children if c.get("class") == "script"]
        assert len(scripts) == 1
        assert "content" in scripts[0]


def test_catui_uilinker_with_index():
    """Test UILinker works with a pre-built index dict."""
    from catpile.ui import UILinker
    from catpile.ir import Program, ScriptDef, EventDef, ActionStmt, ObjectRef, StrLit

    index = {"myButton": "btn_gid"}
    linker = UILinker(index)

    prog = Program()
    script = ScriptDef(alias="test")
    script.events.append(EventDef(type="LOADED", params=[], body=[
        ActionStmt(name="LOOK_HIDE", args=[ObjectRef("myButton")]),
    ]))
    prog.scripts.append(script)

    resolved = linker.link(prog)
    assert resolved == 1
    assert isinstance(prog.scripts[0].events[0].body[0].args[0], StrLit)
    assert prog.scripts[0].events[0].body[0].args[0].value == "btn_gid"


if __name__ == "__main__":
    tests = [
        name for name in dir() if name.startswith("test_")
    ]
    for name in sorted(tests):
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            import traceback
            traceback.print_exc()
