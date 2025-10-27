"""Test for the args pollution bug where unrelated args usages appear in slice."""

import tempfile
from pathlib import Path

import pytest

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


class TestArgsPollutionBug:
    """Test the bug where unrelated args.* accesses pollute the backward slice."""

    def test_args_pollution_simple(self):
        """Test that only relevant args attributes are tracked."""
        code = """
def main(args):
    # Line 3: file_path uses args.file
    file_path = args.file

    # Line 6: Unrelated usage of args.process - should NOT appear in file_path slice
    process_name = args.process

    # Line 9: Another unrelated usage - should NOT appear
    output_format = args.format

    # Line 12: This uses file_path - should appear in forward slice
    print(file_path)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 4, "file_path", SliceDirection.BACKWARD)

            # Should find args.file dependency
            assert len(result.backward_slice) > 0

            # Get all the code lines in the slice
            slice_code = [node.code.strip() for node in result.backward_slice]

            # Should include the assignment: file_path = args.file
            assert any("file_path = args.file" in code for code in slice_code)

            # Should NOT include unrelated args usages
            assert not any("args.process" in code for code in slice_code), \
                "Backward slice should not include unrelated args.process"
            assert not any("args.format" in code for code in slice_code), \
                "Backward slice should not include unrelated args.format"

        finally:
            Path(temp_path).unlink()

    def test_multiple_reassignments_same_var(self):
        """Test tracking through multiple reassignments of the same variable."""
        code = """
def main(args):
    # First assignment
    file_path = args.file

    # Unrelated stuff
    x = args.other
    y = args.another

    # Reassignment of file_path
    if not file_path:
        file_path = args.default_file

    # Use file_path
    print(file_path)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 14, "file_path", SliceDirection.BACKWARD)

            slice_code = [node.code.strip() for node in result.backward_slice]

            # Should include both assignments to file_path
            assert any("file_path = args.file" in code for code in slice_code)
            assert any("file_path = args.default_file" in code for code in slice_code)

            # Should NOT include unrelated args
            assert not any("args.other" in code for code in slice_code)
            assert not any("args.another" in code for code in slice_code)

        finally:
            Path(temp_path).unlink()
