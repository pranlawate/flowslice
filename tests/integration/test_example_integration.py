"""Integration tests using the example.py file."""

from pathlib import Path

import pytest

from flowslice import JSONFormatter, Slicer, SliceDirection, TreeFormatter


class TestExampleIntegration:
    """Integration tests with example.py."""

    @pytest.fixture
    def example_file(self):
        """Path to example.py file."""
        path = Path("example.py")
        if not path.exists():
            pytest.skip("example.py not found")
        return str(path)

    def test_slice_result_variable_backward(self, example_file):
        """Test backward slicing of 'result' variable in example.py."""
        slicer = Slicer()
        result = slicer.slice(example_file, 26, "result", SliceDirection.BACKWARD)

        assert result.target_variable == "result"
        assert result.target_line == 26
        assert len(result.backward_slice) > 0

        # Should find the assignment
        assert any(node.variable == "result" for node in result.backward_slice)

    def test_slice_final_price_forward(self, example_file):
        """Test forward slicing of 'final_price' variable in example.py."""
        slicer = Slicer()
        result = slicer.slice(example_file, 37, "final_price", SliceDirection.FORWARD)

        assert result.target_variable == "final_price"
        assert result.target_line == 37
        assert len(result.forward_slice) > 0

        # Should find usage in print statement
        assert any("print" in node.operation for node in result.forward_slice)

    def test_slice_both_directions(self, example_file):
        """Test bidirectional slicing in example.py."""
        slicer = Slicer()
        # Use line 25 (subtotal) which has both backward and forward dataflow
        result = slicer.slice(example_file, 25, "subtotal", SliceDirection.BOTH)

        assert len(result.backward_slice) > 0
        assert len(result.forward_slice) > 0

    def test_tree_formatter_with_real_code(self, example_file):
        """Test TreeFormatter with real code."""
        slicer = Slicer()
        result = slicer.slice(example_file, 26, "result", SliceDirection.BACKWARD)

        formatter = TreeFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        assert "BACKWARD SLICE" in output
        assert "result" in output
        assert "example.py" in output
        assert "📊 STATISTICS:" in output

    def test_json_formatter_with_real_code(self, example_file):
        """Test JSONFormatter with real code."""
        slicer = Slicer()
        result = slicer.slice(example_file, 26, "result", SliceDirection.BACKWARD)

        formatter = JSONFormatter()
        output = formatter.format(result, SliceDirection.BACKWARD)

        # Should be valid JSON
        import json

        data = json.loads(output)
        assert data["target"]["variable"] == "result"
        assert data["target"]["line"] == 26
        assert "backward_slice" in data
        assert len(data["backward_slice"]) > 0

    def test_function_tracking(self, example_file):
        """Test that function names are correctly tracked."""
        slicer = Slicer()
        result = slicer.slice(example_file, 26, "result", SliceDirection.BACKWARD)

        # Should track process_order function
        functions = set(node.function for node in result.backward_slice)
        assert "process_order" in functions

    def test_dependency_tracking(self, example_file):
        """Test that dependencies are correctly identified."""
        slicer = Slicer()
        result = slicer.slice(example_file, 26, "result", SliceDirection.BACKWARD)

        # result depends on apply_discount, subtotal, and discount
        all_deps = set()
        for node in result.backward_slice:
            all_deps.update(node.dependencies)

        # Should track at least some of the dependencies
        assert len(all_deps) > 0

    def test_multiple_variables_same_file(self, example_file):
        """Test slicing different variables in the same file."""
        slicer = Slicer()

        # Slice 'result' variable
        result1 = slicer.slice(example_file, 26, "result", SliceDirection.BACKWARD)

        # Slice 'subtotal' variable
        result2 = slicer.slice(example_file, 25, "subtotal", SliceDirection.BACKWARD)

        # Both should work but have different slices
        assert result1.target_variable == "result"
        assert result2.target_variable == "subtotal"
        # They might have some overlap but not be identical
        assert result1.target_line != result2.target_line
