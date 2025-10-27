# Complex Dataflow Patterns

## Current Status & Limitations

This document addresses complex dataflow patterns including:
1. **Conditionals** (if/else, switch-like patterns)
2. **Nested dependencies** (deep chains)
3. **Combined patterns** (DAG structures)

---

## 1. Conditionals (Multiple Paths to Same Variable)

### Pattern:
```python
if condition:
    result = transform_a(x)  # Path 1
else:
    result = transform_b(x)  # Path 2

use(result)  # result could come from either path
```

### Current Handling:
✅ **Partially Supported** - The tool tracks both assignments to `result`

**Backward slice from `use(result)`:**
```
result ← Line 3: transform_a(x)  [if branch]
result ← Line 5: transform_b(x)  [else branch]
```

**What's Tracked:**
- Both possible sources of `result`
- The variable `x` used in both paths

**What's NOT Tracked:**
- ❌ The condition that determines which path
- ❌ Which path is "more likely" or dominant
- ❌ Control flow relationships

### Example:
```python
def process(mode, data):
    if mode == "fast":
        result = quick_process(data)
    elif mode == "thorough":
        result = deep_process(data)
    else:
        result = default_process(data)

    return result  # TARGET
```

**Backward slice shows:**
- `result` from line 4 (quick_process)
- `result` from line 6 (deep_process)
- `result` from line 8 (default_process)
- All depend on `data`

**Missing:**
- Doesn't show that `mode` determines which path executes
- Doesn't link the condition to the branches

---

## 2. Nested Dependencies (Deep Chains)

### Pattern:
```python
a = get_value()
b = transform(a)
c = process(b)
d = finalize(c)
result = output(d)  # TARGET
```

### Current Handling:
⚠️ **Incomplete** - Single forward pass misses early dependencies (Issue #6)

**Backward slice from `result`:**
```
Current (INCOMPLETE):
  result ← d

Expected (COMPLETE):
  result ← d ← c ← b ← a
```

**Why It Fails:**
- AST visited in order: a, b, c, d, result
- When visiting `a`, we don't know it's relevant yet
- When we discover `d` is relevant (at result), we've already passed `a`, `b`, `c`

**Fix Required:**
Multi-pass approach or reverse traversal (see Issue #6 in KNOWN_ISSUES.md)

---

## 3. Switch-Like Patterns (Same Function, Same Variable)

### Pattern:
```python
match action:
    case "create":
        perform(data)
    case "update":
        perform(data)
    case "delete":
        perform(data)
```

### Current Handling:
✅ **Supported** - Forward slice from `data` shows all three calls to `perform()`

**Forward slice from `data`:**
```
data passed to perform() - Line 3 [create case]
data passed to perform() - Line 5 [update case]
data passed to perform() - Line 7 [delete case]
```

**Visualization Challenge:**
All three are the same function with the same argument, but in different control flow paths.

**Proposed Display (Graph Formatter):**
```
➡️  FORWARD SLICE

  🎯 SOURCE: data

  📤 PASSED TO FUNCTIONS (3 call sites):

     ├─ perform() (Line 3) [case "create"]
     │
     ├─ perform() (Line 5) [case "update"]
     │
     └─ perform() (Line 7) [case "delete"]

  Note: Same function called from different control flow paths
```

---

## 4. Complex DAG Example

### Pattern:
```python
# Source
x = load_data()

# First split
if condition_a:
    y = transform_1(x)
else:
    y = transform_2(x)

# Second split
if condition_b:
    z = process_1(y)
else:
    z = process_2(y)

# Merge
result = finalize(z)
```

### Graph Structure:
```
       x (source)
       │
    ┌──┴──┐
    │  ?  │  condition_a
    └──┬──┘
    │     │
    v     v
transform_1  transform_2
    │     │
    └──┬──┘
       y
       │
    ┌──┴──┐
    │  ?  │  condition_b
    └──┬──┘
    │     │
    v     v
 process_1  process_2
    │     │
    └──┬──┘
       z
       │
       v
    result
```

### Current Handling:
⚠️ **Partial** - Tracks all nodes but doesn't show control flow

**Backward slice from `result`:**
```
result ← z
z ← process_1(y) OR process_2(y)
y ← transform_1(x) OR transform_2(x)
x ← load_data()
```

**Missing:**
- Control flow conditions (condition_a, condition_b)
- Path feasibility (which combinations are possible)

---

## Visualization Solutions

### For Multiple Sources/Branches:

#### Current Tree View:
```
├─ Line 3: y = transform_1(x)
├─ Line 5: y = transform_2(x)
```
❌ Doesn't show these are alternatives

#### Proposed Graph View:
```
📥 SOURCES FOR y (2 paths):

  ┌─── Path 1 (if branch) ───┐
  │  Line 3: y = transform_1(x)
  │
  └─── Path 2 (else branch) ──┘
     Line 5: y = transform_2(x)

All paths depend on: x
```
✅ Shows alternatives clearly

### For Nested Chains:

#### Current (when fixed):
```
├─ Line 7: result = output(d)
├─ Line 6: d = finalize(c)
├─ Line 5: c = process(b)
├─ Line 4: b = transform(a)
└─ Line 3: a = get_value()
```

#### Proposed Chain View:
```
📍 DEPENDENCY CHAIN:

   [Line 3] a = get_value()
              ↓
   [Line 4] b = transform(a)
              ↓
   [Line 5] c = process(b)
              ↓
   [Line 6] d = finalize(c)
              ↓
   [Line 7] result = output(d) ⭐ TARGET

   Chain depth: 5 levels
   Total transformations: 4
```
✅ Shows flow direction clearly

---

## Recommendations

### Immediate (Phase 1):
1. ✅ Graph formatter for divergence (DONE)
2. ⏳ Fix Issue #6 (multi-pass backward slicing)
3. ⏳ Add control flow context to nodes (which branch)

### Future (Phase 2):
1. Track conditions that determine paths
2. Path feasibility analysis
3. Dominant path identification
4. Interactive exploration (expand/collapse branches)

### User Guidance:
For now, users should:
- Use forward slicing (works well) for impact analysis
- Be aware backward slicing may be incomplete (Issue #6)
- Manually inspect conditional branches
- Use both directions (`both`) to see full picture

---

## Test Cases Created

See `tests/unit/test_dag_visualization.py`:
1. ✅ Multiple sources converging
2. ✅ Single source diverging
3. ✅ Diamond pattern (convergence + divergence)

---

**Last Updated**: 2025-10-27
**Status**: Documentation complete, implementation in progress
