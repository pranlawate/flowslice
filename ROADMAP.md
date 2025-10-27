# flowslice Development Roadmap

## 🎯 Vision

Create the best Python dataflow analysis tool that helps developers understand variable flow through their codebase - showing not just line numbers, but function names, dependencies, and complete dataflow chains.

## 📍 Current Status: Phase 1 IN PROGRESS 🚧 (40% complete)

**Completed:**
- ✅ **Phase 0 COMPLETE** - Research, naming, validation
- ✅ Package structure (src/flowslice/)
- ✅ Core library refactored from POC
- ✅ Type hints (passes mypy --strict)
- ✅ 25 unit tests (66% coverage)
- ✅ CLI working (`flowslice` command)
- ✅ Installable (`pip install -e .`)

**Next Up:**
- 🎯 Increase test coverage to >80%
- 🎯 Add cross-file analysis
- 🎯 Additional formatters (JSON, HTML)

## 🔍 Phase 0: Research & Validation ✅ COMPLETE

**Completed**: 2025-10-27 | **[Full details →](PHASE0_COMPLETE.md)**

**Summary**:
- ✅ Evaluated 7 tool categories - **no competition found**
- ✅ Tested 300+ package names
- ✅ Chose final name: **flowslice**
- ✅ GO decision: Build the tool

<details>
<summary>View Phase 0 details (click to expand)</summary>

- Evaluated: pyan3, code2flow, Semgrep, astroid, PyCharm, VS Code
- Result: **No existing tool does variable-level dataflow slicing**
- Name research: Tested 300+ names, all taken
- Final name: **flowslice** (available on PyPI, GitHub, flowslice.dev)
- See [TOOL_COMPARISON.md](TOOL_COMPARISON.md) and [NAMING_FINAL.md](NAMING_FINAL.md)

</details>

---

## 🏗️ Phase 1: Core Library 🚧 IN PROGRESS (~40% complete)

**Started**: 2025-10-27 | **Est. completion**: 2-3 weeks

**Progress**: Week 1-2 tasks complete, Week 3-6 remaining

### 1.1 Project Setup ✅ COMPLETE
- ✅ Name chosen: flowslice
- ✅ Package structure created (src/flowslice/)
- ✅ pyproject.toml configured
  ```
  flowslice/
  ├── pyproject.toml
  ├── README.md
  ├── LICENSE
  ├── src/
  │   └── flowslice/
  │       ├── __init__.py
  │       ├── core/
  │       │   ├── backward_slicer.py
  │       │   ├── forward_slicer.py
  │       │   └── analyzer.py
  │       ├── formatters/
  │       │   ├── tree.py
  │       │   ├── json.py
  │       │   └── html.py
  │       └── cli.py
  ├── tests/
  │   ├── test_backward.py
  │   ├── test_forward.py
  │   └── test_integration.py
  └── docs/
  ```
- [ ] Set up CI/CD (GitHub Actions)
- [ ] Configure linting (ruff, mypy)
- [ ] Set up testing (pytest)

### 1.2 Refactor POC into Library
- [ ] Extract backward slicer into module
- [ ] Extract forward slicer into module
- [ ] Create clean API
  ```python
  from flowslice import Slicer

  slicer = Slicer('myproject/')
  result = slicer.slice('main.py', 42, 'var', direction='both')
  print(result.as_tree())
  ```
- [ ] Add comprehensive type hints
- [ ] Write docstrings

### 1.3 Improve Accuracy
- [ ] **Type-aware analysis**
  - Parse type annotations
  - Distinguish `skipped: bool` from `skipped: List[str]`
  - Reduce false positives

- [ ] **Alias analysis**
  - Track when variables point to same object
  - Handle list/dict mutations
  - Track function parameters (pass-by-reference)

- [ ] **Control flow analysis**
  - Track conditional dependencies (if/else)
  - Handle loops properly
  - Track context (inside function, class, etc.)

### 1.4 Cross-File Support
- [ ] Parse import statements
- [ ] Track function calls across modules
- [ ] Follow variable flow across files
- [ ] Handle circular imports gracefully

