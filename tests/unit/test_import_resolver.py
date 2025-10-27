"""Tests for import resolution and cross-file analysis."""

import ast
import tempfile
from pathlib import Path

from flowslice.core.import_resolver import ImportResolver


def test_resolve_import_same_directory():
    """Test resolving imports in the same directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create two files
        main_file = tmpdir / "main.py"
        utils_file = tmpdir / "utils.py"

        main_file.write_text("from utils import helper\n")
        utils_file.write_text("def helper(): pass\n")

        resolver = ImportResolver(tmpdir)
        resolved = resolver.resolve_import("utils", main_file)

        assert resolved == utils_file


def test_parse_imports_from_statement():
    """Test parsing 'from module import name' statements."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        main_file = tmpdir / "main.py"
        utils_file = tmpdir / "utils.py"

        main_code = """
from utils import process_data, transform
from helpers import validate
"""
        utils_file.write_text("def process_data(): pass\n")
        main_file.write_text(main_code)

        resolver = ImportResolver(tmpdir)
        tree = ast.parse(main_code)
        imports = resolver.parse_imports(tree, main_file)

        # Should find process_data and transform from utils
        assert "process_data" in imports
        assert imports["process_data"][0] == utils_file
        assert imports["process_data"][1] == "process_data"

        assert "transform" in imports
        assert imports["transform"][0] == utils_file


def test_parse_imports_with_alias():
    """Test parsing imports with 'as' aliases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        main_file = tmpdir / "main.py"
        utils_file = tmpdir / "utils.py"

        main_code = "from utils import process_data as pd\n"
        utils_file.write_text("def process_data(): pass\n")
        main_file.write_text(main_code)

        resolver = ImportResolver(tmpdir)
        tree = ast.parse(main_code)
        imports = resolver.parse_imports(tree, main_file)

        # Should map alias to original
        assert "pd" in imports
        assert imports["pd"][0] == utils_file
        assert imports["pd"][1] == "process_data"


def test_find_function_def():
    """Test finding function definitions in AST."""
    code = """
def helper(x):
    return x * 2

def process():
    pass
"""
    tree = ast.parse(code)
    resolver = ImportResolver(Path("."))

    func_def = resolver.find_function_def(tree, "helper")
    assert func_def is not None
    assert func_def.name == "helper"
    assert len(func_def.args.args) == 1

    func_def2 = resolver.find_function_def(tree, "process")
    assert func_def2 is not None
    assert func_def2.name == "process"

    # Non-existent function
    func_def3 = resolver.find_function_def(tree, "nonexistent")
    assert func_def3 is None


def test_resolve_function_source():
    """Test resolving a function call to its source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        main_file = tmpdir / "main.py"
        utils_file = tmpdir / "utils.py"

        main_code = "from utils import process\n"
        utils_code = "def process(x):\n    return x * 2\n"

        main_file.write_text(main_code)
        utils_file.write_text(utils_code)

        resolver = ImportResolver(tmpdir)
        tree = ast.parse(main_code)
        imports = resolver.parse_imports(tree, main_file)

        # Resolve the function
        result = resolver.resolve_function_source("process", imports)

        assert result is not None
        file_path, func_def = result
        assert file_path == utils_file
        assert func_def.name == "process"
        assert len(func_def.args.args) == 1
        assert func_def.args.args[0].arg == "x"


def test_ast_caching():
    """Test that ASTs are cached."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        utils_file = tmpdir / "utils.py"
        utils_file.write_text("def helper(): pass\n")

        resolver = ImportResolver(tmpdir)

        # First access - should parse
        ast1 = resolver.get_ast(utils_file)
        assert ast1 is not None

        # Second access - should return cached
        ast2 = resolver.get_ast(utils_file)
        assert ast2 is ast1  # Same object


def test_import_not_found():
    """Test behavior when import cannot be resolved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        main_file = tmpdir / "main.py"
        main_file.write_text("from nonexistent import helper\n")

        resolver = ImportResolver(tmpdir)
        resolved = resolver.resolve_import("nonexistent", main_file)

        assert resolved is None


def test_package_import_with_init():
    """Test importing from a package (directory with __init__.py)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create package structure
        main_file = tmpdir / "main.py"
        utils_dir = tmpdir / "utils"
        utils_dir.mkdir()
        utils_init = utils_dir / "__init__.py"

        main_file.write_text("from utils import helper\n")
        utils_init.write_text("def helper(): pass\n")

        resolver = ImportResolver(tmpdir)
        resolved = resolver.resolve_import("utils", main_file)

        # Should resolve to the __init__.py
        assert resolved == utils_init


def test_package_reexport_tracing():
    """Test tracing through __init__.py re-exports to find actual source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create package structure:
        # main.py: from utils import detect_file_format
        # utils/__init__.py: from .file_utils import detect_file_format
        # utils/file_utils.py: def detect_file_format(): pass

        main_file = tmpdir / "main.py"
        utils_dir = tmpdir / "utils"
        utils_dir.mkdir()
        utils_init = utils_dir / "__init__.py"
        file_utils = utils_dir / "file_utils.py"

        main_file.write_text("from utils import detect_file_format\n")
        utils_init.write_text("from .file_utils import detect_file_format\n")
        file_utils.write_text("def detect_file_format(path):\n    pass\n")

        resolver = ImportResolver(tmpdir)
        tree = ast.parse(main_file.read_text())
        imports = resolver.parse_imports(tree, main_file)

        # Should trace through __init__.py to file_utils.py
        assert "detect_file_format" in imports
        assert imports["detect_file_format"][0] == file_utils
        assert imports["detect_file_format"][1] == "detect_file_format"


def test_package_reexport_with_multiple_symbols():
    """Test tracing re-exports when __init__.py imports multiple symbols."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        main_file = tmpdir / "main.py"
        utils_dir = tmpdir / "utils"
        utils_dir.mkdir()
        utils_init = utils_dir / "__init__.py"
        file_utils = utils_dir / "file_utils.py"
        time_utils = utils_dir / "time_utils.py"

        main_code = """
from utils import detect_format, parse_time
"""
        main_file.write_text(main_code)

        # __init__.py re-exports from multiple modules
        utils_init.write_text("""
from .file_utils import detect_format
from .time_utils import parse_time
""")

        file_utils.write_text("def detect_format(): pass\n")
        time_utils.write_text("def parse_time(): pass\n")

        resolver = ImportResolver(tmpdir)
        tree = ast.parse(main_code)
        imports = resolver.parse_imports(tree, main_file)

        # Each should trace to its actual source
        assert imports["detect_format"][0] == file_utils
        assert imports["parse_time"][0] == time_utils
