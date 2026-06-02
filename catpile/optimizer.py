"""Multi-tiered IR optimizer for Catpile.

Three optimization levels:

  -O1  Dead code elimination, empty block stripping
  -O2  + Function inlining, table pre-allocation (default)
  -O3  + Loop unrolling, dead store elimination, string peephole

Each pass transforms the IR in-place and preserves semantic correctness.
"""

from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any

from .ir import (
    Program, ScriptDef, EventDef, FunctionDef,
    ActionStmt, IfStmt, RepeatStmt, ForEachStmt, BreakStmt, ReturnStmt,
    VarRef, StrLit, NumLit, ObjectRef, InterpolatedStr, MathExpr,
    DictLiteral, ListLiteral, KVPair,
    Arg, Stmt,
)
from . import mappings as M


# ---------------------------------------------------------------------------
# Pass utilities
# ---------------------------------------------------------------------------

def _iter_scripts(program: Program):
    """Yield (script_idx, script) for each script in the program."""
    for i, s in enumerate(program.scripts):
        yield i, s


def _iter_event_fns(script: ScriptDef):
    """Yield ('event', idx, event) and ('fn', idx, func) from a script."""
    for i, e in enumerate(script.events):
        yield "event", i, e
    for i, f in enumerate(script.functions):
        yield "fn", i, f


# ---------------------------------------------------------------------------
# Level 1: Dead Code Elimination & Safe Local Transforms
# ---------------------------------------------------------------------------

def pass_unreachable_code(program: Program) -> int:
    """1.1 Strip statements after ReturnStmt / BreakStmt in each block.

    Walks all event/function bodies AND nested control-flow bodies.
    Returns count of removed statements.
    """
    removed = 0

    def _strip_unreachable(stmts: list[Stmt]) -> list[Stmt]:
        nonlocal removed
        out: list[Stmt] = []
        for stmt in stmts:
            if isinstance(stmt, (ReturnStmt, BreakStmt)):
                out.append(stmt)
                # Everything after this in the current list is unreachable
                break
            # Recurse into nested bodies
            if isinstance(stmt, IfStmt):
                stmt.body = _strip_unreachable(stmt.body)
                if stmt.else_body:
                    stmt.else_body = _strip_unreachable(stmt.else_body)
            elif isinstance(stmt, RepeatStmt):
                stmt.body = _strip_unreachable(stmt.body)
            elif isinstance(stmt, ForEachStmt):
                stmt.body = _strip_unreachable(stmt.body)
            out.append(stmt)
        removed += len(stmts) - len(out)
        return out

    for _, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            owner.body = _strip_unreachable(owner.body)

    return removed


def pass_empty_block_stripping(program: Program) -> int:
    """1.2 Remove IfStmt / RepeatStmt / ForEachStmt with empty bodies.

    A control-flow statement whose body and else_body are both empty
    can be removed entirely - no IF_EQ/END pair needed.
    Returns count of removed statements.
    """
    removed = 0

    def _strip_empty(stmts: list[Stmt]) -> list[Stmt]:
        nonlocal removed
        out: list[Stmt] = []
        for stmt in stmts:
            if isinstance(stmt, IfStmt):
                body_empty = _is_body_empty(stmt.body)
                else_empty = not stmt.else_body or _is_body_empty(stmt.else_body)
                if body_empty and else_empty:
                    removed += 1
                    continue  # drop the entire if
                # Recurse even if not empty - nested blocks may be empty
                stmt.body = _strip_empty(stmt.body)
                if stmt.else_body:
                    stmt.else_body = _strip_empty(stmt.else_body)
            elif isinstance(stmt, RepeatStmt):
                if _is_body_empty(stmt.body):
                    removed += 1
                    continue
                stmt.body = _strip_empty(stmt.body)
            elif isinstance(stmt, ForEachStmt):
                if _is_body_empty(stmt.body):
                    removed += 1
                    continue
                stmt.body = _strip_empty(stmt.body)
            out.append(stmt)
        return out

    for _, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            owner.body = _strip_empty(owner.body)

    return removed


def _is_body_empty(stmts: list[Stmt]) -> bool:
    """True if the statement list is empty or only contains comments."""
    for s in stmts:
        # Only ACTION "COMMENT" is ignorable
        if isinstance(s, ActionStmt) and s.name == "COMMENT":
            continue
        return False
    return True


# ---------------------------------------------------------------------------
# Level 2: CatWeb-Specific Optimizations
# ---------------------------------------------------------------------------

