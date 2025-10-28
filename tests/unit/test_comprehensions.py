"""Tests for comprehension tracking (list, dict, set, generator)."""

import tempfile
from pathlib import Path

from flowslice import Slicer, SliceDirection


def test_list_comprehension_backward():
    """Test backward slicing through list comprehension."""
    code = """\
def test_func():
    source = [1, 2, 3, 4, 5]
    filtered = [x * 2 for x in source if x > 2]
    return filtered
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        slicer = Slicer(enable_cross_file=False)
        result = slicer.slice(str(temp_path), 3, "filtered", SliceDirection.BACKWARD)

        assert len(result.backward_slice) == 2
        assert any("source = [1, 2, 3, 4, 5]" in node.code for node in result.backward_slice)
        assert any("filtered = [x * 2 for x in source if x > 2]" in node.code for node in result.backward_slice)
    finally:
        temp_path.unlink()


def test_dict_comprehension_backward():
    """Test backward slicing through dict comprehension."""
    code = """\
def test_func():
    data = {"a": 1, "b": 2, "c": 3}
    transformed = {k: v * 2 for k, v in data.items()}
    return transformed
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        slicer = Slicer(enable_cross_file=False)
        result = slicer.slice(str(temp_path), 3, "transformed", SliceDirection.BACKWARD)

        assert len(result.backward_slice) == 2
        assert any("data = " in node.code for node in result.backward_slice)
        assert any("transformed = " in node.code for node in result.backward_slice)
    finally:
        temp_path.unlink()


def test_set_comprehension_backward():
    """Test backward slicing through set comprehension."""
    code = """\
def test_func():
    numbers = [1, 2, 2, 3, 3, 4]
    unique_doubled = {x * 2 for x in numbers}
    return unique_doubled
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        slicer = Slicer(enable_cross_file=False)
        result = slicer.slice(str(temp_path), 3, "unique_doubled", SliceDirection.BACKWARD)

        assert len(result.backward_slice) == 2
        assert any("numbers = " in node.code for node in result.backward_slice)
        assert any("unique_doubled = " in node.code for node in result.backward_slice)
    finally:
        temp_path.unlink()


def test_generator_expression_backward():
    """Test backward slicing through generator expression."""
    code = """\
def test_func():
    source = [1, 2, 3, 4, 5]
    gen = (x * 2 for x in source if x > 2)
    result = list(gen)
    return result
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        slicer = Slicer(enable_cross_file=False)
        result = slicer.slice(str(temp_path), 4, "result", SliceDirection.BACKWARD)

        # Should include source, gen, and result
        assert len(result.backward_slice) >= 3
        assert any("source = " in node.code for node in result.backward_slice)
    finally:
        temp_path.unlink()


def test_nested_comprehension():
    """Test comprehension with nested structure."""
    code = """\
def test_func():
    matrix = [[1, 2], [3, 4], [5, 6]]
    flattened = [item for row in matrix for item in row]
    return flattened
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        slicer = Slicer(enable_cross_file=False)
        result = slicer.slice(str(temp_path), 3, "flattened", SliceDirection.BACKWARD)

        assert len(result.backward_slice) == 2
        assert any("matrix = " in node.code for node in result.backward_slice)
        assert any("flattened = " in node.code for node in result.backward_slice)
    finally:
        temp_path.unlink()


def test_comprehension_with_method_call():
    """Test comprehension iterating over method call result."""
    code = """\
def test_func():
    data = {"a": 1, "b": 2}
    keys = [k for k in data.keys()]
    return keys
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        slicer = Slicer(enable_cross_file=False)
        result = slicer.slice(str(temp_path), 3, "keys", SliceDirection.BACKWARD)

        assert len(result.backward_slice) == 2
        assert any("data = " in node.code for node in result.backward_slice)
        assert any("keys = " in node.code for node in result.backward_slice)
    finally:
        temp_path.unlink()


def test_comprehension_forward_slice():
    """Test forward slicing from variable used in comprehension."""
    code = """\
def test_func():
    source = [1, 2, 3, 4, 5]
    filtered = [x * 2 for x in source if x > 2]
    result = sum(filtered)
    return result
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)

    try:
        slicer = Slicer(enable_cross_file=False)
        result = slicer.slice(str(temp_path), 2, "source", SliceDirection.FORWARD)

        # Should include filtered (uses source) and potentially result
        # Note: forward slice shows what depends ON source, not source itself
        assert len(result.forward_slice) >= 1
        assert any("filtered = " in node.code for node in result.forward_slice)
    finally:
        temp_path.unlink()
