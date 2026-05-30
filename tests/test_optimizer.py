"""Tests for the Catpile IR optimizer."""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from catpile.ir import (
    Program, ScriptDef, EventDef, FunctionDef,
    ActionStmt, IfStmt, RepeatStmt, ForEachStmt, BreakStmt, ReturnStmt,
    VarRef, StrLit, NumLit, InterpolatedStr,
)
from catpile.emitter import Emitter
from catpile.optimizer import (
    Optimizer,
    pass_unreachable_code,
    pass_empty_block_stripping,
    pass_function_inlining,
    pass_loop_unrolling,
    pass_dead_store_elimination,
    pass_string_peephole,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _make_prog(body: list) -> Program:
    return Program(scripts=[ScriptDef(events=[EventDef("LOADED", body=body)])])


def _actions(prog: Program) -> list:
    return prog.scripts[0].events[0].body


# ---------------------------------------------------------------------------
# Level 1 tests
# ---------------------------------------------------------------------------

def test_unreachable_code():
    """Statements after return should be removed."""
    prog = _make_prog([
        ActionStmt("LOG", [StrLit("hello")]),
        ReturnStmt(value=StrLit("0")),
        ActionStmt("LOG", [StrLit("never")]),  # unreachable
    ])
    removed = pass_unreachable_code(prog)
    assert removed == 1
    assert len(_actions(prog)) == 2
    assert isinstance(_actions(prog)[1], ReturnStmt)


def test_unreachable_break():
    """Statements after break in a loop body should be removed."""
    prog = _make_prog([
        RepeatStmt(times=3, body=[
            ActionStmt("LOG", [StrLit("a")]),
            BreakStmt(),
            ActionStmt("LOG", [StrLit("never")]),
        ]),
    ])
    removed = pass_unreachable_code(prog)
    assert removed == 1
    loop_body = _actions(prog)[0].body
    assert len(loop_body) == 2  # LOG + BREAK
    assert isinstance(loop_body[1], BreakStmt)


def test_empty_if_removed():
    """IfStmt with empty body should be removed entirely."""
    prog = _make_prog([
        IfStmt(condition="IF_EQ", args=[StrLit("a"), StrLit("b")],
               body=[], else_body=None),
        ActionStmt("LOG", [StrLit("keep")]),
    ])
    removed = pass_empty_block_stripping(prog)
    assert removed == 1
    assert len(_actions(prog)) == 1
    assert _actions(prog)[0].name == "LOG"


def test_empty_repeat_removed():
    """RepeatStmt with empty body should be removed."""
    prog = _make_prog([
        RepeatStmt(times=5, body=[]),
    ])
    removed = pass_empty_block_stripping(prog)
    assert removed == 1
    assert len(_actions(prog)) == 0


def test_empty_foreach_removed():
    """ForEachStmt with empty body should be removed."""
    prog = _make_prog([
        ForEachStmt(table="items", body=[]),
    ])
    removed = pass_empty_block_stripping(prog)
    assert removed == 1
    assert len(_actions(prog)) == 0


# ---------------------------------------------------------------------------
# Level 2 tests
# ---------------------------------------------------------------------------

def test_function_inlining():
    """FUNC_RUN calls should be replaced with inlined body."""
    prog = Program(scripts=[
        ScriptDef(
            alias="main",
            events=[
                EventDef("LOADED", body=[
                    ActionStmt("FUNC_RUN", [StrLit("helper")]),
                ]),
            ],
            functions=[
                FunctionDef(name="helper", params=[], body=[
                    ActionStmt("LOG", [StrLit("inlined")]),
                ]),
            ],
        ),
    ])
    inlined = pass_function_inlining(prog)
    assert inlined == 1
    body = prog.scripts[0].events[0].body
    assert len(body) == 1
    assert body[0].name == "LOG"


def test_function_inlining_with_params():
    """Function parameters should be replaced with call arguments."""
    prog = Program(scripts=[
        ScriptDef(
            alias="main",
            events=[
                EventDef("LOADED", body=[
                    ActionStmt("FUNC_RUN", [StrLit("add"),
                                            VarRef("x")]),
                ]),
            ],
            functions=[
                FunctionDef(name="add", params=["a"], body=[
                    ActionStmt("LOG", [VarRef("a")]),
                ]),
            ],
        ),
    ])
    inlined = pass_function_inlining(prog)
    assert inlined == 1
    body = prog.scripts[0].events[0].body
    assert len(body) == 1
    # Parameter 'a' should be replaced with VarRef 'x'
    assert body[0].args[0].name == "x"


def test_function_inlining_single_call_always_inlined():
    """Functions called once are inlined even if large (single-call heuristic)."""
    prog = Program(scripts=[
        ScriptDef(
            alias="main",
            events=[
                EventDef("LOADED", body=[
                    ActionStmt("FUNC_RUN", [StrLit("big")]),
                ]),
            ],
            functions=[
                FunctionDef(name="big", params=[], body=[
                    ActionStmt("LOG", [StrLit("1")]),
                    ActionStmt("LOG", [StrLit("2")]),
                    ActionStmt("LOG", [StrLit("3")]),
                    ActionStmt("LOG", [StrLit("4")]),
                    ActionStmt("LOG", [StrLit("5")]),
                    ActionStmt("LOG", [StrLit("6")]),
                ]),
            ],
        ),
    ])
    inlined = pass_function_inlining(prog, max_body_size=5)
    assert inlined == 1  # Single call site → always inlines
    body = prog.scripts[0].events[0].body
    assert len(body) == 6  # All 6 statements inlined


def test_function_inlining_multi_call_large_skipped():
    """Large functions called multiple times should NOT be inlined."""
    prog = Program(scripts=[
        ScriptDef(
            alias="main",
            events=[
                EventDef("LOADED", body=[
                    ActionStmt("FUNC_RUN", [StrLit("big")]),
                    ActionStmt("FUNC_RUN", [StrLit("big")]),
                ]),
            ],
            functions=[
                FunctionDef(name="big", params=[], body=[
                    ActionStmt("LOG", [StrLit("1")]),
                    ActionStmt("LOG", [StrLit("2")]),
                    ActionStmt("LOG", [StrLit("3")]),
                    ActionStmt("LOG", [StrLit("4")]),
                    ActionStmt("LOG", [StrLit("5")]),
                    ActionStmt("LOG", [StrLit("6")]),
                ]),
            ],
        ),
    ])
    inlined = pass_function_inlining(prog, max_body_size=5)
    assert inlined == 0  # Multiple calls, large body
    body = prog.scripts[0].events[0].body
    for s in body:
        assert s.name == "FUNC_RUN"


# ---------------------------------------------------------------------------
# Level 3 tests
# ---------------------------------------------------------------------------

def test_loop_unrolling():
    """Fixed-count loops with no break should be unrolled."""
    prog = _make_prog([
        RepeatStmt(times=3, body=[
            ActionStmt("LOG", [StrLit("x")]),
        ]),
    ])
    unrolled = pass_loop_unrolling(prog)
    assert unrolled == 1
    body = _actions(prog)
    assert len(body) == 3  # LOG duplicated 3 times
    for s in body:
        assert s.name == "LOG"


def test_loop_unrolling_with_break_skipped():
    """Loops containing break should NOT be unrolled."""
    prog = _make_prog([
        RepeatStmt(times=3, body=[
            ActionStmt("LOG", [StrLit("x")]),
            BreakStmt(),
        ]),
    ])
    unrolled = pass_loop_unrolling(prog)
    assert unrolled == 0
    assert len(_actions(prog)) == 1
    assert _actions(prog)[0].times == 3


def test_dead_store_elimination():
    """VAR_SET for a variable that is never read should be removed."""
    prog = _make_prog([
        ActionStmt("VAR_SET", [StrLit("unused"), StrLit("value")]),
        ActionStmt("LOG", [StrLit("keep")]),
    ])
    eliminated = pass_dead_store_elimination(prog)
    assert eliminated == 1
    assert len(_actions(prog)) == 1


def test_dead_store_keeps_read_variables():
    """VAR_SET for a variable that IS read should be kept."""
    prog = _make_prog([
        ActionStmt("VAR_SET", [StrLit("used"), StrLit("hello")]),
        ActionStmt("LOG", [VarRef("used")]),
    ])
    eliminated = pass_dead_store_elimination(prog)
    assert eliminated == 0
    assert len(_actions(prog)) == 2


def test_string_peephole_merges_adjacent():
    """Adjacent StrLit parts in InterpolatedStr should be merged."""
    prog = _make_prog([
        ActionStmt("LOG", [
            InterpolatedStr([StrLit("Hel"), StrLit("lo "), VarRef("name"),
                             StrLit("!"), StrLit("!")]),
        ]),
    ])
    merged = pass_string_peephole(prog)
    assert merged > 0
    i = _actions(prog)[0].args[0]
    assert isinstance(i, InterpolatedStr)
    assert len(i.parts) == 3  # "Hello ", name, "!!"



# ---------------------------------------------------------------------------
# Full Optimizer test
# ---------------------------------------------------------------------------

def test_optimizer_levels():
    """All optimization levels should run without error."""
    prog = _make_prog([
        ReturnStmt(value=StrLit("0")),
        ActionStmt("LOG", [StrLit("unreachable")]),  # L1 removes this
    ])
    for level in [1, 2, 3]:
        opt = Optimizer(prog, level=level)
        result = opt.run()
        assert isinstance(result, Program)
        assert opt.report()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [name for name in dir() if name.startswith("test_")]
    passed = 0
    failed = 0
    for name in sorted(tests):
        try:
            globals()[name]()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{passed}/{passed + failed} passed")
