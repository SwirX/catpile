# Compiler: Optimizer

The optimizer runs passes on the IR to produce smaller, faster CatWeb output.

## Optimization Levels

### `-O0` (None)

No optimization. The IR is emitted as-is. Fastest compile, largest output.

### `-O1` (Default)

Basic optimizations that don't change semantics:

- **Constant folding** - evaluates compile-time expressions:
  ```python
  # Before: n = 2 + 3 * 4
  # After:  n = 14  (folded)
  ```
- **Dead code elimination** - removes unreachable statements after `break`/`return`:
  ```python
  repeat_forever:
      if eq(x, 1):
          break
      log("after break")   # Dead - removed
  ```
- **Unused variable elimination** - removes variable assignments that are never read

### `-O2` (Aggressive)

More aggressive transformations:

- **Inline expansion** - short function bodies are inlined at call sites
- **Loop unrolling** - small fixed-count `repeat(N)` loops are unrolled:
  ```python
  # Before: repeat(3): log("x")
  # After:  log("x"); log("x"); log("x")
  ```
- **Branch simplification** - merges consecutive IF statements with same condition
- **Peephole optimization** - replaces VAR_SET X, 0; VAR_INC X, 1 → VAR_SET X, 1

### `-O3` (Maximum)

Experimental transformations:

- **Array hoisting** - TABLE_SET calls to the same table are combined
- **Strength reduction** - `n * 2` → `n + n`, `n / 2` → `n * 0.5`
- **CSE (Common Subexpression Elimination)** - repeated expressions computed once
- **Tail call optimization** - `return func_run(...)` flattened

## Pass Pipeline

Optimizations run as ordered passes:

```python
def optimize(program, level):
    if level >= 1:
        program = constant_fold(program)
        program = dead_code_elim(program)
        program = unused_var(program)
    if level >= 2:
        program = inline_functions(program)
        program = loop_unroll(program)
        program = peephole(program)
    if level >= 3:
        program = cse(program)
        program = tail_call(program)
    return program
```

## Constant Folding

Evaluates expressions with only literal operands:

```python
# Compile-time
n = 2 + 3 * 4     → NumLit(14)

# Runtime (variables involved)
n = {x} * {ITEM_SIZE}  → MUL x, ITEM_SIZE  (unchanged)
```

Folding works for:
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- String concatenation: `"a" + "b"` → `"ab"`

## Loop Unrolling

```python
# Before:
repeat(4):
    log("item")

# After:
log("tile")
log("tile")
log("tile")
log("tile")
```

Unrolling threshold: only loops with count ≤ 8 are unrolled.

## Peephole Optimization

Pattern matching on short instruction sequences:

| Pattern | Replacement |
|---|---|
| `VAR_SET X, 0; VAR_INC X, 1` | `VAR_SET X, 1` |
| `IF_EQ a, a` | (removed) |
| `GOTO next; LOG x` | `LOG x` |
| `STR_CONCAT "a", ""` | `STR_CONCAT "a"` |

## Dead Code Elimination

Removes code that can never execute:

```python
repeat_forever:
    if eq(x, 0):
        break
    log("unreachable")  # Removed - after break
```

Also removes unreachable function definitions and empty event handlers.
