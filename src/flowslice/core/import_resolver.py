"""Import resolution and cross-file analysis support."""

import ast
from pathlib import Path
from typing import Optional


class ImportResolver:
    """Resolves imports and tracks cross-file dependencies."""

    def __init__(self, root_path: Path):
        """Initialize the import resolver.

        Args:
            root_path: Root directory of the project.
        """
        self.root_path = root_path
        self.import_map: dict[str, tuple[Path, str]] = {}  # name -> (file_path, module_name)
        self.ast_cache: dict[Path, ast.Module] = {}  # Cache parsed ASTs

    def resolve_import(self, module_name: str, current_file: Path) -> Optional[Path]:
        """Resolve an import to a file path.

        Args:
            module_name: The module being imported (e.g., 'utils' or 'package.utils')
            current_file: Path to the file containing the import

        Returns:
            Path to the imported module file, or None if not found
        """
        # Handle relative imports within the same directory
        current_dir = current_file.parent

        # Try as .py file in same directory
        same_dir = current_dir / f"{module_name}.py"
        if same_dir.exists():
            return same_dir

        # Try as package (directory with __init__.py)
        package_dir = current_dir / module_name / "__init__.py"
        if package_dir.exists():
            return package_dir

        # Try relative to root
        if self.root_path:
            root_relative = self.root_path / f"{module_name.replace('.', '/')}.py"
            if root_relative.exists():
                return root_relative

        return None

    def _trace_reexport(self, module_path: Path, name: str) -> tuple[Path, str]:
        """Trace through package __init__.py re-exports to find the actual source.

        Args:
            module_path: Path to the module (could be __init__.py)
            name: Name being imported

        Returns:
            Tuple of (actual_file_path, actual_name) where the symbol is defined
        """
        # If not an __init__.py, return as-is
        if module_path.name != "__init__.py":
            return (module_path, name)

        # Parse the __init__.py to find re-exports
        tree = self.get_ast(module_path)
        if not tree:
            return (module_path, name)

        # Look for "from .submodule import name" patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # Check if this import includes our target name
                for alias in node.names:
                    if alias.name == name:
                        # Found it! Now resolve where it's actually from
                        if node.module:
                            # Handle relative imports (e.g., from .file_utils import ...)
                            # Remove leading dot for relative imports
                            submodule_name = node.module.lstrip('.')
                            package_dir = module_path.parent

                            # Try as .py file in package directory
                            submodule_path = package_dir / f"{submodule_name}.py"
                            if submodule_path.exists():
                                return (submodule_path, name)

                            # Try as subdirectory with __init__.py
                            submodule_init = package_dir / submodule_name / "__init__.py"
                            if submodule_init.exists():
                                # Recursively trace through nested packages
                                return self._trace_reexport(submodule_init, name)

        # If we couldn't trace it, return the original __init__.py
        return (module_path, name)

    def parse_imports(self, tree: ast.Module, file_path: Path) -> dict[str, tuple[Path, str]]:
        """Parse import statements from an AST.

        Args:
            tree: The AST to parse
            file_path: Path to the file being parsed

        Returns:
            Dictionary mapping imported names to (file_path, original_name)
        """
        imports = {}

        for node in ast.walk(tree):
            # Handle: from module import name
            if isinstance(node, ast.ImportFrom) and node.module:
                module_path = self.resolve_import(node.module, file_path)
                if module_path:
                    for alias in node.names:
                        imported_name = alias.asname if alias.asname else alias.name
                        original_name = alias.name

                        # If this is a package __init__.py, trace through re-exports
                        actual_path, actual_name = self._trace_reexport(module_path, original_name)
                        imports[imported_name] = (actual_path, actual_name)

            # Handle: import module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    module_path = self.resolve_import(module_name, file_path)
                    if module_path:
                        imported_name = alias.asname if alias.asname else alias.name
                        imports[imported_name] = (module_path, module_name)

        return imports

    def get_ast(self, file_path: Path) -> Optional[ast.Module]:
        """Get cached or parse AST for a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Parsed AST module, or None if parsing fails
        """
        if file_path in self.ast_cache:
            return self.ast_cache[file_path]

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(file_path))
            self.ast_cache[file_path] = tree
            return tree
        except (OSError, SyntaxError):
            return None

    def find_function_def(
        self, tree: ast.Module, function_name: str
    ) -> Optional[ast.FunctionDef]:
        """Find a function definition in an AST.

        Args:
            tree: The AST to search
            function_name: Name of the function to find

        Returns:
            The FunctionDef node, or None if not found
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return node
        return None

    def resolve_function_source(
        self, function_name: str, imports: dict[str, tuple[Path, str]]
    ) -> Optional[tuple[Path, ast.FunctionDef]]:
        """Resolve a function call to its source definition.

        Args:
            function_name: Name of the function being called
            imports: Import map from parse_imports()

        Returns:
            Tuple of (file_path, function_def) or None if not found
        """
        # Check if this function is imported
        if function_name not in imports:
            return None

        module_path, original_name = imports[function_name]
        tree = self.get_ast(module_path)
        if not tree:
            return None

        func_def = self.find_function_def(tree, original_name)
        if not func_def:
            return None

        return (module_path, func_def)
