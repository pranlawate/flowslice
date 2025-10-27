"""Unit tests for flowslice.core.slicer."""

import tempfile
from pathlib import Path

import pytest

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


class TestSlicer:
    """Test Slicer class."""

    def test_slicer_initialization(self):
        """Test Slicer can be initialized."""
        slicer = Slicer()
        assert slicer.root_path == Path(".")

    def test_slicer_with_custom_root(self):
        """Test Slicer with custom root path."""
        slicer = Slicer("/tmp")
        assert slicer.root_path == Path("/tmp")

    def test_slice_simple_assignment_backward(self):
        """Test backward slicing of a simple assignment."""
        code = """
x = 10
y = x + 5
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 3, "y", SliceDirection.BACKWARD)

            assert result.target_variable == "y"
            assert result.target_line == 3
            assert len(result.backward_slice) > 0
            # Should find the assignment y = x + 5
            assert any(node.variable == "y" for node in result.backward_slice)
        finally:
            Path(temp_path).unlink()

    def test_slice_simple_assignment_forward(self):
        """Test forward slicing of a simple assignment."""
        code = """
x = 10
y = x + 5
print(y)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 3, "y", SliceDirection.FORWARD)

            assert result.target_variable == "y"
            assert result.target_line == 3
            assert len(result.forward_slice) > 0
            # Should find print(y)
            assert any("print" in node.operation for node in result.forward_slice)
        finally:
            Path(temp_path).unlink()

    def test_slice_both_directions(self):
        """Test bidirectional slicing."""
        code = """
x = 10
y = x + 5
print(y)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 3, "y", SliceDirection.BOTH)

            assert result.target_variable == "y"
            assert len(result.backward_slice) > 0
            assert len(result.forward_slice) > 0
        finally:
            Path(temp_path).unlink()

    def test_slice_with_function(self):
        """Test slicing within a function."""
        code = """
def calculate(a, b):
    result = a + b
    return result

x = calculate(5, 10)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 3, "result", SliceDirection.BACKWARD)

            assert result.target_variable == "result"
            assert len(result.backward_slice) > 0
            # Should track that result depends on a and b
            assert any(node.variable == "result" for node in result.backward_slice)
        finally:
            Path(temp_path).unlink()

    def test_slice_nonexistent_file(self):
        """Test slicing a file that doesn't exist raises appropriate error."""
        slicer = Slicer()
        with pytest.raises(FileNotFoundError):
            slicer.slice("nonexistent_file.py", 1, "x", SliceDirection.BOTH)

    def test_result_filename_extraction(self):
        """Test that result contains just the filename, not full path."""
        code = "x = 10\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 1, "x", SliceDirection.BACKWARD)

            # Result should have just filename, not full path
            assert result.target_file == Path(temp_path).name
        finally:
            Path(temp_path).unlink()
