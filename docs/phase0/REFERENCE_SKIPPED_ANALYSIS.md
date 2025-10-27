# Reference: Complete Dataflow Analysis of `skipped` Variable

## 📋 Purpose

This document preserves the **real-world dataflow analysis** that inspired the PySlice project. It serves as:
- ✅ **Reference example** for what PySlice should achieve
- ✅ **Test case** for validating PySlice accuracy
- ✅ **Documentation** of manual analysis process

## 🎯 The Problem (isort #2412)

**Issue**: When isort skips files, it prints relative paths instead of absolute paths, making debugging harder.

**Example Output (BEFORE fix)**:
```
test.py was skipped as it's listed in 'skip' setting...
Skipped 1 files
```

**Desired Output (AFTER fix)**:
```
/home/user/project/test.py was skipped as it's listed in 'skip' setting...
Skipped 1 files
```

## 🔍 Manual Dataflow Analysis

### Target: `skipped` variable at line 1251 in main.py

**Question**: Where do the values in `skipped` come from?

### Complete Dataflow Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATAFLOW GRAPH: skipped                      │
└─────────────────────────────────────────────────────────────────┘

DEF-1: main.py:1171 in main()
  ┌──────────────────────────┐
  │ skipped: List[str] = []  │  ← CREATION
  └──────────┬───────────────┘
             │
             ├─→ (conditional) DEF-2: main.py:1178 in main()
             │    ┌────────────────────────────────────────────────┐
             │    │ if config.filter_files:                        │
             │    │   if config.is_skipped(Path(file_name)):       │
             │    │     skipped.append(str(Path(...).resolve()))   │ ✨ FIX
             │    │     # BEFORE: skipped.append(file_name)         │
             │    │     # AFTER:  absolute path                     │
             │    └────────────┬───────────────────────────────────┘
             │                 │
             ↓                 ↓
             USE-1 + DEF-3,4,5: main.py:1183 in main()
             ┌──────────────────────────────────────────────────────┐
             │ file_names = files.find(file_names, config,          │
             │                         skipped, broken)             │
             │                         ^^^^^^^^                     │
             │                         Passed as mutable reference  │
             │                                                       │
             │  ╔══════════════════════════════════════════════╗   │
             │  ║ Inside files.find() in files.py:             ║   │
             │  ╚══════════════════════════════════════════════╝   │
             │                                                       │
             │    DEF-4: files.py:24 in find()                      │
             │      for dirname in list(dirnames):                  │
             │        full_path = base_path / dirname               │
             │        if config.is_skipped(full_path):              │
             │          skipped.append(str(full_path))  ✨ FIX      │
             │          # BEFORE: skipped.append(dirname)           │
             │          # AFTER:  absolute path                     │
             │                                                       │
             │    DEF-5: files.py:35 in find()                      │
             │      for filename in filenames:                      │
             │        filepath = os.path.join(dirpath, filename)    │
             │        if config.is_skipped(...):                    │
             │          skipped.append(os.path.abspath(filepath))   │
             │          # BEFORE: skipped.append(filename)  ✨ FIX  │
             │          # AFTER:  absolute path                     │
             └──────────────────┬───────────────────────────────────┘
                                │
                                │ (list now populated with absolute paths)
                                │
                                ↓
             USE-2: main.py:1248 in main()
             ┌─────────────────────────────────────┐
             │ num_skipped += len(skipped)         │
             │                ^^^^^^^^^^^^         │
             │                READ (count)         │
             └──────────┬──────────────────────────┘
                        │
                        ↓
             USE-3: main.py:1249 in main()
             ┌──────────────────────────────────────┐
             │ if num_skipped and not config.quiet: │
             │    ^^^^^^^^^^^                       │
             │    Control flow depends on length    │
             └──────────┬───────────────────────────┘
                        │
                        ↓
             USE-4: main.py:1251 in main() ⭐ TARGET
             ┌──────────────────────────────────────────────┐
             │ for was_skipped in skipped:                  │
             │                    ^^^^^^^^                  │
             │                    ITERATE & READ            │
             │   print(f"{was_skipped} was skipped...")     │
             │          ^^^^^^^^^^^^^^                       │
             │          USE each element value               │
             │                                               │
             │ NOW PRINTS: /home/user/project/test.py       │
             │ BEFORE WAS: test.py                          │
             └──────────────────────────────────────────────┘
