"""Emit CatWeb JSON from the Catpile IR.

Handles:
  - Coordinate layout (event blocks on a grid)
  - Action-limit chunking (max ACTIONS_PER_EVENT actions per block)
  - Nested control flow (if/repeat/foreach → "end" closers)
  - Function definitions (Define function event)
  - String interpolation ({var} → STR_CONCAT chain)
  - Math expressions (constant folding + variable math generation)
  - Global ID generation
"""

from __future__ import annotations

import json

from . import mappings as M
from .ir import (
    Arg, Program, ScriptDef, EventDef, FunctionDef,
    ActionStmt, IfStmt, RepeatStmt, ForEachStmt, BreakStmt, ReturnStmt,
    VarRef, StrLit, NumLit, ObjectRef, InterpolatedStr, MathExpr,
    MathNode, MathNum, MathVarRef, BinOp,
    DictLiteral, ListLiteral, KVPair,
)

#: Max actions per event block (CatWeb limit is 120).
ACTIONS_PER_EVENT = 120

#: Grid step for event block placement.
GRID_X = 450
GRID_Y = 450


class EmitError(Exception):
    pass


# ---------------------------------------------------------------------------
# IR helpers
# ---------------------------------------------------------------------------

def _render_arg(arg: Arg) -> str:
    """Render an IR argument to its CatWeb text value."""
    if isinstance(arg, VarRef):
        return "{" + arg.name + "}"
    if isinstance(arg, StrLit):
        return arg.value
    if isinstance(arg, NumLit):
        return arg.value
    if isinstance(arg, ObjectRef):
        return arg.name
    if isinstance(arg, InterpolatedStr):
        # Reconstruct string form: parts like [{o_x_idx}, ".", {o_y_idx}]
        result = ""
        for p in arg.parts:
            if isinstance(p, VarRef):
                result += "{" + p.name + "}"
            else:
                result += p.value
        return result
    if isinstance(arg, MathExpr):
        result = _eval_math_node(arg.tree)
        if result is not None:
            return str(result)
        return ""
    if isinstance(arg, (DictLiteral, ListLiteral)):
        # Will be resolved by _emit_action with prefix actions
        return ""
    if isinstance(arg, str):
        return arg
    return str(arg)


def _eval_math_node(node: MathNode) -> float | int | None:
    """Evaluate a math node tree to a constant, or None if variables found."""
    import operator as opmod

    if isinstance(node, MathNum):
        v = node.value
        return int(v) if "." not in v else float(v)
    if isinstance(node, MathVarRef):
        return None

    if isinstance(node, BinOp):
        left = _eval_math_node(node.left)
        right = _eval_math_node(node.right)
        if left is None or right is None:
            return None
        ops = {
            "+": opmod.add,
            "-": opmod.sub,
            "*": opmod.mul,
            "/": opmod.truediv,
            "%": opmod.mod,
            "^": opmod.pow,
        }
        op_fn = ops.get(node.op)
        if op_fn is None:
            raise EmitError(f"Unknown operator {node.op!r}")
        return op_fn(left, right)
    return None


def _math_op_to_action(op: str) -> str:
    """Map a math operator to the corresponding CatWeb action name."""
    mapping = {
        "+": "VAR_INC",
        "-": "VAR_DEC",
        "*": "VAR_MUL",
        "/": "VAR_DIV",
        "^": "VAR_POW",
        "%": "VAR_MOD",
    }
    return mapping.get(op, "VAR_SET")


def _slot_count(action_name: str) -> int:
    """Number of parameter slots (``{t: …}`` dicts) in an action template."""
    canonical = M.resolve_action(action_name)
    schema = M.ACTIONS.get(canonical)
    if schema is None:
        raise EmitError(f"Unknown action {action_name!r}")
    return sum(1 for s in schema["text"] if isinstance(s, dict))


# ---------------------------------------------------------------------------
# Emitter
# ---------------------------------------------------------------------------

