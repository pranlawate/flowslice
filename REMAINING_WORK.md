# What's Remaining for flowslice

**Current Status**: Phase 1 ~85% complete
**Last Updated**: 2025-10-27

---

## ✅ What's DONE (Major Accomplishments)

### Core Functionality
- ✅ Intra-procedural backward slicing (with multi-pass for transitive deps)
- ✅ Intra-procedural forward slicing (with function scope boundaries)
- ✅ Derived variable tracking (follows dataflow chains)
- ✅ Three output formatters (tree, graph, json)
- ✅ CLI with format selection
- ✅ Python API
- ✅ 72 tests, 90% core coverage
- ✅ Type-safe (mypy --strict)
- ✅ All 6 critical bugs fixed

### Infrastructure
- ✅ Package structure (src/flowslice/)
- ✅ Installable via pip
- ✅ CLI entry point working
- ✅ Comprehensive documentation

---

## 🎯 Phase 1 Remaining (~15%)

### 1. Cross-File Analysis (HIGH PRIORITY)
**Status**: Not started
**Estimated**: 1-2 weeks
**Complexity**: Medium-High

**What it means:**
Follow variables across module imports

**Example:**
```python
# main.py
from utils import process_data
result = process_data(x)  # Need to trace into utils.py

# utils.py
def process_data(input):
    return transform(input)
```

**Tasks:**
- [ ] Parse import statements
- [ ] Load and analyze imported modules
- [ ] Track variable flow across file boundaries
- [ ] Handle circular imports
- [ ] Update formatters to show multi-file slices
- [ ] Write cross-file tests

**Blocker**: Need to decide scope - just direct imports, or transitive imports too?

---

### 2. Additional Edge Cases (MEDIUM PRIORITY)
**Status**: Partial coverage
**Estimated**: 1 week
**Complexity**: Low-Medium

**What's missing:**
- [ ] Walrus operator (`:=`)
- [ ] Lambda expressions (basic tracking)
- [ ] Match/case statements (Python 3.10+)
- [ ] Complex comprehensions with conditionals
- [ ] Class attribute tracking
- [ ] Global variables
- [ ] Exception handling (try/except variable flow)

**Tasks:**
- [ ] Add AST visitor methods for missing node types
- [ ] Write tests for each edge case
- [ ] Document limitations that won't be supported

---

### 3. Performance Optimization (LOW PRIORITY)
**Status**: Not started
**Estimated**: 1 week
**Complexity**: Medium

**Current issues:**
- Multi-pass backward slicing could be slow on large files
- No caching of parsed ASTs
- No incremental analysis

**Tasks:**
- [ ] Profile performance on large files (10k+ lines)
- [ ] Add AST caching
- [ ] Optimize multi-pass convergence detection
- [ ] Benchmark improvements

---

### 4. CI/CD Setup (LOW PRIORITY)
**Status**: Not started
**Estimated**: 2-3 days
**Complexity**: Low

**Tasks:**
- [ ] GitHub Actions workflow
- [ ] Run tests on push/PR
- [ ] Type checking (mypy)
- [ ] Linting (ruff)
- [ ] Coverage reporting
- [ ] Auto-publish to PyPI (on release)

---

### 5. Packaging & Distribution (LOW PRIORITY)
**Status**: Basic structure exists
**Estimated**: 1 week
**Complexity**: Low-Medium

**Tasks:**
- [ ] Finalize version numbering strategy
- [ ] Create proper CHANGELOG.md
- [ ] Publish to PyPI (test first, then prod)
- [ ] Setup readthedocs or similar for docs hosting
- [ ] Add badges to README (tests, coverage, PyPI version)

---

## 🚀 Phase 2: Advanced Features (Not Started)

### 1. Inter-Procedural Analysis (HIGHEST VALUE)
**Status**: Not started
**Estimated**: 3-4 weeks
**Complexity**: High

**What it means:**
Trace dataflow INTO and OUT OF function bodies

