# PySlice - Python Dataflow Analysis Tool 🔬

## 🎯 Vision

A comprehensive static analysis tool for Python that helps developers understand dataflow in their codebase. Given a variable at a specific line, PySlice traces both backwards (where did this value come from?) and forwards (where does this value go?), showing **function names, code context, and dependencies** - not just line numbers.

## 💡 Why This Matters

### Current Pain Points:
- ❌ Reading large codebases is hard
- ❌ Understanding "where does this value come from?" requires manual grepping
- ❌ Debugging data flow issues is time-consuming
- ❌ Code reviews miss subtle dataflow bugs
- ❌ Refactoring is risky without understanding impact

### PySlice Solution:
- ✅ **Instant dataflow understanding** - See the full picture in seconds
- ✅ **Bidirectional analysis** - Both forward and backward slicing
- ✅ **Function-aware** - Shows which functions are involved
- ✅ **Cross-file support** - Tracks data across module boundaries
- ✅ **Multiple interfaces** - CLI + VS Code extension

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PySlice Core Library                     │
│                   (Pure Python Package)                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  AST-Based Slicing Engine                          │   │
│  │  - Forward slicer (def → use)                      │   │
│  │  - Backward slicer (use → def)                     │   │
│  │  - Bidirectional slicer                            │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Type-Aware Analysis                               │   │
│  │  - Parse type annotations                          │   │
│  │  - Distinguish variables with same name            │   │
│  │  - Track type flow                                 │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Inter-Procedural Analysis                         │   │
│  │  - Track function calls                            │   │
│  │  - Handle pass-by-reference                        │   │
│  │  - Cross-module dataflow                           │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Output Formatters                                 │   │
│  │  - Tree view (console)                             │   │
│  │  - JSON (for tooling)                              │   │
│  │  - HTML (interactive visualization)                │   │
│  │  - Graph (DOT/Graphviz)                            │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────┬───────────────────────┬────────────────┘
                   │                        │
         ┌─────────▼─────────┐    ┌────────▼──────────┐
         │   CLI Interface    │    │  VS Code Extension │
         │   $ flowslice        │    │  (Language Server) │
         │                    │    │                    │
         │  - Simple syntax   │    │  - Hover tooltips  │
         │  - Colored output  │    │  - Click to jump   │
         │  - Export options  │    │  - Inline visuals  │
         └────────────────────┘    └────────────────────┘
```

## 🚀 Features

### Core Features (v1.0)

#### 1. **Backward Slicing** (Use → Def)
```bash
$ flowslice backward main.py:1251:skipped
```

Shows:
- Where the variable was defined
- All assignments that contributed to this value
- Function parameters that flow into this variable
- Dependencies on other variables

#### 2. **Forward Slicing** (Def → Use)
```bash
$ flowslice forward main.py:1171:skipped
```

Shows:
- All uses of this variable
- Functions it's passed to
- Computations that depend on it
- Output/side effects caused by it

#### 3. **Bidirectional Slicing**
```bash
$ flowslice both main.py:1251:skipped
```

Shows complete dataflow picture (both directions).

#### 4. **Function-Aware Output**
Every slice node shows:
- **File name**
- **Line number**
- **Function name** ← KEY DIFFERENTIATOR!
- **Code snippet**
- **Variable dependencies**
- **Context** (loop, conditional, etc.)

Example output:
```
📁 main.py → main()
  ├─ Line 1171: skipped: List[str] = []
  ├─ Line 1178: skipped.append(str(Path(file_name).resolve()))
  │  └─ depends on: file_name, Path, str
  │  └─ context: if config.filter_files
  └─ Line 1183: files.find(file_names, config, skipped, broken)
     └─ operation: passed to files.find()
     └─ cross-file: flows to files.py:9

📁 files.py → find()
  ├─ Line 9: def find(..., skipped: List[str], ...)
  │  └─ parameter (passed by reference)
  ├─ Line 24: skipped.append(str(full_path))
  │  └─ depends on: full_path
  └─ Line 35: skipped.append(os.path.abspath(filepath))
     └─ depends on: filepath
```

### Advanced Features (v2.0+)

- **Type-aware slicing** - Distinguish `skipped: bool` from `skipped: List[str]`
- **Alias analysis** - Track when variables point to same object
- **Control flow analysis** - Show conditional dependencies
- **Visualization** - Interactive HTML graphs
- **CI/CD integration** - Automated dataflow checks
- **Caching** - Fast re-analysis of large codebases

## 🎨 User Interfaces

### 1. CLI Tool

```bash
# Installation
$ pip install flowslice

# Basic usage
$ flowslice backward main.py:1251:skipped
$ flowslice forward main.py:1171:skipped
$ flowslice both main.py:1251:skipped

# With visualization
$ flowslice both main.py:1251:skipped --visualize --output slice.html

# Export as JSON
$ flowslice both main.py:1251:skipped --format json > slice.json

# Cross-project slicing
$ flowslice both main.py:1251:skipped --project-root ./

# Filter by function
$ flowslice both main.py:1251:skipped --function main
```

### 2. VS Code Extension

#### Installation:
```
Extensions → Search "PySlice"
```

#### Features:
1. **Right-click context menu**
   - Right-click variable → "PySlice: Show Dataflow"

2. **Hover tooltips**
   - Hover over variable → See quick slice summary

3. **Inline annotations**
   - Show "↑ 3 sources" and "↓ 5 uses" next to variables

4. **Interactive navigation**
   - Click on slice nodes to jump to definition/usage

5. **Gutter decorations**
   - Visual indicators for variables in current slice

6. **Command palette**
   ```
   Cmd/Ctrl+Shift+P → "PySlice: Analyze Variable"
   ```

## 📦 API Design

### Python API

```python
from flowslice import Slicer, SliceDirection

