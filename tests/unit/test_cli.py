"""Unit tests for flowslice.cli.main."""

import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from flowslice.cli.main import main, print_usage


class TestCLI:
    """Test CLI functionality."""

    def test_print_usage(self, capsys):
        """Test that print_usage outputs help text."""
        print_usage()
        captured = capsys.readouterr()
        assert "flowslice - Dataflow Slicing for Python" in captured.out
        assert "Usage:" in captured.out
        assert "Examples:" in captured.out

    def test_main_no_arguments(self, capsys):
        """Test main with no arguments shows usage and exits."""
        with patch.object(sys, "argv", ["flowslice"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "flowslice - Dataflow Slicing for Python" in captured.out

    def test_main_invalid_format(self, capsys):
        """Test main with invalid criterion format."""
        with patch.object(sys, "argv", ["flowslice", "invalid_format"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error: Invalid format" in captured.out

    def test_main_invalid_direction(self, capsys):
        """Test main with invalid direction."""
        code = "x = 10\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            with patch.object(sys, "argv", ["flowslice", f"{temp_path}:1:x", "invalid"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "Error: Invalid direction 'invalid'" in captured.out
        finally:
            Path(temp_path).unlink()

    def test_main_file_not_found(self, capsys):
        """Test main with non-existent file."""
        with patch.object(
            sys, "argv", ["flowslice", "nonexistent.py:1:x", "backward"]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error: File 'nonexistent.py' not found" in captured.out

    def test_main_backward_slice(self, capsys):
        """Test main with backward slicing."""
        code = """x = 10
y = x + 5
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            with patch.object(sys, "argv", ["flowslice", f"{temp_path}:2:y", "backward"]):
                main()

            captured = capsys.readouterr()
            assert "BACKWARD SLICE" in captured.out
            assert "y" in captured.out
        finally:
            Path(temp_path).unlink()

    def test_main_forward_slice(self, capsys):
        """Test main with forward slicing."""
        code = """x = 10
y = x + 5
print(y)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            with patch.object(sys, "argv", ["flowslice", f"{temp_path}:2:y", "forward"]):
                main()

            captured = capsys.readouterr()
            assert "FORWARD SLICE" in captured.out
            assert "y" in captured.out
        finally:
            Path(temp_path).unlink()

    def test_main_both_directions(self, capsys):
        """Test main with both directions (default)."""
        code = """x = 10
y = x + 5
print(y)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            # Test explicit 'both'
            with patch.object(sys, "argv", ["flowslice", f"{temp_path}:2:y", "both"]):
                main()

            captured = capsys.readouterr()
            assert "BACKWARD SLICE" in captured.out
            assert "FORWARD SLICE" in captured.out
        finally:
            Path(temp_path).unlink()

    def test_main_default_direction_is_both(self, capsys):
        """Test that default direction is 'both'."""
        code = """x = 10
y = x + 5
print(y)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            # No direction specified - should default to 'both'
            with patch.object(sys, "argv", ["flowslice", f"{temp_path}:2:y"]):
                main()

            captured = capsys.readouterr()
            assert "BACKWARD SLICE" in captured.out
            assert "FORWARD SLICE" in captured.out
        finally:
            Path(temp_path).unlink()

    def test_main_with_example_file(self, capsys):
        """Test main with the actual example.py file."""
        example_path = Path("example.py")
        if example_path.exists():
            with patch.object(
                sys, "argv", ["flowslice", "example.py:26:result", "backward"]
            ):
                main()

            captured = capsys.readouterr()
            assert "BACKWARD SLICE" in captured.out
            assert "result" in captured.out
            assert "example.py" in captured.out
