"""Tests for Catpile parser, emitter, and full pipeline."""

import json
import sys
import re
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from catpile.parser import parse, ParseError
from catpile.emitter import Emitter, EmitError
from catpile.ir import (
    Program, ScriptDef, EventDef, FunctionDef, ActionStmt,
    InterpolatedStr, StrLit, VarRef,
)


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


def test_scope_global():
    source = """
on loaded:
    global score = 100
    """
    prog = parse(source)
    ev = prog.scripts[0].events[0]
    assert len(ev.body) == 1
    stmt = ev.body[0]
    assert stmt.name == "VAR_SET"
    # Arg 0 is the variable name (StrLit), arg 1 is the value (NumLit)
    assert stmt.args[0].value == "score"
    from catpile.ir import NumLit
    assert isinstance(stmt.args[1], NumLit)
    # Check it compiles without error
    from catpile.emitter import Emitter
    result = Emitter().emit(prog)
    assert result is not None


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