# Initialize
slicer = Slicer(project_root='./myproject')

# Backward slice
result = slicer.slice(
    file='main.py',
    line=1251,
    variable='skipped',
    direction=SliceDirection.BACKWARD
)

# Access results
print(f"Found {len(result.nodes)} nodes in slice")
for node in result.nodes:
    print(f"{node.file}:{node.line} in {node.function}() - {node.code}")

# Export
result.to_json('slice.json')
result.to_html('slice.html')
result.to_dot('slice.dot')  # Graphviz

# Pretty print
print(result.as_tree())
```

### Language Server Protocol (LSP)

For VS Code integration:
```typescript
// Request: textDocument/dataflow
{
  textDocument: { uri: "file:///path/to/main.py" },
  position: { line: 1250, character: 15 },  // on "skipped"
  direction: "both"
}

// Response: DataflowResult
{
  variable: "skipped",
  nodes: [
    {
      file: "main.py",
      line: 1171,
      function: "main",
      code: "skipped: List[str] = []",
      type: "definition"
    },
    // ... more nodes
  ]
}
```

## 🛣️ Development Roadmap

### Phase 1: Core Library (4-6 weeks)
- [ ] Enhanced AST-based backward slicer
- [ ] Enhanced AST-based forward slicer
- [ ] Function context tracking
- [ ] Basic cross-file support
- [ ] Output formatters (tree, JSON)
- [ ] Unit tests (>80% coverage)
- [ ] Documentation

### Phase 2: CLI Tool (2-3 weeks)
- [ ] Command-line interface
- [ ] Colored terminal output
- [ ] Export to multiple formats
- [ ] Configuration file support
- [ ] Performance optimization
- [ ] Integration tests

### Phase 3: Advanced Analysis (4-6 weeks)
- [ ] Type-aware slicing
- [ ] Alias analysis
- [ ] Control flow analysis
- [ ] Inter-procedural analysis
- [ ] Call graph integration
- [ ] Performance benchmarks

### Phase 4: VS Code Extension (6-8 weeks)
- [ ] Language server implementation
- [ ] Extension scaffolding
- [ ] Hover provider
- [ ] Command integration
- [ ] Inline decorations
- [ ] Interactive visualization
- [ ] Marketplace publication

### Phase 5: Polish & Release (2-3 weeks)
- [ ] Beta testing
- [ ] Performance tuning
- [ ] Documentation website
- [ ] Video tutorials
- [ ] Blog post / announcement
- [ ] PyPI publication

## 📊 Success Metrics

### Technical Metrics:
- ✅ Analyzes 10k+ line codebase in <5 seconds
- ✅ >90% accuracy on test suite
- ✅ Handles top 100 PyPI packages
- ✅ <100MB memory footprint

### User Metrics:
- 🎯 1000+ GitHub stars in first 6 months
- 🎯 10k+ pip installs/month
- 🎯 Featured on Python Weekly
- 🎯 5+ contributor community

## 🤝 Target Users

1. **Python Developers** debugging complex dataflow
2. **Code Reviewers** understanding impact of changes
3. **Security Researchers** tracking tainted data
4. **Educators** teaching program analysis
5. **Refactoring Teams** ensuring safe transformations

## 💻 Tech Stack

- **Language**: Python 3.9+
- **AST**: Built-in `ast` module
- **CLI**: `click` or `typer`
- **Visualization**: `graphviz`, HTML/JavaScript
- **VS Code**: TypeScript + LSP
- **Testing**: `pytest`
- **Type Checking**: `mypy`
- **Packaging**: `poetry` or `hatch`

## 🔧 Implementation Priorities

### Must Have (MVP):
1. ✅ Backward slicing with function names
2. ✅ Forward slicing with function names
3. ✅ CLI interface
4. ✅ Tree-based output

### Should Have:
5. Cross-file analysis
6. Type awareness
7. HTML visualization
8. VS Code extension

### Nice to Have:
9. Graph visualization
10. Caching
11. CI/CD integration
12. Jupyter notebook support

## 🎓 Learning Resources

For implementation:
- "Program Slicing" - Mark Weiser (original paper)
- "The Program Dependence Graph" - Ferrante et al.
- Python AST documentation
- LSP specification
- VS Code extension API

## 🚦 Next Steps

### Immediate Actions:
1. ✅ Create proof-of-concept (DONE!)
2. [ ] Set up GitHub repository
3. [ ] Choose project name (PySlice? DataFlowPy? SliceTrace?)
4. [ ] Create project structure
5. [ ] Write initial tests
6. [ ] Start core library development

### Questions to Decide:
- **Name**: PySlice, DataFlowPy, SliceTrace, or?
- **License**: MIT, Apache 2.0, or?
- **Hosting**: GitHub? GitLab?
- **Package manager**: poetry, hatch, setuptools?
- **Solo or team**: Looking for co-maintainers?

## 📝 Conclusion

**PySlice has the potential to become an essential tool in every Python developer's toolkit.** The proof-of-concept works, the architecture is sound, and the need is real.

With focused development over ~4-6 months, we can ship a production-ready tool that:
- Saves developers hours of manual code tracing
- Prevents bugs through better code understanding
- Makes code reviews more thorough
- Helps onboard new developers faster

**Ready to build this? Let's start!** 🚀

---

**Created by**: Your team
**Date**: 2025-10-02
**Status**: Proof-of-Concept Complete ✅
