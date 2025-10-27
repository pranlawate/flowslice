"""Test cases for DAG (graph) visualization of dataflow."""

import tempfile
from pathlib import Path

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


def test_backward_slice_multiple_sources_converge():
    """Test backward slice when multiple variables converge to one.

    This creates a graph structure:
         x ──┐
         y ──┼──> result
         z ──┘
    """
    code = """
def main():
    x = get_x()
    y = get_y()
    z = get_z()
    result = calculate(x, y, z)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        slicer = Slicer()
        # Slice result at line 6
        result = slicer.slice(temp_path, 6, "result", SliceDirection.BACKWARD)

        print("\n=== BACKWARD SLICE: Multiple Sources Converging ===")
        print(f"Total nodes: {len(result.backward_slice)}")

        # Group by line to see the structure
        by_line = {}
        for node in result.backward_slice:
            if node.line not in by_line:
                by_line[node.line] = []
            by_line[node.line].append(node)

        for line in sorted(by_line.keys()):
            nodes = by_line[line]
            print(f"\nLine {line}: {nodes[0].code.strip()}")
            for node in nodes:
                print(f"  - var={node.variable}, op={node.operation}, deps={node.dependencies}")

        # The structure should show:
        # Line 6: result depends on [x, y, z]
        # Line 3: x (no deps)
        # Line 4: y (no deps)
        # Line 5: z (no deps)

        assert len(result.backward_slice) >= 4  # result + 3 sources

    finally:
        Path(temp_path).unlink()


def test_forward_slice_single_source_diverges():
    """Test forward slice when one variable diverges to multiple uses.

    This creates a graph structure:
                 ┌──> x
         data ───┼──> y
                 └──> z
    """
    code = """
def main():
    data = load_data()
    x = transform(data)
    y = analyze(data)
    z = export(data)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        slicer = Slicer()
        # Slice data at line 3
        result = slicer.slice(temp_path, 3, "data", SliceDirection.FORWARD)

        print("\n=== FORWARD SLICE: Single Source Diverging ===")
        print(f"Total nodes: {len(result.forward_slice)}")

        # Group by line
        by_line = {}
        for node in result.forward_slice:
            if node.line not in by_line:
                by_line[node.line] = []
            by_line[node.line].append(node)

        for line in sorted(by_line.keys()):
            nodes = by_line[line]
            print(f"\nLine {line}: {nodes[0].code.strip()}")
            for node in nodes:
                print(f"  - var={node.variable}, op={node.operation}, deps={node.dependencies}")

        # The structure should show:
        # Line 3: data is the source
        # Line 4: x derived from data
        # Line 5: y derived from data
        # Line 6: z derived from data
        # All three branch from the same source!

        forward_lines = {node.line for node in result.forward_slice}
        assert 4 in forward_lines  # x = transform(data)
        assert 5 in forward_lines  # y = analyze(data)
        assert 6 in forward_lines  # z = export(data)

    finally:
        Path(temp_path).unlink()


def test_complex_dag_diamond_pattern():
    """Test complex DAG with diamond pattern.

    This creates a diamond structure:
         x ──┐
             ├──> temp ──┐
         y ──┘           ├──> result
         z ──────────────┘
    """
    code = """
def main():
    x = get_x()
    y = get_y()
    z = get_z()
    temp = combine(x, y)
    result = finalize(temp, z)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        slicer = Slicer()
        # Slice result at line 7 (backward)
        result = slicer.slice(temp_path, 7, "result", SliceDirection.BACKWARD)

        print("\n=== BACKWARD SLICE: Diamond Pattern ===")
        print(f"Total nodes: {len(result.backward_slice)}")

        by_line = {}
        for node in result.backward_slice:
            if node.line not in by_line:
                by_line[node.line] = []
            by_line[node.line].append(node)

        for line in sorted(by_line.keys()):
            nodes = by_line[line]
            print(f"\nLine {line}: {nodes[0].code.strip()}")
            for node in nodes:
                print(f"  - var={node.variable}, op={node.operation}, deps={node.dependencies}")

        # Should trace:
        # result <- [temp, z]
        # temp <- [x, y]
        # So the full dependency graph is: x, y, z all contribute to result
        # but through different paths (x,y via temp; z directly)

    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    test_backward_slice_multiple_sources_converge()
    test_forward_slice_single_source_diverges()
    test_complex_dag_diamond_pattern()
