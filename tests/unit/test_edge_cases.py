"""Edge case tests for flowslice."""

import tempfile
from pathlib import Path

import pytest

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_slice_list_append(self):
        """Test slicing with list.append() method calls."""
        code = """
items = []
items.append(1)
items.append(2)
print(items)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 3, "items", SliceDirection.BACKWARD)

            # Should find the list initialization and append calls
            assert len(result.backward_slice) > 0
            assert any(node.operation == ".append()" for node in result.backward_slice)
        finally:
            Path(temp_path).unlink()

    def test_slice_multiple_assignments(self):
        """Test slicing with multiple assignments to same variable."""
        code = """
x = 1
x = 2
x = 3
print(x)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 4, "x", SliceDirection.BACKWARD)

            # Should find all assignments
            assert len(result.backward_slice) > 0
        finally:
            Path(temp_path).unlink()

    def test_slice_nested_function_call(self):
        """Test slicing with nested function calls."""
        code = """
def inner(x):
    return x * 2

def outer(y):
    return inner(y + 1)

result = outer(5)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 8, "result", SliceDirection.BACKWARD)

            assert len(result.backward_slice) > 0
            assert any("outer" in node.code for node in result.backward_slice)
        finally:
            Path(temp_path).unlink()

    def test_slice_with_for_loop(self):
        """Test slicing with for loop variable."""
        code = """
numbers = [1, 2, 3]
for num in numbers:
    print(num)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 3, "num", SliceDirection.BACKWARD)

            # Should find the for loop
            assert len(result.backward_slice) > 0
            assert any(node.operation == "for loop" for node in result.backward_slice)
        finally:
            Path(temp_path).unlink()

    def test_slice_empty_line(self):
        """Test slicing at a line with no code."""
        code = """
x = 10

y = 20
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            # Line 2 is empty - should handle gracefully
            result = slicer.slice(temp_path, 2, "x", SliceDirection.BACKWARD)

            # Should still work, just empty or minimal results
            assert result.target_line == 2
        finally:
            Path(temp_path).unlink()

    def test_slice_module_level_code(self):
        """Test slicing module-level (non-function) code."""
        code = """# Module level
x = 10
y = x + 5
z = y * 2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            # z is at line 4
            result = slicer.slice(temp_path, 4, "z", SliceDirection.BACKWARD)

            # Should track through module-level variables
            assert len(result.backward_slice) > 0
            functions = set(node.function for node in result.backward_slice)
            assert "<module>" in functions
        finally:
            Path(temp_path).unlink()

    def test_slice_variable_in_expression(self):
        """Test slicing a variable used in a complex expression."""
        code = """
a = 5
b = 10
c = 15
result = a + b * c - 3
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 5, "result", SliceDirection.BACKWARD)

            # Should find dependencies on a, b, c
            assert len(result.backward_slice) > 0
            all_deps = set()
            for node in result.backward_slice:
                all_deps.update(node.dependencies)
            # Should depend on at least some of a, b, c
            assert len(all_deps & {"a", "b", "c"}) > 0
        finally:
            Path(temp_path).unlink()

    def test_slice_with_comments(self):
        """Test that comments don't interfere with slicing."""
        code = """
# This is a comment
x = 10  # inline comment
# Another comment
y = x + 5  # more comments
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 5, "y", SliceDirection.BACKWARD)

            # Should work despite comments
            assert len(result.backward_slice) > 0
        finally:
            Path(temp_path).unlink()

    def test_slice_forward_print(self):
        """Test forward slicing to a print statement."""
        code = """
message = "Hello"
name = "World"
greeting = f"{message}, {name}!"
print(greeting)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 2, "message", SliceDirection.FORWARD)

            # Should trace forward to the print
            assert len(result.forward_slice) > 0
        finally:
            Path(temp_path).unlink()

    def test_slice_string_variable(self):
        """Test slicing with string literals."""
        code = """
name = "Alice"
greeting = "Hello, " + name
print(greeting)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            slicer = Slicer()
            result = slicer.slice(temp_path, 3, "greeting", SliceDirection.BACKWARD)

            # Should find the assignment with string concatenation
            assert len(result.backward_slice) > 0
            all_deps = set()
            for node in result.backward_slice:
                all_deps.update(node.dependencies)
            assert "name" in all_deps
        finally:
            Path(temp_path).unlink()