```

## 📊 Def-Use Chains Analysis

### Definition Sites (Where values are added to `skipped`)

| Location | Function | Code | Value Type |
|----------|----------|------|------------|
| main.py:1171 | main() | `skipped: List[str] = []` | Empty list |
| main.py:1178 | main() | `skipped.append(str(Path(file_name).resolve()))` | Absolute path ✨ |
| files.py:24 | find() | `skipped.append(str(full_path))` | Absolute path ✨ |
| files.py:35 | find() | `skipped.append(os.path.abspath(filepath))` | Absolute path ✨ |

### Use Sites (Where `skipped` is read)

| Location | Function | Code | Purpose |
|----------|----------|------|---------|
| main.py:1183 | main() | `files.find(..., skipped, ...)` | Pass to function |
| main.py:1248 | main() | `len(skipped)` | Count items |
| main.py:1249 | main() | `if num_skipped ...` | Control flow |
| main.py:1251 | main() | `for was_skipped in skipped:` | Iterate & print ⭐ |

## 🔧 The Fix

### Changes Made:

#### 1. main.py:1178 (filter_files path)

**BEFORE:**
```python
if config.is_skipped(Path(file_name)):
    skipped.append(file_name)  # Relative: "test.py"
```

**AFTER:**
```python
if config.is_skipped(Path(file_name)):
    skipped.append(str(Path(file_name).resolve()))  # Absolute: "/home/.../test.py"
```

#### 2. files.py:24 (directory skipping)

**BEFORE:**
```python
if config.is_skipped(full_path):
    skipped.append(dirname)  # Relative: "tests"
    dirnames.remove(dirname)
```

**AFTER:**
```python
if config.is_skipped(full_path):
    skipped.append(str(full_path))  # Absolute: "/home/.../tests"
    dirnames.remove(dirname)
```

#### 3. files.py:35 (file skipping)

**BEFORE:**
```python
if config.is_skipped(Path(os.path.abspath(filepath))):
    skipped.append(filename)  # Relative: "test.py"
```

**AFTER:**
```python
if config.is_skipped(Path(os.path.abspath(filepath))):
    skipped.append(os.path.abspath(filepath))  # Absolute: "/home/.../test.py"
```

## 🧪 Testing the Fix

### Test Setup:
```bash
cd /tmp
mkdir isort_test
cd isort_test

# Create test file
cat > test.py << 'EOF'
import os
import sys
EOF

# Create config to skip it
cat > .isort.cfg << 'EOF'
[settings]
skip=test.py
EOF

# Run isort with verbose
isort . -v
```

### Output BEFORE Fix:
```
test.py was skipped as it's listed in 'skip' setting...
Skipped 1 files
```

### Output AFTER Fix:
```
/tmp/isort_test/test.py was skipped as it's listed in 'skip' setting...
Skipped 1 files
```

✅ **Success!** Now shows absolute path.

## 🎯 PySlice Goal: Automate This Analysis

**What we did manually:**
1. ✅ Identified all definition sites (4 locations)
2. ✅ Traced backward from use site (line 1251)
3. ✅ Followed cross-file dataflow (main.py → files.py)
4. ✅ Tracked pass-by-reference (mutable list)
5. ✅ Showed function context
6. ✅ Visualized complete flow

**What PySlice should do:**
```bash
$ flowslice both main.py:1251:skipped
```

**Expected output:**
```
⬅️  BACKWARD SLICE (How did we get here?)

  📁 main.py → main()
    ├─ Line 1171: skipped: List[str] = []
    ├─ Line 1178: skipped.append(str(Path(file_name).resolve()))
    │  └─ depends on: file_name, Path
    │  └─ context: if config.filter_files
    └─ Line 1183: files.find(file_names, config, skipped, broken)
       └─ passed to: files.find()

  📁 files.py → find()
    ├─ Line 9: def find(..., skipped: List[str], ...)
    │  └─ parameter (mutable)
    ├─ Line 24: skipped.append(str(full_path))
    │  └─ depends on: full_path
    │  └─ context: if config.is_skipped(full_path)
    └─ Line 35: skipped.append(os.path.abspath(filepath))
       └─ depends on: filepath
       └─ context: if config.is_skipped(...)

➡️  FORWARD SLICE (Where does it go?)

  📁 main.py → main()
    ├─ Line 1248: num_skipped += len(skipped)
    │  └─ operation: count length
    ├─ Line 1249: if num_skipped and not config.quiet:
    │  └─ control flow
    └─ Line 1251: for was_skipped in skipped:  ⭐
       └─ Line 1253: print(f"{was_skipped} was skipped...")
          └─ outputs each element
