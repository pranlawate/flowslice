# Known Issues & Limitations

**Status**: All critical bugs fixed! ✅
**Last Updated**: 2025-10-27

---

## 📊 Summary

| Issue | Status | Severity | Description |
|-------|--------|----------|-------------|
| #1 | ✅ Fixed | High | Backward slice pollution (line number checks) |
| #2 | ✅ Fixed | Low | Missing TARGET marker in backward slices |
| #3 | ✅ Fixed | Medium | Duplicate nodes in output |
| #4 | ⚠️ Limitation | High | No inter-procedural analysis (Phase 2) |
| #5 | ✅ Fixed | High | Forward slice pollution (function scope) |
| #6 | ✅ Fixed | High | Missing transitive dependencies (multi-pass) |

**All critical bugs resolved!** The tool now correctly handles:
- ✅ Intra-procedural dataflow analysis
- ✅ Transitive dependencies (multi-pass backward slicing)
- ✅ Function scope boundaries (no pollution)
- ✅ Derived variable tracking
- ✅ Complex DAG patterns (convergence/divergence)

---

## ⚠️ Current Limitations

### 1. No Inter-Procedural Analysis (Issue #4)
**Severity**: High (architectural limitation)
**Planned**: Phase 2

**What it means:**
- Can't trace dataflow **into** function bodies
- Can't track **return values** back to caller
- Limited to single-function analysis

**Example:**
```python
def process(x):
    result = transform(x)  # Can't trace into transform()
    return result          # Can't track return back to caller

data = get_data()
output = process(data)      # Shows data passed to process()
                           # But NOT what happens inside process()
```

**Workaround:**
Manually slice inside the called function:
```bash
# First: slice at call site
flowslice main.py:10:data both

# Then: slice inside the function
flowslice main.py:45:result both  # where result is inside process()
```

---

### 2. No Cross-File Analysis
**Severity**: Medium
**Planned**: Phase 1 (remaining work)

**What it means:**
- Can't follow variables across module imports
- Limited to single file

**Example:**
```python
# main.py
from utils import process_data
result = process_data(x)  # Can't trace into utils.py
```

---

### 3. No Control Flow Tracking
**Severity**: Low
**Planned**: Phase 2

**What it means:**
- Shows all branches (if/else) but doesn't track which executes
- No path feasibility analysis

**Example:**
```python
if condition:
    result = path_a(x)  # Branch 1
else:
    result = path_b(x)  # Branch 2

use(result)  # Shows BOTH paths, doesn't know which executes
```

---

### 4. Limited AST Node Coverage
**Severity**: Low

**Not yet tracked:**
- Lambda expressions
- Walrus operator (`:=`)
- Match/case statements (partial)
- Complex comprehensions (partial)

---

## 🐛 Fixed Issues (For Reference)

<details>
<summary><b>Issue #1: Backward Slice Pollution ✅ FIXED</b></summary>

**Problem**: Backward slicing included ALL occurrences of variables throughout file, even those AFTER the target line.

**Fix**: Added line number checks: `if node.lineno <= self.target_line`

**Impact**: Backward slices now only show code that actually contributes to the target.
</details>

<details>
<summary><b>Issue #2: Missing TARGET Marker ✅ FIXED</b></summary>

**Problem**: Forward slices showed `⭐ TARGET` but backward slices didn't.

**Fix**: Added marker to both directions in tree formatter.

**Impact**: Better UX, easier to identify target line.
</details>

<details>
<summary><b>Issue #3: Duplicate Nodes ✅ FIXED</b></summary>

**Problem**: Same line appeared multiple times (e.g., 3 duplicate entries for line 3591).

**Fix**: Added `_merge_nodes_by_line()` helper to deduplicate by line number.

**Impact**: Cleaner, more concise output.
</details>

<details>
<summary><b>Issue #5: Forward Slice Pollution ✅ FIXED</b></summary>

**Problem**: Forward slices included functions defined later in file but NOT in execution path.

**Example:**
```python
def main():
    file_path = "input.txt"  # TARGET
    process(file_path)

def unrelated_function():
    file_path = "other.txt"  # Was WRONGLY included
```

**Fix**: Added function scope tracking with `self.target_function`.

**Impact**: Forward slices now respect function boundaries.
</details>

<details>
<summary><b>Issue #6: Missing Transitive Dependencies ✅ FIXED</b></summary>

**Problem**: Single-pass backward slicing missed dependencies defined before they were discovered.

**Example:**
```python
base = 10              # Line 3 - was MISSED
x = base * 2           # Line 4 - was MISSED
y = base + 5           # Line 5 - was MISSED
z = base - 3           # Line 6 - was MISSED
result = calc(x,y,z)   # Line 7 - TARGET
```

**Fix**: Implemented multi-pass approach (up to 10 passes, stops when converged).

**Impact**: Backward slices now find complete dependency chains.
</details>

---

## 📖 See Also

- [README.md](README.md) - Getting started and usage
- [ROADMAP.md](ROADMAP.md) - Development roadmap and phases
- [COMPLEX_DATAFLOW_HANDLING.md](COMPLEX_DATAFLOW_HANDLING.md) - DAG patterns, conditionals
- [VISUALIZATION_OPTIONS.md](VISUALIZATION_OPTIONS.md) - Different output formats
- [docs/phase0/](docs/phase0/) - Phase 0 research and decisions
