"""Unit tests for flowslice.core.models."""


from flowslice.core.models import SliceDirection, SliceNode, SliceResult


class TestSliceDirection:
    """Test SliceDirection enum."""

    def test_backward_value(self):
        """Test BACKWARD direction has correct value."""
        assert SliceDirection.BACKWARD.value == "backward"

    def test_forward_value(self):
        """Test FORWARD direction has correct value."""
        assert SliceDirection.FORWARD.value == "forward"

    def test_both_value(self):
        """Test BOTH direction has correct value."""
        assert SliceDirection.BOTH.value == "both"

    def test_from_string(self):
        """Test creating SliceDirection from string."""
        assert SliceDirection("backward") == SliceDirection.BACKWARD
        assert SliceDirection("forward") == SliceDirection.FORWARD
        assert SliceDirection("both") == SliceDirection.BOTH


class TestSliceNode:
    """Test SliceNode dataclass."""

    def test_create_basic_node(self):
        """Test creating a basic SliceNode."""
        node = SliceNode(
            file="test.py",
            line=42,
            function="main",
            code="x = 10",
            variable="x",
            operation="assignment",
        )
        assert node.file == "test.py"
        assert node.line == 42
        assert node.function == "main"
        assert node.code == "x = 10"
        assert node.variable == "x"
        assert node.operation == "assignment"
        assert node.dependencies == []
        assert node.context is None

    def test_create_node_with_dependencies(self):
        """Test creating a SliceNode with dependencies."""
        node = SliceNode(
            file="test.py",
            line=42,
            function="main",
            code="y = x + 1",
            variable="y",
            operation="assignment",
            dependencies=["x"],
        )
        assert node.dependencies == ["x"]

    def test_create_node_with_context(self):
        """Test creating a SliceNode with context."""
        node = SliceNode(
            file="test.py",
            line=42,
            function="main",
            code="for item in items:",
            variable="item",
            operation="for loop",
            context="iterates over items",
        )
        assert node.context == "iterates over items"


class TestSliceResult:
    """Test SliceResult dataclass."""

    def test_create_empty_result(self):
        """Test creating an empty SliceResult."""
        result = SliceResult(
            target_file="test.py",
            target_line=42,
            target_variable="x",
        )
        assert result.target_file == "test.py"
        assert result.target_line == 42
        assert result.target_variable == "x"
        assert result.backward_slice == []
        assert result.forward_slice == []

    def test_create_result_with_slices(self):
        """Test creating a SliceResult with slice data."""
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
        assert len(result.backward_slice) == 1
        assert len(result.forward_slice) == 1
        assert result.backward_slice[0] == backward_node
        assert result.forward_slice[0] == forward_node