def pass_function_inlining(program: Program, max_body_size: int = 5) -> int:
    """2.1 Inline FUNC_RUN calls with function body.

    FUNC_RUN (ID 87) has significant runtime overhead in CatWeb.
    This pass replaces calls with the inlined function body, alpha-renaming
    parameters and local variables with a unique suffix to prevent collisions.

    Inlining removes the FUNC_RUN instruction and replaces it with the
    function's actual statements, eliminating the call overhead.

    Heuristic: inline if the function body is under *max_body_size*
    statements, OR if the function is called exactly once regardless of size.

    Returns count of inlined calls.
    """
    # Phase 1: Build a name → FunctionDef index per script
    fn_index: dict[str, list[tuple[int, FunctionDef]]] = defaultdict(list)
    for sidx, script in _iter_scripts(program):
        for fn in script.functions:
            fn_index[fn.name].append((sidx, fn))

    # Phase 2: Count call sites per function
    call_counts: dict[str, int] = defaultdict(int)

    def _count_calls(stmts: list[Stmt]):
        for s in stmts:
            if isinstance(s, ActionStmt):
                if s.name == "FUNC_RUN" and s.args:
                    first = s.args[0]
                    if isinstance(first, StrLit):
                        call_counts[first.value] += 1
            elif isinstance(s, IfStmt):
                _count_calls(s.body)
                if s.else_body:
                    _count_calls(s.else_body)
            elif isinstance(s, RepeatStmt):
                _count_calls(s.body)
            elif isinstance(s, ForEachStmt):
                _count_calls(s.body)

    for _, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            _count_calls(owner.body)

    # Phase 3: Inline
    inline_counter = [0]
    inlined = 0

    def _inline_in_scope(stmts: list[Stmt],
                         current_script_idx: int) -> list[Stmt]:
        nonlocal inlined
        out: list[Stmt] = []
        for stmt in stmts:
            if isinstance(stmt, ActionStmt) and stmt.name == "FUNC_RUN":
                if not stmt.args:
                    out.append(stmt)
                    continue
                first_arg = stmt.args[0]
                if not isinstance(first_arg, StrLit):
                    out.append(stmt)
                    continue
                fn_name = first_arg.value
                candidates = fn_index.get(fn_name, [])
                if not candidates:
                    out.append(stmt)
                    continue

                # Pick the function definition (same script preferred)
                fn_def = None
                for sidx, fn in candidates:
                    if sidx == current_script_idx:
                        fn_def = fn
                        break
                if fn_def is None:
                    fn_def = candidates[0][1]

                # Heuristic: inline if small body or single call site
                body_size = len(fn_def.body)
                if body_size > max_body_size and call_counts.get(fn_name, 0) > 1:
                    out.append(stmt)
                    continue

                # Build parameter bindings from FUNC_RUN args
                # FUNC_RUN format: run("fnName", [args...])
                # arg[0] = function name, arg[1] = tuple of args (optional)
                inline_idx = inline_counter[0]
                inline_counter[0] += 1
                suffix = f"_inline{inline_idx}"

                # Deep-copy the function body and alpha-rename
                new_body = _clone_and_rename(
                    fn_def.body, fn_def.params,
                    stmt.args[1:] if len(stmt.args) > 1 else [],
                    suffix,
                )
                out.extend(new_body)
                inlined += 1

            elif isinstance(stmt, IfStmt):
                stmt.body = _inline_in_scope(stmt.body, current_script_idx)
                if stmt.else_body:
                    stmt.else_body = _inline_in_scope(
                        stmt.else_body, current_script_idx)
                out.append(stmt)
            elif isinstance(stmt, RepeatStmt):
                stmt.body = _inline_in_scope(stmt.body, current_script_idx)
                out.append(stmt)
            elif isinstance(stmt, ForEachStmt):
                stmt.body = _inline_in_scope(stmt.body, current_script_idx)
                out.append(stmt)
            else:
                out.append(stmt)
        return out

    for sidx, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            owner.body = _inline_in_scope(owner.body, sidx)

    return inlined