```

## 📐 Accuracy Comparison

### Manual Analysis:
- ✅ Found all 4 definition sites
- ✅ Tracked cross-file flow
- ✅ Identified pass-by-reference
- ✅ Showed function context
- ⏱️ Time: ~10 minutes

### PySlice POC:
```bash
$ python flowslice_poc.py /home/plawate/git_space/isort/isort/main.py:1251:skipped backward
```

**Results**:
- ✅ Found line 1178 (append in main.py)
- ⚠️ Noise: Found unrelated `skipped: bool` from SortAttempt class
- ❌ Missed: Cross-file flow to files.py (single-file analysis only)
- ✅ Showed: Function names (main, __init__, sort_imports)
- ⏱️ Time: ~1 second

### Gap Analysis:

| Feature | Manual | POC | Target |
|---------|--------|-----|--------|
| Backward slice | ✅ | ✅ | ✅ |
| Forward slice | ✅ | ✅ | ✅ |
| Function names | ✅ | ✅ | ✅ |
| Cross-file | ✅ | ❌ | ✅ |
| Type-aware | ✅ | ❌ | ✅ |
| Pass-by-ref | ✅ | ❌ | ✅ |

## 🎓 Lessons Learned

### 1. **Cross-File Analysis is Critical**

The fix required changes in TWO files:
- main.py (1 location)
- files.py (2 locations)

PySlice MUST handle cross-file flow!

### 2. **Type Awareness Reduces Noise**

There are TWO different `skipped` variables in main.py:
- `skipped: List[str]` (our target)
- `skipped: bool` (in SortAttempt class)

Type annotations can disambiguate!

### 3. **Pass-by-Reference is Common**

The `skipped` list is passed to `files.find()` and modified in-place:
```python
def find(paths, config, skipped, broken):  # ← receives list
    ...
    skipped.append(...)  # ← modifies caller's list!
```

This is crucial to track!

### 4. **Function Context is Essential**

Knowing the function name helps understanding:
- `main()` creates the list
- `find()` populates it
- `main()` consumes it

Much better than just line numbers!

## 🧪 Use This as Test Case

### Test Data:
- **Files**: `isort/main.py`, `isort/files.py`
- **Target**: `main.py:1251:skipped`
- **Direction**: `both`

### Expected Results:

**Backward Slice Should Find**:
- [ ] main.py:1171 (creation)
- [ ] main.py:1178 (conditional append)
- [ ] main.py:1183 (pass to find)
- [ ] files.py:9 (parameter)
- [ ] files.py:24 (append in loop)
- [ ] files.py:35 (append in loop)

**Forward Slice Should Find**:
- [ ] main.py:1183 (pass to function)
- [ ] main.py:1248 (len())
- [ ] main.py:1249 (if condition)
- [ ] main.py:1251 (for loop)
- [ ] main.py:1253 (print)

**Should NOT Include**:
- [ ] main.py:69-110 (different `skipped: bool` variable)

### Validation:
```bash
# Run PySlice on this exact case
flowslice both isort/main.py:1251:skipped

# Compare output to this reference
# All items from "Expected Results" should be present
```

## 📝 Manual Analysis Process (for Reference)

### Step 1: Identify Target
- File: main.py
- Line: 1251
- Variable: `skipped`
- Context: Used in for loop

### Step 2: Backward Trace
1. Search for `skipped` assignments before line 1251
2. Found: Line 1171 - `skipped: List[str] = []`
3. Found: Line 1178 - `skipped.append(...)`
4. Found: Line 1183 - passed to `files.find()`

### Step 3: Cross-File Trace
5. Open files.py
6. Find `find()` function signature
7. See `skipped` is parameter (line 9)
8. Search for `skipped.append` in that function
9. Found: Line 24 (directory skip)
10. Found: Line 35 (file skip)

### Step 4: Forward Trace
11. Search for `skipped` uses after line 1171
12. Found: Line 1248 - `len(skipped)`
13. Found: Line 1251 - `for ... in skipped`
14. Found: Line 1253 - `print(f"{was_skipped}...")`

### Step 5: Verify
15. Check types (List[str])
16. Verify all paths lead to/from target
17. Document dependencies

**Total Time**: ~10 minutes
**Lines Examined**: ~100
**Files Opened**: 2

## 🎯 Success Criteria for PySlice

**PySlice succeeds when**:
```bash
$ flowslice both main.py:1251:skipped
```

Produces output that:
1. ✅ Shows ALL 6 modification points
2. ✅ Includes BOTH files (main.py and files.py)
3. ✅ Shows function names for each location
4. ✅ Displays code snippets
5. ✅ Excludes unrelated `skipped: bool`
6. ✅ Completes in <5 seconds
7. ✅ Presents in readable tree format

**Bonus points for**:
- 🎁 Interactive HTML output
- 🎁 Click to jump to location
- 🎁 Syntax highlighting
- 🎁 Diff view (before/after fix)
- 🎁 Export to diagram

---

**Last Updated**: 2025-10-03
**Purpose**: Reference for PySlice development
**Status**: Complete manual analysis documented
**Next**: Use as test case for PySlice
