"""Test for forward slice pollution - including unrelated functions."""

import tempfile
from pathlib import Path

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


def test_forward_slice_should_not_include_unrelated_functions():
    """Test that forward slice doesn't include unrelated functions that happen after target."""
    code = """
def main():
    file_path = "input.txt"  # Line 3 - TARGET
    process(file_path)       # Line 4 - Should be in forward slice
    print("Done")            # Line 5 - NOT using file_path, should not be in slice

# These functions are defined after main() but NOT called from main()
# They should NOT appear in forward slice of file_path from main()
def display_all_content():
    file_path = "different.txt"  # Line 10 - Different variable, different scope
    print(file_path)             # Line 11 - Should NOT be in forward slice from main()

def display_pager():
    file_path = "another.txt"    # Line 14 - Different variable, different scope
    show(file_path)              # Line 15 - Should NOT be in forward slice from main()
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = f.name

    try:
        slicer = Slicer()
        result = slicer.slice(temp_path, 3, "file_path", SliceDirection.FORWARD)

        print("\n=== FORWARD SLICE RESULTS ===")
        for node in result.forward_slice:
            print(f"Line {node.line} in {node.function}: {node.code.strip()}")

        # Get all functions that appear in the forward slice
        functions_in_slice = set(node.function for node in result.forward_slice)

        print(f"\nFunctions in forward slice: {functions_in_slice}")

        # Forward slice should ONLY include nodes from main() function
        # because that's where the target line is
        assert "main" in functions_in_slice, "Should include main function"

        # These functions are defined later but NOT called from main
        # They should NOT be in the forward slice
        assert "display_all_content" not in functions_in_slice, \
            "Should NOT include display_all_content - it's a different function scope"
        assert "display_pager" not in functions_in_slice, \
            "Should NOT include display_pager - it's a different function scope"

    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    test_forward_slice_should_not_include_unrelated_functions()
