# flowslice 🔬

[![Tests](https://github.com/pranlawate/flowslice/actions/workflows/tests.yml/badge.svg)](https://github.com/pranlawate/flowslice/actions/workflows/tests.yml)
[![Lint](https://github.com/pranlawate/flowslice/actions/workflows/lint.yml/badge.svg)](https://github.com/pranlawate/flowslice/actions/workflows/lint.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Dataflow Slicing for Python** - Trace where your variables come from and where they go!

## 🎯 What is flowslice?

flowslice is a static analysis tool that helps you understand dataflow in Python code. Given a variable at a specific line, it shows you:

- ⬅️ **Backward Slice**: Where did this value come from?
- ➡️ **Forward Slice**: Where does this value go?
- 📍 **Function Context**: Which functions are involved?
- 🔗 **Dependencies**: What other variables affect this?

## ⚡ Quick Start

```bash
# Install (development mode)
pip install -e .

# Run flowslice
flowslice <file>:<line>:<variable> [direction] [format]

# Examples
flowslice example.py:26:result both          # Default tree format
flowslice example.py:26:result backward graph  # Graph format (shows DAG structure)
flowslice example.py:26:result forward json    # JSON format (for tools)
```

### Output Formats

All formatters support **color-coded output** with cross-file indicators:
- 🔗 **Cross-file nodes** highlighted in magenta (bold)
- 📁 **Local nodes** shown in standard colors
- ⭐ **Target line** highlighted in yellow

- **tree** (default): Chronological tree view with inline cross-file nodes
- **graph**: Grouped DAG view showing convergence/divergence patterns
- **json**: Machine-readable JSON output for tool integration
- **dot**: Graphviz DOT format for graph visualization (pipe to `dot -Tpng > output.png`)

**Color Support:** Colors auto-disable when piping to files or when `NO_COLOR` env var is set.
```

## 📖 Example Output

```
╔══════════════════════════════════════════════════════════════════════╗
║  BIDIRECTIONAL SLICE: skipped @ main.py:1251                         ║
╚══════════════════════════════════════════════════════════════════════╝

⬅️  BACKWARD SLICE (How did we get here?)
────────────────────────────────────────────────────────────────────────

  📁 main.py → main()
    ├─ Line 1171: skipped: List[str] = []
    ├─ Line 1178: skipped.append(str(Path(file_name).resolve()))
    │  └─ depends on: file_name, Path, str
    └─ Line 1183: files.find(file_names, config, skipped, broken)
       └─ operation: passed to files.find()

  📁 files.py → find()
    ├─ Line 24: skipped.append(str(full_path))
    │  └─ depends on: full_path
    └─ Line 35: skipped.append(os.path.abspath(filepath))
       └─ depends on: filepath

➡️  FORWARD SLICE (Where does it go?)
────────────────────────────────────────────────────────────────────────

  📁 main.py → main()
    ├─ Line 1248: num_skipped += len(skipped)
    └─ Line 1251: for was_skipped in skipped:  ⭐ TARGET
       └─ Line 1253: print(f"{was_skipped} was skipped...")
```

## 🚀 Status

**Phase 1 COMPLETE** ✅ (v1.0-ready)

- ✅ Phase 0 Complete - Research & validation
- ✅ Package structure & refactoring
- ✅ **87 tests passing** (88% core coverage)
- ✅ Type-safe (mypy --strict passing)
- ✅ CLI working with 4 output formats (`flowslice` command)
- ✅ JSON, Tree, Graph, & DOT output formatters
- ✅ Derived variable tracking (intra-procedural)
- ✅ Function scope boundaries (no cross-function pollution)
- ✅ Multi-pass backward slicing (finds transitive dependencies)
- ✅ **Cross-file analysis - BOTH directions** (follows imports, traces dataflow through imported functions) 🆕
  - Backward slicing: traces where parameters come from across files
  - Forward slicing: tracks where parameters are used in imported functions
- ✅ **Package import support** (handles `__init__.py` re-exports) 🆕
- ✅ All major bugs fixed (Issues #1-6)
- 🎯 Next: Phase 2 - Nested function calls, inter-procedural analysis & control flow

See [ROADMAP.md](ROADMAP.md) for full plan and progress.

## 🎯 Use Cases

### 1. **Debugging**
```bash
# "Where does this variable come from?"
flowslice mycode.py:42:user_input backward
```

### 2. **Impact Analysis**
```bash
# "If I change this, what will be affected?"
flowslice mycode.py:10:config forward
```

### 3. **Code Review**
```bash
# "Show me the full dataflow"
flowslice mycode.py:100:result both
```

### 4. **Learning Codebases**
```bash
# Understand how data flows through unfamiliar code
flowslice framework.py:500:request both
```

## 🐍 Python API

flowslice can also be used as a library in your Python code:

```python
from flowslice import Slicer, SliceDirection, TreeFormatter, JSONFormatter, GraphFormatter

# Create a slicer
slicer = Slicer()

# Analyze a variable
result = slicer.slice("mycode.py", 42, "user_input", SliceDirection.BACKWARD)

# Format as tree (human-readable, default)
tree_formatter = TreeFormatter()
print(tree_formatter.format(result))

# Or format as graph (shows DAG structure - convergence/divergence)
graph_formatter = GraphFormatter()
print(graph_formatter.format(result, SliceDirection.BACKWARD))

# Or format as JSON (for tools)
json_formatter = JSONFormatter()
json_output = json_formatter.format(result, indent=2)
print(json_output)
```

**Output formats:**
- **Tree**: Chronological tree view with color-coded cross-file indicators
- **Graph**: Grouped DAG view showing convergence/divergence in dataflow
- **JSON**: Machine-readable for tool integration
- **DOT**: Graphviz format for graph visualization

**Visualization Features:**
- 🎨 Color-coded output (auto-disabled for pipes and `NO_COLOR`)
- 🔗 Cross-file nodes clearly marked and highlighted
- ⭐ Target line prominently displayed
- 📊 Inline chronological ordering for better flow understanding

## 📚 Documentation

- **[INDEX.md](INDEX.md)** - Documentation index and quick links
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - Limitations and workarounds (all critical bugs fixed!)
- **[ROADMAP.md](ROADMAP.md)** - Development phases and progress
- **[VISUALIZATION_OPTIONS.md](VISUALIZATION_OPTIONS.md)** - Choosing output formats
- **[COMPLEX_DATAFLOW_HANDLING.md](COMPLEX_DATAFLOW_HANDLING.md)** - DAG patterns and complex cases
- **[docs/phase0/](docs/phase0/)** - Phase 0 research (archived)

## 🛠️ How It Works

flowslice uses Python's built-in `ast` module to:

1. Parse the source code into an Abstract Syntax Tree
2. Track variable assignments (definitions)
3. Track variable uses (reads)
4. Build def-use chains (backward) and use-def chains (forward)
5. Format results with function names and context

### Derived Variable Tracking

flowslice doesn't just track a single variable name - it tracks **dataflow**. When a variable is used to create a new variable, the tool automatically tracks the derived variable too:

```python
file_path = "input.txt"                           # TARGET variable
detected_format = detect_file_format(file_path)   # derived variable
process(detected_format)                          # tracks this too!
```

**Forward slice from `file_path`** will show:
1. `file_path` passed to `detect_file_format()`
2. `detected_format` assigned from the function call
3. `detected_format` passed to `process()` ← **Automatically tracked!**

This works for chains too:
```python
x = 5
y = transform(x)      # y is derived from x
z = process(y)        # z is derived from y (and transitively from x)
result = finalize(z)  # result is derived from z
```

**Forward slice from `x`** includes the entire chain: `x → y → z → result`

**Note**: This is intra-procedural tracking (within the same function). Inter-procedural tracking (following dataflow into and out of function bodies) is planned for Phase 2.

## 🎓 Background

This project was born from a real need while debugging the [isort](https://github.com/PyCQA/isort) codebase. We needed to trace how the `skipped` list variable flowed through multiple files and functions. Manual tracing was tedious, so we built this tool!

**Phase 0 Research** validated that no existing tool provides this functionality. See [TOOL_COMPARISON.md](TOOL_COMPARISON.md) for details.

## 🗺️ Roadmap

- ✅ **Phase 0: Research** (COMPLETE)
  - Researched existing tools
  - Validated market gap
  - Chose name: flowslice

- 🚧 **Phase 1: Core Library** (IN PROGRESS - 60% complete)
  - ✅ Refactored POC into production library
  - ✅ 53 tests (88% coverage)
  - ✅ JSON & Tree formatters
  - ⏭️ Cross-file support (TODO)
  - ⏭️ Edge case handling (TODO)

- ⏳ **Phase 2: CLI Tool** (2-3 weeks)
- ⏳ **Phase 3: PyPI Publication** (1 week)
- ⏳ **Phase 4: VS Code Extension** (6-8 weeks)

See [ROADMAP.md](ROADMAP.md) for complete timeline.

## 🤝 Contributing

We're in **Phase 1 development** (~60% complete). Interested in contributing?

**Now**:
- Try the tool and provide feedback
- Report bugs or suggest features
- Help with cross-file analysis
- Write additional tests

**Soon (Phase 2-3)**:
- CLI enhancements
- Additional output formats
- PyPI package preparation

**Later (Phase 4)**:
- VS Code extension
- IDE integrations

See [ROADMAP.md](ROADMAP.md) for the complete plan.

## 📜 License

TBD (MIT or Apache 2.0 recommended)

## 🙏 Acknowledgments

- Built while fixing issue #2412 in the [isort](https://github.com/PyCQA/isort) project
- Inspired by the need for better dataflow understanding in large Python codebases

---

**Status**: Phase 0 Complete ✅ | Phase 1 Starting
**Last Updated**: 2025-10-27
**Package Name**: flowslice (PyPI: coming soon)
**Website**: flowslice.dev (coming soon)
