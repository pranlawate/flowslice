"""Unit tests for flowslice.formatters.json."""

import json

import pytest

from flowslice.core.models import SliceDirection, SliceNode, SliceResult
from flowslice.formatters.json import JSONFormatter


class TestJSONFormatter:
    """Test JSONFormatter class."""

    def test_format_empty_result(self):
        """Test formatting an empty SliceResult."""
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
        )
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BOTH)

        data = json.loads(output)
        assert data["target"]["file"] == "test.py"
        assert data["target"]["line"] == 42
        assert data["target"]["variable"] == "x"
        assert "backward_slice" not in data
        assert "forward_slice" not in data
        assert data["statistics"]["total_lines"] == 0

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
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        data = json.loads(output)
        assert "backward_slice" in data
        assert "forward_slice" not in data
        assert len(data["backward_slice"]) == 1
        assert data["backward_slice"][0]["line"] == 40
        assert data["backward_slice"][0]["code"] == "x = 10"

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
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.FORWARD)

        data = json.loads(output)
        assert "forward_slice" in data
        assert "backward_slice" not in data
        assert len(data["forward_slice"]) == 1
        assert data["forward_slice"][0]["line"] == 44
        assert data["forward_slice"][0]["operation"] == "passed to print()"

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
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BOTH)

        data = json.loads(output)
        assert "backward_slice" in data
        assert "forward_slice" in data
        assert len(data["backward_slice"]) == 1
        assert len(data["forward_slice"]) == 1

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
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        data = json.loads(output)
        assert "statistics" in data
        assert data["statistics"]["total_lines"] == 1
        assert "test.py" in data["statistics"]["files_involved"]
        assert "main" in data["statistics"]["functions_involved"]

    def test_format_includes_dependencies(self):
        """Test that dependencies are included in output."""
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
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        data = json.loads(output)
        assert "dependencies" in data["backward_slice"][0]
        assert data["backward_slice"][0]["dependencies"] == ["x", "y"]

    def test_format_includes_context(self):
        """Test that context is included when present."""
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
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        data = json.loads(output)
        assert "context" in data["backward_slice"][0]
        assert data["backward_slice"][0]["context"] == "iterates over items"

    def test_format_custom_indent(self):
        """Test formatting with custom indentation."""
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
        )
        formatter = JSONFormatter()
        output_indent_2 = formatter.format(result, SliceDirection.BOTH, indent=2)
        output_indent_4 = formatter.format(result, SliceDirection.BOTH, indent=4)

        # indent=4 should produce longer output
        assert len(output_indent_4) > len(output_indent_2)

    def test_format_is_valid_json(self):
        """Test that output is always valid JSON."""
        node = SliceNode(
            file="test.py",
            line=40,
            function="main",
            code='x = "hello"  # comment',
            variable="x",
            operation="assignment",
        )
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
            backward_slice=[node],
        )
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        # Should not raise an exception
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_format_multiple_files_and_functions(self):
        """Test statistics with multiple files and functions."""
        node1 = SliceNode(
            file="file1.py",
            line=10,
            function="helper",
            code="a = 1",
            variable="a",
            operation="assignment",
        )
        node2 = SliceNode(
            file="file2.py",
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
        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        data = json.loads(output)
        assert len(data["statistics"]["files_involved"]) == 2
        assert "file1.py" in data["statistics"]["files_involved"]
        assert "file2.py" in data["statistics"]["files_involved"]
        assert len(data["statistics"]["functions_involved"]) == 2
        assert "helper" in data["statistics"]["functions_involved"]
        assert "main" in data["statistics"]["functions_involved"]
