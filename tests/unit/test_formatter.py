"""Unit tests for flowslice.formatters.tree."""

import pytest

from flowslice.core.models import SliceDirection, SliceNode, SliceResult
from flowslice.formatters.tree import TreeFormatter


class TestTreeFormatter:
    """Test TreeFormatter class."""

    def test_format_empty_result(self):
        """Test formatting an empty SliceResult."""
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BOTH)

        assert "test.py:42" in output
        assert "x" in output
        assert "BIDIRECTIONAL SLICE" in output

    def test_format_backward_only(self):
        """Test formatting backward slice only."""
        node = SliceNode(
            file="test.py",
            line=40,
            function="main",
            code="x = 10",
            variable="x",
            operation="assignment",
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
            backward_slice=[node],
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        assert "⬅️  BACKWARD SLICE" in output
        assert "➡️  FORWARD SLICE" not in output
        assert "Line 40" in output
        assert "x = 10" in output

    def test_format_forward_only(self):
        """Test formatting forward slice only."""
        node = SliceNode(
            file="test.py",
            line=44,
            function="main",
            code="print(x)",
            variable="x",
            operation="passed to print()",
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
            forward_slice=[node],
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.FORWARD)

        assert "➡️  FORWARD SLICE" in output
        assert "⬅️  BACKWARD SLICE" not in output
        assert "Line 44" in output
        assert "print(x)" in output

    def test_format_both_directions(self):
        """Test formatting both backward and forward slices."""
        backward_node = SliceNode(
            file="test.py",
            line=40,
            function="main",
            code="x = 10",
            variable="x",
            operation="assignment",
        )
        forward_node = SliceNode(
            file="test.py",
            line=44,
            function="main",
            code="print(x)",
            variable="x",
            operation="passed to print()",
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
            backward_slice=[backward_node],
            forward_slice=[forward_node],
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BOTH)

        assert "⬅️  BACKWARD SLICE" in output
        assert "➡️  FORWARD SLICE" in output
        assert "Line 40" in output
        assert "Line 44" in output

    def test_format_includes_statistics(self):
        """Test that formatted output includes statistics."""
        node = SliceNode(
            file="test.py",
            line=40,
            function="main",
            code="x = 10",
            variable="x",
            operation="assignment",
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
            backward_slice=[node],
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        assert "📊 STATISTICS:" in output
        assert "Total lines in slice:" in output
        assert "Files involved:" in output
        assert "Functions involved:" in output

    def test_format_shows_dependencies(self):
        """Test that dependencies are shown in output."""
        node = SliceNode(
            file="test.py",
            line=40,
            function="main",
            code="z = x + y",
            variable="z",
            operation="assignment",
            dependencies=["x", "y"],
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="z",
            backward_slice=[node],
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        assert "depends on: x, y" in output

    def test_format_shows_context(self):
        """Test that context is shown in output when present."""
        node = SliceNode(
            file="test.py",
            line=40,
            function="main",
            code="for item in items:",
            variable="item",
            operation="for loop",
            context="iterates over items",
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="item",
            backward_slice=[node],
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        assert "iterates over items" in output

    def test_format_groups_by_function(self):
        """Test that nodes are grouped by function in output."""
        node1 = SliceNode(
            file="test.py",
            line=10,
            function="helper",
            code="a = 1",
            variable="a",
            operation="assignment",
        )
        node2 = SliceNode(
            file="test.py",
            line=20,
            function="main",
            code="b = 2",
            variable="b",
            operation="assignment",
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
            backward_slice=[node1, node2],
        )
        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        assert "📁 test.py → helper()" in output
        assert "📁 test.py → main()" in output