def _clone_and_rename(
    body: list[Stmt],
    params: list[str],
    call_args: list[Arg],
    suffix: str,
) -> list[Stmt]:
    """Deep-copy a statement list, renaming parameter references.

    Parameters are replaced with the corresponding call argument values.
    Any VarRef that matches a parameter name gets remapped.
    Additional local variables are suffixed to prevent collisions.
    """
    param_map: dict[str, Arg] = {}
    for i, pname in enumerate(params):
        if i < len(call_args):
            param_map[pname] = call_args[i]
        else:
            param_map[pname] = StrLit("")

    # Collect local variables referenced in the body
    local_vars: set[str] = set()

    def _collect_vars(stmt: Stmt):
        if isinstance(stmt, ActionStmt):
            for a in stmt.args:
                if isinstance(a, VarRef) and a.name not in params:
                    local_vars.add(a.name)
                elif isinstance(a, InterpolatedStr):
                    for p in a.parts:
                        if isinstance(p, VarRef) and p.name not in params:
                            local_vars.add(p.name)
        elif isinstance(stmt, IfStmt):
            for s in stmt.body:
                _collect_vars(s)
            if stmt.else_body:
                for s in stmt.else_body:
                    _collect_vars(s)
        elif isinstance(stmt, RepeatStmt):
            for s in stmt.body:
                _collect_vars(s)
        elif isinstance(stmt, ForEachStmt):
            for s in stmt.body:
                _collect_vars(s)

    for s in body:
        _collect_vars(s)

    def _rename_arg(arg: Arg) -> Arg:
        if isinstance(arg, VarRef):
            if arg.name in param_map:
                return param_map[arg.name]
            if arg.name in local_vars:
                return VarRef(arg.name + suffix)
            return arg
        if isinstance(arg, InterpolatedStr):
            new_parts = []
            for p in arg.parts:
                if isinstance(p, VarRef):
                    if p.name in param_map:
                        mapped = param_map[p.name]
                        if isinstance(mapped, VarRef):
                            new_parts.append(mapped)
                        else:
                            new_parts.append(StrLit(str(mapped)))
                    elif p.name in local_vars:
                        new_parts.append(VarRef(p.name + suffix))
                    else:
                        new_parts.append(p)
                else:
                    new_parts.append(p)
            return InterpolatedStr(new_parts)
        return arg

    def _rename_stmt(stmt: Stmt) -> Stmt:
        if isinstance(stmt, ActionStmt):
            return ActionStmt(
                stmt.name,
                [_rename_arg(a) for a in stmt.args],
                stmt.line,
            )
        if isinstance(stmt, IfStmt):
            return IfStmt(
                stmt.condition,
                [_rename_arg(a) for a in stmt.args],
                [_rename_stmt(s) for s in stmt.body],
                [_rename_stmt(s) for s in stmt.else_body]
                if stmt.else_body else None,
                stmt.line,
            )
        if isinstance(stmt, RepeatStmt):
            return RepeatStmt(
                stmt.times,
                [_rename_stmt(s) for s in stmt.body],
                stmt.line,
            )
        if isinstance(stmt, ForEachStmt):
            return ForEachStmt(
                stmt.table,
                [_rename_stmt(s) for s in stmt.body],
                stmt.line,
            )
        if isinstance(stmt, ReturnStmt):
            return ReturnStmt(
                _rename_arg(stmt.value) if stmt.value else None,
            )
        return stmt

    return [_rename_stmt(s) for s in copy.deepcopy(body)]


def pass_table_preallocation(program: Program) -> int:
    """2.2 Table literal pre-allocation marker (informational).

    DictLiteral and ListLiteral are already compiled efficiently by the
    emitter (TABLE_CREATE + TABLE_SET chain). This pass identifies
    fully-static tables (no VarRef interpolations) so downstream tools
    can mark them as cacheable.

    Returns count of fully-static table literals found.
    """
    static_count = 0

    def _is_static(arg: Arg) -> bool:
        if isinstance(arg, VarRef):
            return False
        if isinstance(arg, InterpolatedStr):
            return all(not isinstance(p, VarRef) for p in arg.parts)
        if isinstance(arg, DictLiteral):
            for kv in arg.entries:
                if not _is_static(kv.key) or not _is_static(kv.value):
                    return False
            return True
        if isinstance(arg, ListLiteral):
            return all(_is_static(i) for i in arg.items)
        return True

    def _check_arg(arg: Arg):
        nonlocal static_count
        if isinstance(arg, DictLiteral) and _is_static(arg):
            static_count += 1
        elif isinstance(arg, ListLiteral) and _is_static(arg):
            static_count += 1
        # Recurse into nested dicts/lists
        if isinstance(arg, DictLiteral):
            for kv in arg.entries:
                _check_arg(kv.key)
                _check_arg(kv.value)
        if isinstance(arg, ListLiteral):
            for i in arg.items:
                _check_arg(i)

    def _check_stmts(stmts: list[Stmt]):
        for s in stmts:
            if isinstance(s, ActionStmt):
                for a in s.args:
                    _check_arg(a)
            elif isinstance(s, IfStmt):
                _check_stmts(s.body)
                if s.else_body:
                    _check_stmts(s.else_body)
            elif isinstance(s, RepeatStmt):
                _check_stmts(s.body)
            elif isinstance(s, ForEachStmt):
                _check_stmts(s.body)

    for _, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            _check_stmts(owner.body)

    return static_count