**Example:**
```python
def process(x):
    result = transform(x)  # Trace into transform()
    return result          # Track return back to caller

data = get_data()
output = process(data)     # Should show full flow: data -> x -> result -> output
```

**Tasks:**
- [ ] Build call graph
- [ ] Map function parameters to arguments
- [ ] Track return values
- [ ] Handle recursion
- [ ] Handle callbacks/lambdas
- [ ] Write extensive tests

**This is the BIG feature** - makes the tool truly powerful

---

### 2. Control Flow Tracking
**Status**: Not started
**Estimated**: 2-3 weeks
**Complexity**: High

**What it means:**
Track which branches execute based on conditions

**Example:**
```python
if mode == "fast":
    result = quick_process(x)
else:
    result = slow_process(x)

# Currently shows BOTH paths
# Goal: Show which path is possible based on mode value
```

**Tasks:**
- [ ] Track conditional expressions
- [ ] Path feasibility analysis
- [ ] Symbolic execution (basic)
- [ ] Show "this path when condition X"

---

### 3. Additional Formatters
**Status**: Partial (have 3, could add more)
**Estimated**: 1-2 weeks each
**Complexity**: Low-Medium

**Possible additions:**
- [ ] HTML formatter (interactive, collapsible)
- [ ] Graphviz/DOT formatter (visual graph)
- [ ] Markdown formatter (for docs/reports)
- [ ] CSV formatter (for data analysis)

---

## 📊 Priority Ranking

### Must-Have for v1.0 (Phase 1 completion)
1. **Cross-file analysis** - Critical for real-world use
2. **Edge cases** - Robustness
3. **CI/CD** - Quality assurance
4. **PyPI publishing** - Distribution

### Nice-to-Have for v1.0
5. **Performance optimization** - Only if issues arise
6. **Additional formatters** - HTML would be nice

### Future (v2.0)
7. **Inter-procedural analysis** - Game changer
8. **Control flow tracking** - Advanced feature

---

## 🤔 Open Questions / Decisions Needed

### Cross-File Analysis Scope
**Question**: How deep should we go?
- Option A: Only direct imports (one level)
- Option B: Transitive imports (full dependency tree)
- Option C: User-configurable depth

**Recommendation**: Start with A, add B later

### Performance Targets
**Question**: What's acceptable performance?
- Files < 1k lines: < 1 second?
- Files < 10k lines: < 5 seconds?
- Files > 10k lines: Best effort?

**Need**: Benchmark on real codebases

### Versioning Strategy
**Question**: When to release v1.0?
- Option A: After Phase 1 complete (cross-file analysis done)
- Option B: After current state (mark as v0.9, document limitations)
- Option C: After inter-procedural analysis (v2.0 feature as v1.0)

**Recommendation**: A (v1.0 = Phase 1 complete)

---

## 📅 Estimated Timeline

### If working full-time:
- **Phase 1 remaining**: 2-3 weeks
- **Phase 2 (inter-procedural)**: 3-4 weeks
- **Total to v1.0**: 2-3 weeks
- **Total to v2.0**: 5-7 weeks

### If working part-time (10 hrs/week):
- **Phase 1 remaining**: 1-2 months
- **Phase 2**: 2-3 months
- **Total to v1.0**: 1-2 months
- **Total to v2.0**: 3-5 months

---

## 🎯 Recommended Next Steps

### Immediate (This Week)
1. ✅ Fix remaining bugs - DONE!
2. ✅ Clean up documentation - DONE!
3. [ ] Decide on cross-file scope
4. [ ] Start cross-file analysis design

### Short-term (Next 2-4 Weeks)
1. [ ] Implement cross-file analysis
2. [ ] Add missing edge cases
3. [ ] Setup CI/CD
4. [ ] Publish to PyPI (test)

### Medium-term (1-2 Months)
1. [ ] Complete Phase 1
2. [ ] Release v1.0
3. [ ] Start Phase 2 planning
4. [ ] Begin inter-procedural analysis

---

**Bottom Line**: We're at ~85% of Phase 1. Main remaining work is **cross-file analysis** (the big piece), then cleanup for v1.0 release.