### 1.5 Testing
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests on real code
- [ ] Test on top 10 PyPI packages
- [ ] Performance benchmarks
- [ ] Edge case testing

**Deliverable**: Python library installable via pip

---

## 🖥️ Phase 2: CLI Tool (2-3 weeks)

### 2.1 Production CLI
- [ ] Use `click` or `typer` for interface
- [ ] Support all output formats
  ```bash
  flowslice backward main.py:42:var
  flowslice forward main.py:42:var --format json
  flowslice both main.py:42:var --output slice.html
  ```
- [ ] Configuration file support (.flowslice.toml)
- [ ] Colored output
- [ ] Progress indicators for large files
- [ ] Error handling and helpful messages

### 2.2 Output Formats
- [ ] Tree (terminal - already have POC)
- [ ] JSON (for tooling integration)
- [ ] HTML (interactive visualization)
- [ ] DOT/Graphviz (for graph visualization)
- [ ] Markdown (for documentation)

### 2.3 Performance
- [ ] Caching analysis results
- [ ] Incremental analysis
- [ ] Parallel processing for large codebases
- [ ] Progress bars for long operations

### 2.4 Documentation
- [ ] User guide
- [ ] API reference
- [ ] Examples and tutorials
- [ ] Video demo
- [ ] Blog post announcement

**Deliverable**: Professional CLI tool with docs

---

## 📦 Phase 3: PyPI Publication (1 week)

### 3.1 Package Preparation
- [ ] Final name verification
- [ ] License selection (MIT recommended)
- [ ] README polish
- [ ] CHANGELOG.md
- [ ] CONTRIBUTING.md
- [ ] Code of conduct

### 3.2 Publishing
- [ ] Test PyPI upload
- [ ] Production PyPI upload
- [ ] GitHub release with binaries
- [ ] Documentation website (ReadTheDocs or GitHub Pages)

### 3.3 Announcement
- [ ] Post on Reddit r/Python
- [ ] Post on Hacker News
- [ ] Tweet/social media
- [ ] Python Weekly submission
- [ ] Blog post with use cases

**Deliverable**: `pip install flowslice` works!

---

## 🎨 Phase 4: VS Code Extension (6-8 weeks)

### 4.1 LSP Server
- [ ] Language Server Protocol implementation
- [ ] Use PySlice library as backend
- [ ] Handle workspace/file changes
- [ ] Caching for performance

### 4.2 Extension Features
- [ ] **Hover tooltips**
  - Show quick slice summary on hover
  - "↑ Defined at line X"
  - "↓ Used in lines Y, Z"

- [ ] **Context menu**
  - Right-click → "PySlice: Show Dataflow"
  - Shows full slice in panel

- [ ] **Inline decorations**
  - Show "↑ 3 sources" next to variables
  - Show "↓ 5 uses" next to definitions
  - Color-code by type (def/use)

- [ ] **Interactive panel**
  - Tree view of slice
  - Click to jump to line
  - Filter by function/file
  - Export options

- [ ] **Commands**
  - "PySlice: Analyze Variable"
  - "PySlice: Show Backward Slice"
  - "PySlice: Show Forward Slice"
  - "PySlice: Export Slice"

### 4.3 Publishing
- [ ] VS Code Marketplace submission
- [ ] Extension documentation
- [ ] Demo GIF/video
- [ ] README for extension

**Deliverable**: VS Code extension in marketplace

---

## 🚀 Phase 5: Advanced Features (Future)

### 5.1 Taint Analysis
- Track untrusted input through code
- Security vulnerability detection
- Sanitization verification

### 5.2 Integration
- [ ] pytest plugin (analyze test coverage dataflow)
- [ ] mypy plugin (enhance type checking)
- [ ] pre-commit hook (check dataflow changes)
- [ ] CI/CD integration (GitHub Actions)

### 5.3 Visualization
- [ ] Interactive HTML graphs
- [ ] D3.js dataflow diagrams
- [ ] Export to Mermaid diagrams
- [ ] Jupyter notebook widgets

