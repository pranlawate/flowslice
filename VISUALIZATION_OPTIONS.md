# Dataflow Visualization Options

## Problem Statement

Dataflow is a **DAG (Directed Acyclic Graph)**, not a tree:
- **Backward slice**: Multiple sources converge to one variable
- **Forward slice**: One source diverges to multiple variables

Current tree view doesn't clearly show convergence/divergence.

---

## Option 1: Enhanced Tree View (ASCII Art DAG)

### Backward Slice (Convergence):
```
⬅️  BACKWARD SLICE (How did we get here?)

  📁 tmpfile.py → main()

    result = calculate(x, y, z) ⭐ TARGET (Line 6)
         ↑         ↑   ↑   ↑
         │         │   │   └─── z = get_z() (Line 5)
         │         │   └─────── y = get_y() (Line 4)
         │         └─────────── x = get_x() (Line 3)
         └─────────────────── calculate (external)
```

**Pros**:
- Shows convergence visually with arrows
- Clear dependencies
- Compact

**Cons**:
- Complex ASCII art for deep graphs
- May not scale well

---

## Option 2: Grouped by Dependencies

### Backward Slice:
```
⬅️  BACKWARD SLICE (How did we get here?)

  📁 tmpfile.py → main()

    🎯 TARGET: result (Line 6)
       └─ result = calculate(x, y, z)

    📥 DIRECT DEPENDENCIES (3):
       ├─ x (Line 3): x = get_x()
       ├─ y (Line 4): y = get_y()
       └─ z (Line 5): z = get_z()

    📦 EXTERNAL FUNCTIONS:
       └─ calculate
```

### Forward Slice (Divergence):
```
➡️  FORWARD SLICE (Where does it go?)

  📁 tmpfile.py → main()

    🎯 SOURCE: data (Line 3)
       └─ data = load_data()

    📤 DIRECT USES (3):
       ├─ Line 4: x = transform(data)
       ├─ Line 5: y = analyze(data)
       └─ Line 6: z = export(data)

    🌿 DERIVED VARIABLES (3):
       ├─ x → ... (further uses)
       ├─ y → ... (further uses)
       └─ z → ... (further uses)
```

**Pros**:
- Clearly separates direct deps from transitive
- Shows count of dependencies/uses
- Easy to scan

**Cons**:
- Loses line-by-line flow
- May be verbose for complex graphs

---

## Option 3: Graph Flow View

### Backward Slice:
```
⬅️  BACKWARD SLICE (How did we get here?)

  📁 tmpfile.py → main()

  [Line 3] x = get_x()
              ↓
  [Line 4] y = get_y()
              ↓
  [Line 5] z = get_z()
              ↓
           ╭──┴──╮
           │  ×  │  ← MERGE POINT
           ╰──┬──╯
              ↓
  [Line 6] result = calculate(x, y, z) ⭐ TARGET
           depends on: x, y, z
```

### Forward Slice:
```
➡️  FORWARD SLICE (Where does it go?)

  📁 tmpfile.py → main()

  [Line 3] data = load_data() 🎯 SOURCE
              ↓
           ╭──┴──╮
           │  ÷  │  ← SPLIT POINT (3 branches)
           ╰──┬──╯
              ↓
         ┌────┼────┐
         ↓    ↓    ↓
  [L4] x=   y=   z=
       │    │    │
       transform() analyze() export()
```

**Pros**:
- Most visual representation of graph structure
- Shows flow clearly
- Highlights merge/split points

**Cons**:
- Complex to render
- Takes vertical space
- Hard to align for complex graphs

---

## Option 4: Indented Dependency Tree (Current + Enhanced)

### Backward Slice:
```
⬅️  BACKWARD SLICE (How did we get here?)

  📁 tmpfile.py → main()

    Line 6: result = calculate(x, y, z) ⭐ TARGET
    │
    ├─── depends on x ───┐
    │    Line 3: x = get_x()
    │
    ├─── depends on y ───┤
    │    Line 4: y = get_y()
    │
    └─── depends on z ───┘
         Line 5: z = get_z()
```

**Pros**:
- Clean, readable
- Shows dependencies explicitly
- Easy to implement

**Cons**:
- Still tree-like, not true graph
- Repetitive for shared dependencies

---

## Option 5: Matrix/Table View

```
⬅️  BACKWARD SLICE (How did we get here?)

  LINE | CODE                         | DEPENDS ON      | CONTRIBUTES TO
  ──────────────────────────────────────────────────────────────────────
    3  | x = get_x()                  | get_x           | result
    4  | y = get_y()                  | get_y           | result
    5  | z = get_z()                  | get_z           | result
    6  | result = calculate(x,y,z) ⭐  | x, y, z, calc   | -
```

**Pros**:
- Compact
- Scannable
- Shows all relationships

**Cons**:
- Less visual
- Doesn't show graph structure intuitively
- Wide (may wrap in narrow terminals)

---

## Option 6: Hybrid: Tree + Dependency Annotations

### Current Enhanced:
```
⬅️  BACKWARD SLICE (How did we get here?)

  📁 tmpfile.py → main()

    ╔═══════════════════════════════════════╗
    ║ Line 6 ⭐ TARGET                      ║
    ║ result = calculate(x, y, z)          ║
    ╚═══════════════════════════════════════╝
         ↑ [x] ↑ [y] ↑ [z] ↑ [calculate]

    ┌─── Direct Dependencies (3) ───┐
    │                                │
    ├─ Line 3: x = get_x()          │
    │  Purpose: Input to calculate   │
    │                                │
    ├─ Line 4: y = get_y()          │
    │  Purpose: Input to calculate   │
    │                                │
    └─ Line 5: z = get_z()          │
       Purpose: Input to calculate   │
```

**Pros**:
- Clear target highlighting
- Shows purpose/relationship
- Good balance of visual and informative

**Cons**:
- Verbose
- May be too detailed

---

## Recommendation: Implement Multiple Formatters

### 1. **Default: Enhanced Grouped View** (Option 2)
   - Best for most use cases
   - Clear separation of concerns
   - Shows counts

### 2. **Compact: Current Tree** (existing)
   - For quick scans
   - Legacy compatibility

### 3. **Graph: Flow View** (Option 3)
   - For understanding complex DAGs
   - Visual learners
   - Add `--graph` flag

### 4. **Debug: Table View** (Option 5)
   - For programmatic analysis
   - Wide terminals
   - Add `--table` flag

---

## Implementation Plan

1. **Phase 1**: Enhance current tree formatter with dependency grouping (Option 2)
2. **Phase 2**: Add graph flow formatter (Option 3) with `--graph` flag
3. **Phase 3**: Add table formatter (Option 5) with `--table` flag

---

## User Feedback Needed

Which visualization do you prefer for:
1. Quick debugging?
2. Understanding complex dataflows?
3. Code review/documentation?