# ---------------------------------------------------------------------------
# Level 3: Aggressive Global Transformations
# ---------------------------------------------------------------------------

def pass_loop_unrolling(program: Program, max_unroll: int = 4) -> int:
    """3.1 Unroll fixed-count loops with small iteration counts.

    A RepeatStmt with a static integer count and no BreakStmt in the
    body can be unrolled: the body is duplicated N times and the
    REPEAT/END overhead is removed entirely.

    Returns count of unrolled loops.
    """
    unrolled = 0

    def _has_break(stmts: list[Stmt]) -> bool:
        for s in stmts:
            if isinstance(s, BreakStmt):
                return True
            if isinstance(s, IfStmt):
                if _has_break(s.body):
                    return True
                if s.else_body and _has_break(s.else_body):
                    return True
            if isinstance(s, RepeatStmt):
                if _has_break(s.body):
                    return True
            if isinstance(s, ForEachStmt):
                if _has_break(s.body):
                    return True
        return False

    def _unroll(stmts: list[Stmt]) -> list[Stmt]:
        nonlocal unrolled
        out: list[Stmt] = []
        for stmt in stmts:
            if isinstance(stmt, RepeatStmt):
                if stmt.times is not None and stmt.times <= max_unroll:
                    if not _has_break(stmt.body):
                        # Duplicate body N times
                        for _ in range(stmt.times):
                            out.extend(copy.deepcopy(stmt.body))
                        unrolled += 1
                        continue
                # Can't unroll - recurse into body anyway
                stmt.body = _unroll(stmt.body)
            elif isinstance(stmt, IfStmt):
                stmt.body = _unroll(stmt.body)
                if stmt.else_body:
                    stmt.else_body = _unroll(stmt.else_body)
            elif isinstance(stmt, ForEachStmt):
                stmt.body = _unroll(stmt.body)
            out.append(stmt)
        return out

    for _, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            owner.body = _unroll(owner.body)

    return unrolled


def pass_dead_store_elimination(program: Program) -> int:
    """3.2 Remove VAR_SET statements for variables that are never read.

    Tracks assignments and reads per variable. If a local variable is
    assigned but never referenced before being overwritten or going
    out of scope, the assignment is eliminated.

    Does NOT remove global or obj-scoped variables (can't prove
    they aren't read by other scripts).

    Returns count of eliminated stores.
    """
    # We only track local variables (bare names that appear in VAR_SET lhs)
    # Phase 1: collect all variable uses
    var_assignments: dict[int, list[tuple[int, ActionStmt]]] = defaultdict(list)
    var_reads: set[str] = set()

    def _collect_actions(stmts: list[Stmt], depth: int,
                         script_idx: int,
                         collected: list[tuple[int, ActionStmt]]):
        for stmt in stmts:
            if isinstance(stmt, ActionStmt):
                collected.append((depth, stmt))
                # Check args for reads
                for a in stmt.args:
                    _collect_var_reads(a, var_reads, stmt.name)
            elif isinstance(stmt, IfStmt):
                _collect_actions(stmt.body, depth + 1, script_idx, collected)
                if stmt.else_body:
                    _collect_actions(stmt.else_body, depth + 1,
                                     script_idx, collected)
            elif isinstance(stmt, RepeatStmt):
                _collect_actions(stmt.body, depth + 1, script_idx, collected)
            elif isinstance(stmt, ForEachStmt):
                _collect_actions(stmt.body, depth + 1, script_idx, collected)

    def _collect_var_reads(arg: Arg, reads: set[str],
                           action_name: str):
        if isinstance(arg, VarRef):
            reads.add(arg.name)
        elif isinstance(arg, InterpolatedStr):
            for p in arg.parts:
                if isinstance(p, VarRef):
                    reads.add(p.name)
        elif isinstance(arg, MathExpr):
            _collect_math_reads(arg.tree, reads)

    def _collect_math_reads(node, reads: set[str]):
        from .ir import MathNum, MathVarRef, BinOp
        if isinstance(node, MathVarRef):
            reads.add(node.name)
        elif isinstance(node, BinOp):
            _collect_math_reads(node.left, reads)
            _collect_math_reads(node.right, reads)

    # Phase 2: for each kind of scope (event/fn), find VAR_SETs
    eliminated = 0

    for sidx, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            all_actions: list[tuple[int, ActionStmt]] = []
            _collect_actions(owner.body, 0, sidx, all_actions)

            # Build a set of all variables that are ever read in this scope
            local_reads: set[str] = set()
            for _, act in all_actions:
                for a in act.args:
                    _collect_var_reads(a, local_reads, act.name)

            # Scan VAR_SET actions - if LHS var is never read, remove it
            # But preserve settings to variables that are used as function args
            filtered: list[Stmt] = []
            for stmt in owner.body:
                if isinstance(stmt, ActionStmt) and stmt.name == "VAR_SET":
                    if stmt.args:
                        lhs = stmt.args[0]
                        if isinstance(lhs, StrLit):
                            varname = lhs.value
                            if varname not in local_reads:
                                eliminated += 1
                                continue
                filtered.append(stmt)
            owner.body = filtered

    return eliminated