class Emitter:
    """Compile a ``Program`` IR into a CatWeb JSON string."""

    def __init__(self, clean: bool = True) -> None:
        self._idgen = M.IDGen()
        self._temp_counter = 0
        self._clean = clean

    def _temp_var(self) -> str:
        """Generate a unique temporary variable name."""
        self._temp_counter += 1
        return f"_sx_{self._temp_counter}"

    def emit(self, program: Program) -> str:
        """Return CatWeb JSON string for the given program."""
        outputs: list[dict] = []
        for script_def in program.scripts:
            outputs.append(self._emit_script(script_def))
        return json.dumps(outputs, indent=2, ensure_ascii=False)

    def _emit_script(self, script: ScriptDef) -> dict:
        catweb = M.make_script(alias=script.alias)

        x, y = 0, 0
        for ev in script.events:
            blocks = self._emit_event(ev, x, y)
            catweb["content"].extend(blocks)
            x += GRID_X
            if x > 9500:
                x = 0
                y += GRID_Y

        for fn in script.functions:
            catweb["content"].append(self._emit_function(fn, x, y))
            x += GRID_X

        return catweb

    def _emit_event(self, ev: EventDef, x: int, y: int) -> list[dict]:
        actions = self._flatten_body(ev.body)

        chunks: list[list[dict]] = []
        for i in range(0, len(actions), ACTIONS_PER_EVENT):
            chunks.append(actions[i:i + ACTIONS_PER_EVENT])

        blocks: list[dict] = []
        for idx, chunk in enumerate(chunks):
            e = M.make_event(ev.type, idgen=self._idgen,
                             x=x + idx * GRID_X, y=y,
                             clean=self._clean)
            e["actions"] = chunk

            if ev.params:
                slot_idx = 0
                for i, slot in enumerate(e["text"]):
                    if isinstance(slot, dict) and "t" in slot:
                        if slot_idx < len(ev.params):
                            slot["value"] = ev.params[slot_idx]
                            slot_idx += 1
            blocks.append(e)
        return blocks

    def _emit_function(self, fn: FunctionDef, x: int, y: int) -> dict:
        actions = self._flatten_body(fn.body)
        f_event = M.make_event("FUNC_DEF", idgen=self._idgen, x=x, y=y,
                               clean=self._clean)
        for slot in f_event["text"]:
            if isinstance(slot, dict):
                slot["value"] = fn.name
                break
        f_event["actions"] = actions
        if fn.params:
            f_event["variable_overrides"] = [
                {"value": ""} for _ in fn.params
            ]
        return f_event

    def _flatten_body(self, stmts: list) -> list[dict]:
        result: list[dict] = []
        for stmt in stmts:
            result.extend(self._emit_stmt(stmt))
        return result

    def _emit_stmt(self, stmt) -> list[dict]:
        if isinstance(stmt, ActionStmt):
            # Multi-arg console actions: log(x, y, z) → three LOG actions
            if stmt.name in ("LOG", "WARN", "ERROR") and len(stmt.args) > 1:
                return [self._emit_action(
                    ActionStmt(stmt.name, [a], stmt.line)
                ) for a in stmt.args]
            result = self._emit_action(stmt)
            if isinstance(result, list):
                return result
            return [result]

        if isinstance(stmt, IfStmt):
            return self._emit_if(stmt)
        if isinstance(stmt, RepeatStmt):
            return self._emit_repeat(stmt)
        if isinstance(stmt, ForEachStmt):
            return self._emit_foreach(stmt)
        if isinstance(stmt, BreakStmt):
            return [M.make_action("BREAK", idgen=self._idgen)]
        if isinstance(stmt, ReturnStmt):
            val = _render_arg(stmt.value) if stmt.value else ""
            return [M.make_action("RETURN", val, idgen=self._idgen)]

        raise EmitError(f"Unknown statement type: {type(stmt).__name__}")

    def _emit_action(self, stmt: ActionStmt) -> dict | list[dict]:
        """Single action statement → action dict.

        Handles string interpolation and math expressions by injecting
        prefix actions before the main action.

        Tuple slots (``t="tuple"``) collect multiple args into an array of
        ``{value, t, l}`` objects so CatWeb can iterate over them.
        """
        line_info = f" at line {stmt.line}" if stmt.line else ""
        try:
            canonical = M.resolve_action(stmt.name)
        except KeyError as e:
            raise EmitError(f"{str(e)}{line_info}") from None

        schema = M.ACTIONS.get(canonical, {})
        text_slots = schema.get("text", [])

        # Collect dict slots (parameter slots) from the schema text template
        dict_slots = [
            (text_idx, slot)
            for text_idx, slot in enumerate(text_slots)
            if isinstance(slot, dict)
        ]

        # Pre-count remaining non-tuple dict slots after each position.
        # Used to determine how many args a tuple slot consumes.
        remaining_non_tuple = 0
        remaining_counts = [0] * len(dict_slots)
        for i in range(len(dict_slots) - 1, -1, -1):
            _, s = dict_slots[i]
            if s.get("t") != "tuple":
                remaining_non_tuple += 1
            remaining_counts[i] = remaining_non_tuple

        prefix_actions: list[dict] = []
        values: list = []
        arg_idx = 0

        for slot_idx, (_, slot_schema) in enumerate(dict_slots):
            if slot_schema.get("t") == "tuple":
                # Tuple slot: consume all remaining args except those reserved
                # for non-tuple dict slots that follow.
                end = len(stmt.args) - remaining_counts[slot_idx]
                tuple_args = list(stmt.args[arg_idx:end])
                arg_idx = end

                # Build tuple value as an array of param objects
                tuple_value: list[dict] = []
                for ta in tuple_args:
                    rendered = self._resolve_arg(ta, prefix_actions)
                    tuple_value.append({
                        "value": rendered,
                        "t": "string",
                        "l": "any",
                    })
                values.append(tuple_value)
            else:
                # Non-tuple slot: consume 1 arg
                if arg_idx < len(stmt.args):
                    rendered = self._resolve_arg(
                        stmt.args[arg_idx], prefix_actions
                    )
                    arg_idx += 1
                    # Name slots (l: variable, l: x, l: y, etc.) expect bare
                    # identifiers, not {var} references.
                    label = slot_schema.get("l", "")
                    is_name_slot = (
                        (label and label != "any" and slot_schema.get("t") != "any")
                        or slot_schema.get("t") == "object"
                    )
                    if is_name_slot and rendered.startswith("{") and rendered.endswith("}"):
                        rendered = rendered[1:-1]
                    values.append(rendered)
                else:
                    values.append("")

        result = M.make_action(stmt.name, *values,
                               clean=self._clean, idgen=self._idgen)

        if prefix_actions:
            prefix_actions.append(result)
            return prefix_actions  # type: ignore

        return result

    def _math_tree_to_actions(self, node: MathNode,
                               actions: list[dict]) -> str:
        """Convert a math expression tree into VAR_* actions, appending to
        *actions*. Returns the temp variable name or literal value."""
        if isinstance(node, MathNum):
            return node.value  # return literal number directly

        if isinstance(node, MathVarRef):
            return node.name  # use the variable directly

        if isinstance(node, BinOp):
            left_var = self._math_tree_to_actions(node.left, actions)
            right_var = self._math_tree_to_actions(node.right, actions)
            op_name = _math_op_to_action(node.op)
            tmp = self._temp_var()

            # Detect if operands are literals vs variable refs
            left_is_literal = left_var.lstrip("-").replace(".", "").isdigit()
            right_is_literal = right_var.lstrip("-").replace(".", "").isdigit()

            left_ref = "{" + left_var + "}" if not left_is_literal else left_var
            right_ref = "{" + right_var + "}" if not right_is_literal else right_var

            if op_name in ("VAR_INC", "VAR_DEC"):
                # Always store in a temp for expression contexts
                # inc/dec take (variable, number) and modify in-place
                # We need: set tmp = left, then inc/dec tmp by right
                actions.append(M.make_action("VAR_SET", left_ref, tmp,
                                             idgen=self._idgen))
                actions.append(M.make_action(op_name, tmp, right_ref,
                                             idgen=self._idgen))
            elif op_name == "VAR_SET":
                actions.append(M.make_action(op_name, left_ref, right_ref,
                                             idgen=self._idgen))
            else:
                # VAR_MUL, VAR_DIV, VAR_POW, VAR_MOD: modify in-place
                # Store left in temp, then do op
                actions.append(M.make_action("VAR_SET", left_ref, tmp,
                                             idgen=self._idgen))
                actions.append(M.make_action(op_name, tmp, right_ref,
                                             idgen=self._idgen))

            return tmp

        return ""


    def _resolve_arg(self, arg: Arg, prefix_actions: list[dict]) -> str:
        """Resolve an IR argument to a CatWeb string value.

        For simple args this returns the rendered string directly.
        For complex args (interpolation, math, dict/list), this generates
        prefix actions and returns a variable reference to the result.
        """
        if isinstance(arg, InterpolatedStr) and len(arg.parts) > 1:
            return self._emit_interpolation(arg, prefix_actions)
        if isinstance(arg, MathExpr):
            const = _eval_math_node(arg.tree)
            if const is not None:
                return str(const)
            tmp = self._math_tree_to_actions(arg.tree, prefix_actions)
            return "{" + tmp + "}"
        if isinstance(arg, DictLiteral):
            return self._emit_dict(arg, prefix_actions)
        if isinstance(arg, ListLiteral):
            return self._emit_list(arg, prefix_actions)
        return _render_arg(arg)

    def _emit_interpolation(self, arg: InterpolatedStr,
                             prefix_actions: list[dict]) -> str:
        parts = arg.parts
        chain = self._temp_var()
        left = self._part_str(parts[0])
        right = self._part_str(parts[1])
        prefix_actions.append(
            M.make_action("STR_CONCAT", left, right, chain,
                          idgen=self._idgen)
        )
        for p in parts[2:]:
            p_str = self._part_str(p)
            nxt = self._temp_var()
            prefix_actions.append(
                M.make_action("STR_CONCAT", "{" + chain + "}", p_str, nxt,
                              idgen=self._idgen)
            )
            chain = nxt
        return "{" + chain + "}"

    @staticmethod
    def _part_str(part: StrLit | VarRef) -> str:
        if isinstance(part, VarRef):
            return "{" + part.name + "}"
        return part.value

    def _emit_dict(self, arg: DictLiteral,
                    prefix_actions: list[dict]) -> str:
        table = self._temp_var()
        prefix_actions.append(
            M.make_action("TABLE_CREATE", table, idgen=self._idgen)
        )
        for kv in arg.entries:
            k_str = _render_arg(kv.key)
            v_str = _render_arg(kv.value)
            prefix_actions.append(
                M.make_action("TABLE_SET", k_str, table, v_str,
                              idgen=self._idgen)
            )
        return "{" + table + "}"

    def _emit_list(self, arg: ListLiteral,
                    prefix_actions: list[dict]) -> str:
        table = self._temp_var()
        prefix_actions.append(
            M.make_action("TABLE_CREATE", table, idgen=self._idgen)
        )
        for idx, item in enumerate(arg.items):
            v_str = _render_arg(item)
            prefix_actions.append(
                M.make_action("TABLE_SET", str(idx + 1), table, v_str,
                              idgen=self._idgen)
            )
        return "{" + table + "}"

    def _emit_if(self, stmt: IfStmt) -> list[dict]:
        blocks: list[dict] = []
        rendered = [_render_arg(a) for a in stmt.args]
        slot_n = _slot_count(stmt.condition)
        while len(rendered) < slot_n:
            rendered.append("")
        blocks.append(M.make_action(stmt.condition, *rendered,
                                    idgen=self._idgen))

        for s in stmt.body:
            blocks.extend(self._emit_stmt(s))

        if stmt.else_body:
            blocks.append(M.make_action("ELSE", idgen=self._idgen))
            for s in stmt.else_body:
                blocks.extend(self._emit_stmt(s))

        blocks.append(M.make_action("END", idgen=self._idgen))
        return blocks

    def _emit_repeat(self, stmt: RepeatStmt) -> list[dict]:
        blocks: list[dict] = []
        if stmt.times is not None:
            val = str(stmt.times)
            # Variable reference: wrap in {braces} for the number slot
            if val and val[0].isalpha():
                val = "{" + val + "}"
            blocks.append(M.make_action("REPEAT", val, idgen=self._idgen))
        else:
            blocks.append(M.make_action("REPEAT_FOREVER", idgen=self._idgen))
        for s in stmt.body:
            blocks.extend(self._emit_stmt(s))
        blocks.append(M.make_action("END", idgen=self._idgen))
        return blocks

    def _emit_foreach(self, stmt: ForEachStmt) -> list[dict]:
        blocks: list[dict] = []
        rendered = _render_arg(stmt.table)
        # VarRef → "{name}" (variable reference), StrLit → "name" (literal)
        blocks.append(M.make_action("TABLE_ITER", rendered,
                                    idgen=self._idgen))
        for s in stmt.body:
            blocks.extend(self._emit_stmt(s))
        blocks.append(M.make_action("END", idgen=self._idgen))
        return blocks
