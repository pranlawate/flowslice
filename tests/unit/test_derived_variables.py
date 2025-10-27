"""Test forward slicing with derived variables from function calls."""

import tempfile
from pathlib import Path

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


def test_forward_slice_tracks_derived_variables():
    """Forward slice should track variables derived from function calls.

    When file_path is passed to a function and the result is assigned to
    detected_format, the forward slice should include uses of detected_format
    since it contains data derived from file_path.
    """
    code = """
def detect_file_format(path):
    return "json"

def process(fmt):
    print(fmt)

def main():
    file_path = "input.txt"
    detected_format = detect_file_format(file_path)
    process(detected_format)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        slicer = Slicer()
        # Slice file_path at line 9 (file_path = "input.txt")
        result = slicer.slice(temp_path, 9, "file_path", SliceDirection.FORWARD)

        # Extract line numbers and variables from forward slice
        forward_lines = {node.line for node in result.forward_slice}
        forward_vars = {node.variable for node in result.forward_slice}

        print(f"Forward slice lines: {sorted(forward_lines)}")
        print(f"Forward slice variables: {forward_vars}")
        print("\nForward slice nodes:")
        for node in result.forward_slice:
            print(f"  Line {node.line}: {node.code.strip()} (var={node.variable}, op={node.operation})")

        # Should include:
        # Line 10: detected_format = detect_file_format(file_path) - file_path passed
        assert 10 in forward_lines, "Should include line 10 where file_path is passed to function"

        # Line 11: process(detected_format) - derived variable used
        assert 11 in forward_lines, "Should include line 11 where detected_format (derived from file_path) is used"

        # Should track detected_format as a derived variable
        assert "detected_format" in forward_vars, "Should track detected_format as it's derived from file_path"

    finally:
        Path(temp_path).unlink()


def test_forward_slice_tracks_chained_derived_variables():
    """Forward slice should track chains of derived variables."""
    code = """
def main():
    x = 5
    y = transform(x)
    z = process(y)
    result = finalize(z)
    print(result)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        slicer = Slicer()
        # Slice x at line 3 (x = 5)
        result = slicer.slice(temp_path, 3, "x", SliceDirection.FORWARD)

        forward_lines = {node.line for node in result.forward_slice}
        forward_vars = {node.variable for node in result.forward_slice}

        print(f"\nChained forward slice lines: {sorted(forward_lines)}")
        print(f"Chained forward slice variables: {forward_vars}")

        # Should track the entire chain
        assert 4 in forward_lines, "Should include y = transform(x)"
        assert 5 in forward_lines, "Should include z = process(y)"
        assert 6 in forward_lines, "Should include result = finalize(z)"
        assert 7 in forward_lines, "Should include print(result)"

        assert "y" in forward_vars
        assert "z" in forward_vars
        assert "result" in forward_vars

    finally:
        Path(temp_path).unlink()