### 5.4 Multi-Language
- [ ] JavaScript/TypeScript support
- [ ] Go support
- [ ] Rust support
- [ ] Generic AST-based approach

**Deliverable**: Feature-complete platform

---

## ⏱️ Timeline Summary

```
Phase 0: Research         → 2 weeks   (CRITICAL: Do this first!)
Phase 1: Core Library     → 6 weeks
Phase 2: CLI Tool         → 3 weeks
Phase 3: PyPI Publishing  → 1 week
────────────────────────────────────
         Total MVP        → 12 weeks (3 months)

Phase 4: VS Code Ext      → 8 weeks
Phase 5: Advanced         → Ongoing
```

---

## 🎯 Success Milestones

### Month 1:
- ✅ Research complete
- ✅ Name chosen
- ✅ Core library working
- ✅ 50+ unit tests passing

### Month 2:
- ✅ CLI tool complete
- ✅ Documentation published
- ✅ Beta tested by 10 users

### Month 3:
- ✅ Published on PyPI
- ✅ 100+ GitHub stars
- ✅ Featured on Python Weekly

### Month 6:
- ✅ 1000+ stars
- ✅ 10k+ downloads
- ✅ VS Code extension published
- ✅ 3+ major projects using it

### Year 1:
- ✅ 5k+ stars
- ✅ 50k+ downloads
- ✅ 10+ contributors
- ✅ Profitable (if pursuing commercial)

---

## 🚦 Decision Points

### After Phase 0 Research:

**GO Decision**: Proceed to Phase 1 if:
- ✅ No existing tool solves this problem well
- ✅ Positive feedback from user research
- ✅ Clear differentiation from competitors
- ✅ Available name secured

**NO-GO Decision**: Stop or pivot if:
- ❌ Existing tool is good enough
- ❌ No user demand
- ❌ Better to contribute to existing project
- ❌ Too competitive

### After Phase 3 (MVP Published):

**Accelerate**: Move to Phase 4 if:
- ✅ 1000+ stars in first month
- ✅ 5000+ downloads in first month
- ✅ Strong community feedback
- ✅ Low bug rate

**Pause**: Improve core if:
- ⚠️ High bug rate
- ⚠️ Poor performance
- ⚠️ Confusing UX
- ⚠️ Lukewarm reception

---

## 📊 Metrics to Track

### Technical:
- Lines of code
- Test coverage %
- Performance (time to analyze 10k LOC)
- Memory usage
- Bug count
- Documentation coverage

### User:
- GitHub stars
- PyPI downloads/month
- VS Code extension installs
- Issues opened/closed
- Contributors
- Community engagement

### Business (if applicable):
- Sponsors/donations
- Premium subscriptions
- Enterprise customers
- Revenue

---

## 🤝 Collaboration

### Looking for:
- **Core contributors** - Help build the library
- **Beta testers** - Try it and give feedback
- **Documentation** - Improve docs and examples
- **Integrations** - Build plugins/extensions

### How to contribute:
1. Read CONTEXT.md
2. Try the POC
3. Open an issue or discussion
4. Submit PRs

---

## 📝 Notes

### Principles:
1. **User-first**: Build what developers actually need
2. **Simple**: Easy to install and use
3. **Fast**: Subsecond analysis for most files
4. **Accurate**: Minimize false positives
5. **Beautiful**: Great UX matters

### Non-Goals:
- Not a full IDE (use existing IDEs)
- Not a profiler (use py-spy)
- Not a debugger (use pdb)
- Not symbolic execution (too complex)

### Inspiration:
- `grep` - Simple, fast, ubiquitous
- `rg` (ripgrep) - Modern, beautiful, fast
- `fzf` - Great UX for CLI tools
- PyCharm's "Find Usages" - But for CLI

---

**Ready to start? Begin with Phase 0! 🚀**

Last Updated: 2025-10-03
Status: Roadmap Complete, Awaiting Phase 0 Research
