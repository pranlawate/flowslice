# Cross-File Analysis

**Status**: ✅ Available (Phase 1 Complete!)
**Version**: 0.2.0+
**Last Updated**: 2025-10-27

---

## 🎉 Overview

flowslice now supports **cross-file analysis**! It can track dataflow across module boundaries when functions are imported from other files.

---

## ✨ Features

### What Works

1. ✅ **Import Resolution**
   - `from module import function`
   - `from module import function as alias`
   - `import module`
   - Relative imports (same directory)
   - Package imports (`__init__.py`)

2. ✅ **Automatic Tracking**
   - Imports parsed automatically
   - Module ASTs cached for performance
   - Works with both backward and forward slicing

3. ✅ **Multi-File Awareness**
   - Tracks which file each node comes from
   - Handles import aliases correctly
   - Graceful fallback if imports can't be resolved

---

## 📖 Usage

### Basic Example

**utils.py:**
```python
def read_config(config_path):
    with open(config_path) as f:
        return f.read()
```

**main.py:**
```python
from utils import read_config

def main():
    path = "config.ini"
    data = read_config(path)  # <-- Slice this!
    process(data)
```

**Command:**
```bash
flowslice main.py:6:data both
```

**Result:**
- Backward slice shows: `path` assignment and import
- Import resolver finds `read_config` in `utils.py`
- Tracks that `data` depends on `path` via the imported function

---

## 🔧 How It Works

### Architecture

1. **Import Parsing** (`ImportResolver`)
   - Parses all `import` and `from...import` statements
   - Builds map: `{function_name: (file_path, original_name)}`
   - Resolves relative paths

2. **AST Caching**
   - Imported files parsed once
   - ASTs cached in memory
   - Reused across multiple slices

3. **Slicer Integration**
   - Import map passed to `SlicerVisitor`
   - Available during dataflow analysis
   - Used when function calls detected

### Enabling/Disabling

**Enabled by default:**
```python
slicer = Slicer()  # Cross-file ON
```

**Disable if needed:**
```python
slicer = Slicer(enable_cross_file=False)  # Single-file only
```

---

## 📊 Current Scope

### Phase 1 Implementation (Current)

**What's Included:**
- ✅ Direct imports (one level)
- ✅ Function call tracking
- ✅ Import alias resolution
- ✅ Same-directory modules
- ✅ Package imports

**What's NOT Included (Yet):**
- ❌ Tracing INTO function bodies (inter-procedural - Phase 2)
- ❌ Tracking return values back (inter-procedural - Phase 2)
- ❌ Transitive imports (imports of imports)
- ❌ Dynamic imports (`importlib`)
- ❌ Relative imports (`from .. import`)

---

## 🧪 Examples

### Example 1: Simple Import

**helpers.py:**
```python
def validate(value):
    return value is not None
```

**main.py:**
```python
from helpers import validate

user_input = get_input()
if validate(user_input):  # Slice 'user_input' forward
    process(user_input)
```

Shows that `user_input` is passed to both `validate()` and `process()`.

---

### Example 2: Import with Alias

**utils.py:**
```python
def process_data(input):
    return transform(input)
```

**main.py:**
```python
from utils import process_data as process

data = load()
result = process(data)  # Slice 'data'
```

Correctly handles the alias `process` → `process_data`.

---

### Example 3: Multiple Imports

**config.py:**
```python
def read_config(path):
    return open(path).read()

def parse_config(raw):
    return raw.split('\n')
```

**main.py:**
```python
from config import read_config, parse_config

path = "app.conf"
raw = read_config(path)
parsed = parse_config(raw)  # Slice 'parsed' backward
```

Traces back: `parsed` ← `raw` ← `path`

---

## 🎯 Limitations

### 1. Single Level
**Current**: Only direct imports
```python
# main.py
from utils import helper  # ✅ Tracked

# utils.py
from core import process  # ❌ Not tracked
```

**Workaround**: Manually slice in `utils.py`

### 2. No Inter-Procedural Analysis
**Current**: Sees function is called, doesn't trace inside
```python
# main.py
result = helper(x)  # Knows x is passed to helper

# utils.py
def helper(value):
    processed = transform(value)  # ❌ Doesn't trace this
    return processed
```

**Planned**: Phase 2 feature

### 3. Same Directory Only
**Current**: Resolves imports in same directory
```python
from utils import helper  # ✅ Works if utils.py in same dir
from package.utils import helper  # ⚠️ Limited support
```

---

## 🧪 Testing

**84 tests passing**, including:
- 7 import resolver unit tests
- 5 cross-file integration tests
- All existing tests still pass

**Test Coverage:**
- Import resolution: ✅
- Alias handling: ✅
- Graceful fallback: ✅
- Disabled mode: ✅

---

## 🚀 Performance

**Optimizations:**
- AST caching (parse each file once)
- Lazy loading (only load when needed)
- Early termination (stop if imports can't resolve)

**Benchmarks:**
- Small projects (<10 files): Negligible overhead
- Medium projects (10-100 files): ~10-20% slower
- Large projects (100+ files): Not yet tested

---

## 📝 API

### Python API

```python
from flowslice import Slicer, SliceDirection

# Enable cross-file (default)
slicer = Slicer(root_path="/path/to/project")
result = slicer.slice("main.py", 42, "variable", SliceDirection.BOTH)

# Disable cross-file
slicer = Slicer(enable_cross_file=False)
```

### CLI

```bash
# Cross-file enabled by default
flowslice main.py:42:variable both

# Works across files automatically
flowslice main.py:10:data backward graph
```

---

## 🔜 Future Enhancements (Phase 2)

1. **Inter-Procedural Analysis**
   - Trace into function bodies
   - Track return values
   - Parameter-to-argument mapping

2. **Transitive Imports**
   - Follow imports of imports
   - Full dependency graph

3. **Advanced Import Forms**
   - Relative imports (`from ..utils import`)
   - Dynamic imports
   - Star imports (`from module import *`)

---

## 📖 See Also

- [README.md](README.md) - Main documentation
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) - Current limitations
- [REMAINING_WORK.md](REMAINING_WORK.md) - Phase 2 roadmap

---

**🎉 Cross-file analysis is now available! Try it today!**
