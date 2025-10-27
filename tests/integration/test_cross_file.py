"""Integration tests for cross-file analysis."""

import tempfile
from pathlib import Path

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


def test_cross_file_backward_slice():
    """Test backward slicing across file boundaries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create utils.py with a helper function
        utils_file = tmpdir / "utils.py"
        utils_code = """
def process_data(input_file):
    data = read_file(input_file)
    return transform(data)
"""
        utils_file.write_text(utils_code)

        # Create main.py that imports from utils
        main_file = tmpdir / "main.py"
        main_code = """
from utils import process_data

def main():
    file_path = "input.txt"
    result = process_data(file_path)
    print(result)
"""
        main_file.write_text(main_code)

        # Slice 'result' in main.py
        slicer = Slicer(root_path=str(tmpdir))
        slice_result = slicer.slice(str(main_file), 6, "result", SliceDirection.BACKWARD)

        # Should find the assignment in main.py
        backward_lines = {node.line for node in slice_result.backward_slice}
        assert 5 in backward_lines  # file_path = "input.txt"
        assert 6 in backward_lines  # result = process_data(file_path)

        # Check that we tracked the imports correctly
        assert slicer.import_resolver is not None


def test_cross_file_forward_slice():
    """Test forward slicing across file boundaries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create utils.py
        utils_file = tmpdir / "utils.py"
        utils_code = """
def save_result(output_path, data):
    with open(output_path, 'w') as f:
        f.write(data)
"""
        utils_file.write_text(utils_code)

        # Create main.py
        main_file = tmpdir / "main.py"
        main_code = """
from utils import save_result

def main():
    output = "output.txt"
    data = process()
    save_result(output, data)
"""
        main_file.write_text(main_code)

        # Slice 'output' in main.py forward
        slicer = Slicer(root_path=str(tmpdir))
        slice_result = slicer.slice(str(main_file), 5, "output", SliceDirection.FORWARD)

        # Should find where output is used
        forward_lines = {node.line for node in slice_result.forward_slice}
        assert 7 in forward_lines  # save_result(output, data)


def test_cross_file_with_alias():
    """Test cross-file analysis with import aliases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create helpers.py
        helpers_file = tmpdir / "helpers.py"
        helpers_code = """
def validate_input(value):
    return value is not None
"""
        helpers_file.write_text(helpers_code)

        # Create main.py with alias
        main_file = tmpdir / "main.py"
        main_code = """
from helpers import validate_input as validate

def main():
    user_input = get_input()
    is_valid = validate(user_input)
    if is_valid:
        process(user_input)
"""
        main_file.write_text(main_code)

        # Slice 'user_input' forward
        slicer = Slicer(root_path=str(tmpdir))
        slice_result = slicer.slice(str(main_file), 5, "user_input", SliceDirection.FORWARD)

        # Should find usage with aliased function
        forward_lines = {node.line for node in slice_result.forward_slice}
        assert 6 in forward_lines  # is_valid = validate(user_input)
        assert 8 in forward_lines  # process(user_input)


def test_cross_file_disabled():
    """Test that cross-file analysis can be disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        utils_file = tmpdir / "utils.py"
        utils_file.write_text("def helper(x): return x * 2\n")

        main_file = tmpdir / "main.py"
        main_code = """
from utils import helper

def main():
    value = 10
    result = helper(value)
"""
        main_file.write_text(main_code)

        # Create slicer with cross-file disabled
        slicer = Slicer(root_path=str(tmpdir), enable_cross_file=False)
        assert slicer.import_resolver is None

        # Should still work for single-file analysis
        slice_result = slicer.slice(str(main_file), 6, "result", SliceDirection.BACKWARD)
        assert len(slice_result.backward_slice) > 0


def test_import_not_found_graceful():
    """Test graceful handling when imported module doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create main.py that imports non-existent module
        main_file = tmpdir / "main.py"
        main_code = """
from nonexistent import helper

def main():
    value = 10
    result = helper(value)
    print(result)
"""
        main_file.write_text(main_code)

        # Should not crash
        slicer = Slicer(root_path=str(tmpdir))
        slice_result = slicer.slice(str(main_file), 7, "result", SliceDirection.BACKWARD)

        # Should still find local variables
        backward_lines = {node.line for node in slice_result.backward_slice}
        assert 6 in backward_lines  # result = helper(value)