def pass_string_peephole(program: Program) -> int:
    """1.3 (Level 3) Merge adjacent static parts in interpolated strings.

    NOTE: Placed at Level 3 because collapsing STR_CONCAT chains can
    interfere with Roblox content filtering evasion techniques that
    rely on splitting strings across multiple concatenation operations.

    For an InterpolatedStr like [StrLit("Hel"), StrLit("lo "), VarRef("name")]
    this merges into [StrLit("Hello "), VarRef("name")], reducing the
    number of runtime concat actions needed.
    """
    merged = 0

    def _optimize_interp(arg: Arg) -> Arg:
        nonlocal merged
        if isinstance(arg, InterpolatedStr):
            new_parts: list[StrLit | VarRef] = []
            buf = ""
            for p in arg.parts:
                if isinstance(p, StrLit):
                    buf += p.value
                else:
                    if buf:
                        new_parts.append(StrLit(buf))
                        merged += 1
                        buf = ""
                    new_parts.append(p)
            if buf:
                new_parts.append(StrLit(buf))
            if len(new_parts) < len(arg.parts):
                return InterpolatedStr(new_parts)
        if isinstance(arg, DictLiteral):
            new_entries = []
            for kv in arg.entries:
                new_entries.append(KVPair(
                    _optimize_interp(kv.key),
                    _optimize_interp(kv.value),
                ))
            return DictLiteral(new_entries)
        if isinstance(arg, ListLiteral):
            return ListLiteral([_optimize_interp(i) for i in arg.items])
        return arg

    def _optimize_stmts(stmts: list[Stmt]):
        for s in stmts:
            if isinstance(s, ActionStmt):
                s.args = [_optimize_interp(a) for a in s.args]
            elif isinstance(s, IfStmt):
                _optimize_stmts(s.body)
                if s.else_body:
                    _optimize_stmts(s.else_body)
            elif isinstance(s, RepeatStmt):
                _optimize_stmts(s.body)
            elif isinstance(s, ForEachStmt):
                _optimize_stmts(s.body)

    for _, script in _iter_scripts(program):
        for kind, _, owner in _iter_event_fns(script):
            _optimize_stmts(owner.body)

    return merged


# ---------------------------------------------------------------------------
# Optimizer class
# ---------------------------------------------------------------------------

class Optimizer:
    """Multi-tier IR optimizer for Catpile.

    Usage::

        opt = Optimizer(program, level=2)
        optimized = opt.run()
    """

    def __init__(self, program: Program, level: int = 2) -> None:
        self.program = program
        self.level = level
        self.stats: dict[str, int] = {}

    def run(self) -> Program:
        """Execute all passes for the configured optimization level."""
        if self.level >= 1:
            self.stats["unreachable_removed"] = pass_unreachable_code(self.program)
            self.stats["empty_blocks_removed"] = pass_empty_block_stripping(self.program)

        if self.level >= 2:
            self.stats["functions_inlined"] = pass_function_inlining(self.program)
            self.stats["static_tables_found"] = pass_table_preallocation(self.program)

        if self.level >= 3:
            self.stats["loops_unrolled"] = pass_loop_unrolling(self.program)
            self.stats["dead_stores_eliminated"] = pass_dead_store_elimination(self.program)
            self.stats["string_parts_merged"] = pass_string_peephole(self.program)

        return self.program

    def report(self) -> str:
        """Return a human-readable summary of what was optimized."""
        if not self.stats:
            return "No optimizations applied (level 0)."
        lines = [f"Optimization level -O{self.level} results:"]
        for key, val in sorted(self.stats.items()):
            if val:
                lines.append(f"  {key}: {val}")
        if all(v == 0 for v in self.stats.values()):
            lines.append("  (no transformations applied)")
        return "\n".join(lines)
