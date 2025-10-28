"""Core slicing engine for flowslice."""

import ast
from pathlib import Path
from typing import Optional

from flowslice.core.import_resolver import ImportResolver
from flowslice.core.models import SliceDirection, SliceNode, SliceResult


class SlicerVisitor(ast.NodeVisitor):
    """AST visitor for dataflow slicing."""

    def __init__(
        self,
        target_var: str,
        target_line: int,
        direction: SliceDirection,
        source_lines: list[str],
        current_file: str = "<current>",
        imports: Optional[dict[str, tuple[Path, str]]] = None,
        import_resolver: Optional[ImportResolver] = None,
        function_defs: Optional[dict[str, ast.FunctionDef]] = None,
    ):
        self.target_var = target_var
        self.target_line = target_line
        self.direction = direction
        self.source_lines = source_lines
        self.current_file = current_file  # Track current file for cross-file analysis
        self.imports = imports or {}  # Map of imported names to (file_path, original_name)
        self.import_resolver = import_resolver  # For resolving cross-file calls
        self.function_defs = function_defs or {}  # Local function definitions

        self.nodes: list[SliceNode] = []
        self.current_function = "<module>"
        self.function_stack = ["<module>"]
        self.started = False
        self.target_function: Optional[str] = None  # Track function containing target

        if direction == SliceDirection.BACKWARD:
            self.relevant_vars: set[str] = {target_var}
        else:  # forward
            self.affected_vars: set[str] = {target_var}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function context."""
        self.function_stack.append(node.name)
        self.current_function = node.name

        # Check parameters
        if self.direction == SliceDirection.BACKWARD:
            for arg in node.args.args:
                if arg.arg in self.relevant_vars:
                    self.nodes.append(
                        SliceNode(
                            file=self.current_file,
                            line=node.lineno,
                            function=self.current_function,
                            code=f"def {node.name}(..., {arg.arg}, ...)",
                            variable=arg.arg,
                            operation="parameter",
                            dependencies=[],
                        )
                    )

        self.generic_visit(node)
        self.function_stack.pop()
        self.current_function = (
            self.function_stack[-1] if self.function_stack else "<module>"
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track assignments."""
        if self.direction == SliceDirection.BACKWARD:
            # Only include assignments at or before the target line
            if node.lineno <= self.target_line:
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in self.relevant_vars:
                        rhs_vars = self._get_names_from_expr(node.value)
                        code = (
                            self.source_lines[node.lineno - 1]
                            if node.lineno <= len(self.source_lines)
                            else ""
                        )

                        # Filter to most specific attribute paths
                        filtered_deps = self._filter_most_specific(rhs_vars)

                        self.nodes.append(
                            SliceNode(
                                file=self.current_file,
                                line=node.lineno,
                                function=self.current_function,
                                code=code,
                                variable=target.id,
                                operation="assignment",
                                dependencies=list(filtered_deps),
                            )
                        )

                        # Check if RHS is a function call (imported or local)
                        # If so, follow into it because it produces the tracked variable
                        if isinstance(node.value, ast.Call):
                            func_call = node.value
                            if isinstance(func_call.func, ast.Name):
                                arg_vars = set()
                                for arg in func_call.args:
                                    arg_vars.update(self._get_names_from_expr(arg))
                                if arg_vars:  # Only if it has arguments
                                    # Try cross-file first, falls back to local
                                    self._analyze_cross_file_call(func_call, arg_vars, node.lineno)

                        # Add RHS vars to relevant set
                        self.relevant_vars.update(rhs_vars)

        else:  # forward
            if not self.started and node.lineno >= self.target_line:
                self.started = True
                self.target_function = self.current_function  # Capture target's function

            # Only include nodes from the same function as the target
            if self.started and self.current_function == self.target_function:
                rhs_vars = self._get_names_from_expr(node.value)
                if rhs_vars & self.affected_vars:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            code = (
                                self.source_lines[node.lineno - 1]
                                if node.lineno <= len(self.source_lines)
                                else ""
                            )
                            self.nodes.append(
                                SliceNode(
                                    file=self.current_file,
                                    line=node.lineno,
                                    function=self.current_function,
                                    code=code,
                                    variable=target.id,
                                    operation="assignment",
                                    dependencies=list(rhs_vars & self.affected_vars),
                                )
                            )
                            self.affected_vars.add(target.id)

        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        """Track method calls like list.append()."""
        if isinstance(node.value, ast.Call) and isinstance(
            node.value.func, ast.Attribute
        ):
            obj = self._get_base_name(node.value.func.value)
            method = node.value.func.attr

            if self.direction == SliceDirection.BACKWARD:
                # Only include method calls at or before the target line
                if node.lineno <= self.target_line and obj in self.relevant_vars:
                    args = [self._get_names_from_expr(arg) for arg in node.value.args]
                    all_args = set()
                    for arg_set in args:
                        all_args.update(arg_set)

                    code = (
                        self.source_lines[node.lineno - 1]
                        if node.lineno <= len(self.source_lines)
                        else ""
                    )
                    self.nodes.append(
                        SliceNode(
                            file=self.current_file,
                            line=node.lineno,
                            function=self.current_function,
                            code=code,
                            variable=obj,
                            operation=f".{method}()",
                            dependencies=list(all_args),
                        )
                    )
                    self.relevant_vars.update(all_args)

            else:  # forward
                # Only include nodes from the same function as the target
                if (self.started and
                    self.current_function == self.target_function and
                    obj in self.affected_vars):
                    code = (
                        self.source_lines[node.lineno - 1]
                        if node.lineno <= len(self.source_lines)
                        else ""
                    )
                    self.nodes.append(
                        SliceNode(
                            file=self.current_file,
                            line=node.lineno,
                            function=self.current_function,
                            code=code,
                            variable=obj,
                            operation=f".{method}()",
                            dependencies=[],
                        )
                    )

        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Track for loops."""
        if self.direction == SliceDirection.BACKWARD:
            # Only include for loops at or before the target line
            if (node.lineno <= self.target_line and
                isinstance(node.target, ast.Name) and
                node.target.id in self.relevant_vars):
                iter_vars = self._get_names_from_expr(node.iter)
                code = (
                    self.source_lines[node.lineno - 1]
                    if node.lineno <= len(self.source_lines)
                    else ""
                )

                self.nodes.append(
                    SliceNode(
                        file=self.current_file,
                        line=node.lineno,
                        function=self.current_function,
                        code=code,
                        variable=node.target.id,
                        operation="for loop",
                        dependencies=list(iter_vars),
                        context=f"iterates over {iter_vars}",
                    )
                )
                self.relevant_vars.update(iter_vars)

        else:  # forward
            # Only include nodes from the same function as the target
            if self.started and self.current_function == self.target_function:
                iter_vars = self._get_names_from_expr(node.iter)
                if iter_vars & self.affected_vars:
                    code = (
                        self.source_lines[node.lineno - 1]
                        if node.lineno <= len(self.source_lines)
                        else ""
                    )
                    if isinstance(node.target, ast.Name):
                        self.nodes.append(
                            SliceNode(
                                file=self.current_file,
                                line=node.lineno,
                                function=self.current_function,
                                code=code,
                                variable=node.target.id,
                                operation="for loop",
                                dependencies=list(iter_vars & self.affected_vars),
                                context=f"iterates over {iter_vars & self.affected_vars}",
                            )
                        )
                        self.affected_vars.add(node.target.id)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Track function calls."""
        # For forward slicing, track where variables are used in function calls
        # For backward slicing, we only care about calls that PRODUCE tracked variables
        # (handled in visit_Assign)
        if self.direction == SliceDirection.FORWARD and self.started:
            # Check arguments
            for arg in node.args:
                arg_vars = self._get_names_from_expr(arg)
                check_set = self.affected_vars

                # Only include if in same function as target
                if not (self.started and self.current_function == self.target_function):
                    continue

                if arg_vars & check_set and hasattr(node, "lineno"):
                    code = (
                        self.source_lines[node.lineno - 1]
                        if node.lineno <= len(self.source_lines)
                        else ""
                    )
                    func_name = self._get_func_name(node.func)
                    self.nodes.append(
                        SliceNode(
                            file=self.current_file,
                            line=node.lineno,
                            function=self.current_function,
                            code=code,
                            variable=list(arg_vars & check_set)[0],
                            operation=f"passed to {func_name}()",
                            dependencies=list(arg_vars & check_set),
                        )
                    )

                    # Cross-file analysis: follow into imported functions
                    if self.import_resolver and isinstance(node.func, ast.Name):
                        self._analyze_cross_file_call(node, arg_vars & check_set, node.lineno)

        self.generic_visit(node)

    def _get_func_name(self, node: ast.expr) -> str:
        """Get function name from call."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        return "<unknown>"

    def _filter_most_specific(self, names: set[str]) -> set[str]:
        """Filter to keep only the most specific attribute paths.

        If we have both "args" and "args.file", keep only "args.file".
        If we have "obj.a" and "obj.b", keep both (different attributes).

        Args:
            names: Set of variable/attribute names

        Returns:
            Filtered set with only most specific paths
        """
        if not names:
            return names

        # Group by base name
        result = set()
        for name in names:
            # Check if this name is a prefix of any other name
            is_prefix = False
            for other in names:
                if other != name and other.startswith(name + "."):
                    # This name is a prefix of a more specific path
                    is_prefix = True
                    break
            if not is_prefix:
                result.add(name)

        return result

    def _get_names_from_expr(self, expr: ast.expr) -> set[str]:
        """Extract all variable names from an expression, including attributes.

        Examples:
            args.file -> {"args.file", "args"}
            obj.attr.subattr -> {"obj.attr.subattr", "obj.attr", "obj"}
            simple_var -> {"simple_var"}
        """
        names: set[str] = set()

        class NameCollector(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name) -> None:
                names.add(node.id)

            def visit_Attribute(self, node: ast.Attribute) -> None:
                # Get the full attribute path
                full_path = self._get_full_attr_path(node)
                if full_path:
                    names.add(full_path)
                    # Also add intermediate paths for tracking
                    # e.g., for "a.b.c" add "a.b" and "a"
                    parts = full_path.split(".")
                    for i in range(len(parts) - 1, 0, -1):
                        names.add(".".join(parts[:i]))
                # Continue visiting to get nested attributes
                self.generic_visit(node)

            def visit_ListComp(self, node: ast.ListComp) -> None:
                """Handle list comprehensions: [x*2 for x in source]."""
                # Visit the iterator (source)
                for generator in node.generators:
                    self.visit(generator.iter)
                # Note: Don't visit the target (x) as it's local to comprehension

            def visit_SetComp(self, node: ast.SetComp) -> None:
                """Handle set comprehensions: {x*2 for x in source}."""
                for generator in node.generators:
                    self.visit(generator.iter)

            def visit_DictComp(self, node: ast.DictComp) -> None:
                """Handle dict comprehensions: {k: v for k, v in items}."""
                for generator in node.generators:
                    self.visit(generator.iter)

            def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
                """Handle generator expressions: (x*2 for x in source)."""
                for generator in node.generators:
                    self.visit(generator.iter)

            def _get_full_attr_path(self, node: ast.expr) -> str:
                """Build full attribute path like 'obj.attr.subattr'."""
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    base = self._get_full_attr_path(node.value)
                    if base:
                        return f"{base}.{node.attr}"
                return ""

        NameCollector().visit(expr)
        return names

    def _get_base_name(self, node: ast.expr) -> str:
        """Get the base variable name from an attribute chain."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_base_name(node.value)
        return ""

    def _analyze_local_function_call(
        self, call_node: ast.Call, relevant_args: set[str], call_site_line: int
    ) -> None:
        """Analyze a call to a local function (defined in same file).

        Args:
            call_node: The Call node to analyze
            relevant_args: Set of argument variable names that are relevant to the slice
            call_site_line: Line number where the function is called
        """
        if not isinstance(call_node.func, ast.Name):
            return

        func_name = call_node.func.id

        # Check if this is a local function
        if func_name not in self.function_defs:
            return

        func_def = self.function_defs[func_name]

        # Map call arguments to function parameters
        param_mapping = {}
        for i, arg in enumerate(call_node.args):
            if i < len(func_def.args.args):
                param_name = func_def.args.args[i].arg
                arg_vars = self._get_names_from_expr(arg)
                if arg_vars & relevant_args:
                    param_mapping[param_name] = arg_vars

        if not param_mapping:
            return

        # Analyze the local function body for dataflow
        if self.direction == SliceDirection.BACKWARD:
            self._backward_slice_local_function(func_def, param_mapping)
        else:  # FORWARD
            self._forward_slice_local_function(func_def, param_mapping)

    def _analyze_cross_file_call(
        self, call_node: ast.Call, relevant_args: set[str], call_site_line: int
    ) -> None:
        """Analyze a function call that may be from an imported module.

        Args:
            call_node: The Call node to analyze
            relevant_args: Set of argument variable names that are relevant to the slice
            call_site_line: Line number where the function is called (for ordering)
        """
        if not isinstance(call_node.func, ast.Name):
            return

        func_name = call_node.func.id

        # Check if this function is imported
        if func_name not in self.imports:
            # Check if it's a local function instead
            self._analyze_local_function_call(call_node, relevant_args, call_site_line)
            return

        # Resolve the function to its source
        if not self.import_resolver:
            return
        result = self.import_resolver.resolve_function_source(func_name, self.imports)
        if not result:
            return

        file_path, func_def = result

        # Get the source lines for the imported file
        try:
            with open(file_path, encoding="utf-8") as f:
                imported_source_lines = f.readlines()
        except (OSError, UnicodeDecodeError):
            return

        # Map call arguments to function parameters
        # e.g., process_data(file_path) -> parameter 'input_file'
        param_mapping = {}  # param_name -> arg_vars
        for i, arg in enumerate(call_node.args):
            if i < len(func_def.args.args):
                param_name = func_def.args.args[i].arg
                arg_vars = self._get_names_from_expr(arg)
                if arg_vars & relevant_args:
                    param_mapping[param_name] = arg_vars

        if not param_mapping:
            return

        # Analyze the imported function body for dataflow
        if self.direction == SliceDirection.BACKWARD:
            self._backward_slice_imported_function(
                func_def, file_path, imported_source_lines, param_mapping
            )
        else:  # FORWARD
            self._forward_slice_imported_function(
                func_def, file_path, imported_source_lines, param_mapping
            )

    def _forward_slice_imported_function(
        self,
        func_def: ast.FunctionDef,
        file_path: Path,
        source_lines: list[str],
        param_mapping: dict[str, set[str]],
    ) -> None:
        """Perform forward slicing on an imported function.

        Args:
            func_def: The function definition AST node
            file_path: Path to the file containing the function
            source_lines: Source code lines of the imported file
            param_mapping: Mapping of parameter names to argument variables
        """
        # Start tracking from the parameters we care about
        affected_vars = set(param_mapping.keys())

        # Walk through the function body forward to see where parameters are used
        for stmt in func_def.body:
            self._track_statement_forward(
                stmt, affected_vars, file_path, source_lines, func_def.name
            )

    def _backward_slice_local_function(
        self, func_def: ast.FunctionDef, param_mapping: dict[str, set[str]]
    ) -> None:
        """Perform backward slicing on a local function.

        Args:
            func_def: The function definition AST node
            param_mapping: Mapping of parameter names to argument variables
        """
        # Start tracking from the parameters we care about
        tracked_vars = set(param_mapping.keys())

        # Walk through the function body to track dependencies
        for stmt in func_def.body:
            self._track_statement_backward(
                stmt, tracked_vars, Path(self.current_file), self.source_lines, func_def.name
            )

    def _forward_slice_local_function(
        self, func_def: ast.FunctionDef, param_mapping: dict[str, set[str]]
    ) -> None:
        """Perform forward slicing on a local function.

        Args:
            func_def: The function definition AST node
            param_mapping: Mapping of parameter names to argument variables
        """
        # Start tracking from the parameters we care about
        affected_vars = set(param_mapping.keys())

        # Walk through the function body to see where parameters are used
        for stmt in func_def.body:
            self._track_statement_forward(
                stmt, affected_vars, Path(self.current_file), self.source_lines, func_def.name
            )

    def _backward_slice_imported_function(
        self,
        func_def: ast.FunctionDef,
        file_path: Path,
        source_lines: list[str],
        param_mapping: dict[str, set[str]],
    ) -> None:
        """Perform backward slicing on an imported function.

        Args:
            func_def: The function definition AST node
            file_path: Path to the file containing the function
            source_lines: Source code lines of the imported file
            param_mapping: Mapping of parameter names to argument variables
        """
        # Start tracking from the parameters we care about
        tracked_vars = set(param_mapping.keys())

        # First pass: identify all variables we need to track
        # Walk FORWARD to build the dependency chain
        for stmt in func_def.body:
            self._track_statement_backward(
                stmt, tracked_vars, file_path, source_lines, func_def.name
            )

    def _track_statement_forward(
        self,
        stmt: ast.stmt,
        affected_vars: set[str],
        file_path: Path,
        source_lines: list[str],
        function_name: str,
    ) -> None:
        """Track a statement forward for cross-file analysis.

        Args:
            stmt: The statement to analyze
            affected_vars: Variables we're currently tracking (affected by the slice)
            file_path: The file containing this statement
            source_lines: Source lines of the file
            function_name: Name of the function being analyzed
        """
        # Handle assignments: x = expr (if expr uses affected vars, x becomes affected)
        if isinstance(stmt, ast.Assign):
            rhs_vars = self._get_names_from_expr(stmt.value)

            # If any affected variable is used in RHS, track the assignment
            if rhs_vars & affected_vars:
                code = source_lines[stmt.lineno - 1] if stmt.lineno <= len(source_lines) else ""
                target_name = ""
                if stmt.targets and isinstance(stmt.targets[0], ast.Name):
                    target_name = stmt.targets[0].id

                # Add this assignment to the slice
                self.nodes.append(
                    SliceNode(
                        file=file_path.name,
                        line=stmt.lineno,
                        function=function_name,
                        code=code,
                        variable=list(rhs_vars & affected_vars)[0],
                        operation="assignment",
                        dependencies=list(rhs_vars & affected_vars),
                    )
                )

                # The target is now also affected
                if target_name:
                    affected_vars.add(target_name)

        # Handle function calls with affected variables as arguments
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            arg_vars = set()
            for arg in stmt.value.args:
                arg_vars.update(self._get_names_from_expr(arg))

            if arg_vars & affected_vars:
                code = source_lines[stmt.lineno - 1] if stmt.lineno <= len(source_lines) else ""
                func_name = self._get_func_name(stmt.value.func)

                relevant_vars = arg_vars & affected_vars
                self.nodes.append(
                    SliceNode(
                        file=file_path.name,
                        line=stmt.lineno,
                        function=function_name,
                        code=code,
                        variable=list(relevant_vars)[0] if relevant_vars else "",
                        operation=f"passed to {func_name}()",
                        dependencies=list(relevant_vars),
                    )
                )

        # Handle return statements
        elif isinstance(stmt, ast.Return) and stmt.value:
            return_vars = self._get_names_from_expr(stmt.value)

            if return_vars & affected_vars:
                code = source_lines[stmt.lineno - 1] if stmt.lineno <= len(source_lines) else ""

                self.nodes.append(
                    SliceNode(
                        file=file_path.name,
                        line=stmt.lineno,
                        function=function_name,
                        code=code,
                        variable=list(return_vars & affected_vars)[0],
                        operation="returned",
                        dependencies=list(return_vars & affected_vars),
                    )
                )

        # Handle compound statements (Try, With, For, If, etc.) - recurse into their bodies
        elif isinstance(stmt, (ast.Try, ast.With, ast.For, ast.While, ast.If)):
            # Get all sub-statements from the compound statement
            sub_stmts = []
            if isinstance(stmt, ast.Try):
                sub_stmts.extend(stmt.body)
                sub_stmts.extend(stmt.orelse)
                sub_stmts.extend(stmt.finalbody)
                for handler in stmt.handlers:
                    sub_stmts.extend(handler.body)
            elif isinstance(stmt, ast.With):
                # Check if the with statement uses an affected variable
                for item in stmt.items:
                    context_vars = self._get_names_from_expr(item.context_expr)
                    if context_vars & affected_vars:
                        line_idx = stmt.lineno - 1
                        code = source_lines[line_idx] if stmt.lineno <= len(source_lines) else ""
                        self.nodes.append(
                            SliceNode(
                                file=file_path.name,
                                line=stmt.lineno,
                                function=function_name,
                                code=code,
                                variable=list(context_vars & affected_vars)[0],
                                operation="used in with statement",
                                dependencies=list(context_vars & affected_vars),
                            )
                        )
                sub_stmts.extend(stmt.body)
            elif isinstance(stmt, (ast.For, ast.While)):
                sub_stmts.extend(stmt.body)
                sub_stmts.extend(stmt.orelse)
            elif isinstance(stmt, ast.If):
                sub_stmts.extend(stmt.body)
                sub_stmts.extend(stmt.orelse)

            # Recursively process sub-statements
            for sub_stmt in sub_stmts:
                self._track_statement_forward(
                    sub_stmt, affected_vars, file_path, source_lines, function_name
                )

    def _track_statement_backward(
        self,
        stmt: ast.stmt,
        tracked_vars: set[str],
        file_path: Path,
        source_lines: list[str],
        function_name: str,
    ) -> None:
        """Track a statement backward for cross-file analysis.

        Args:
            stmt: The statement to analyze
            tracked_vars: Variables we're currently tracking
            file_path: The file containing this statement
            source_lines: Source lines of the file
            function_name: Name of the function being analyzed
        """
        # Handle assignments: x = ...
        if isinstance(stmt, ast.Assign):
            # Get all variables used in the RHS
            rhs_vars = self._get_names_from_expr(stmt.value)

            # Check if any tracked variable is USED in the RHS
            if rhs_vars & tracked_vars:
                code = source_lines[stmt.lineno - 1] if stmt.lineno <= len(source_lines) else ""
                target_name = ""
                if stmt.targets and isinstance(stmt.targets[0], ast.Name):
                    target_name = stmt.targets[0].id

                # Add this assignment to the slice
                self.nodes.append(
                    SliceNode(
                        file=file_path.name,
                        line=stmt.lineno,
                        function=function_name,
                        code=code,
                        variable=list(rhs_vars & tracked_vars)[0],
                        operation="assignment",
                        dependencies=list(rhs_vars & tracked_vars),
                    )
                )

                # Track the new variable being assigned
                if target_name:
                    tracked_vars.add(target_name)

            # Also check if the target is a tracked variable (being redefined)
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id in tracked_vars:
                    # Track dependencies
                    dependencies = list(self._get_names_from_expr(stmt.value))
                    tracked_vars.update(dependencies)

        # Handle function calls with tracked variables as arguments
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            arg_vars = set()
            for arg in stmt.value.args:
                arg_vars.update(self._get_names_from_expr(arg))

            if arg_vars & tracked_vars:
                code = source_lines[stmt.lineno - 1] if stmt.lineno <= len(source_lines) else ""
                func_name = self._get_func_name(stmt.value.func)

                relevant_vars = arg_vars & tracked_vars
                self.nodes.append(
                    SliceNode(
                        file=file_path.name,
                        line=stmt.lineno,
                        function=function_name,
                        code=code,
                        variable=list(relevant_vars)[0] if relevant_vars else "",
                        operation=f"passed to {func_name}()",
                        dependencies=list(relevant_vars),
                    )
                )

        # Recursively handle compound statements
        for child in ast.walk(stmt):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id in tracked_vars:
                        dependencies = list(self._get_names_from_expr(child.value))
                        tracked_vars.update(dependencies)


class Slicer:
    """Main slicer class for analyzing Python code dataflow."""

    def __init__(self, root_path: str = ".", enable_cross_file: bool = True):
        """Initialize the slicer.

        Args:
            root_path: Root directory of the project to analyze.
            enable_cross_file: Whether to enable cross-file analysis (default: True).
        """
        self.root_path = Path(root_path)
        self.enable_cross_file = enable_cross_file
        self.import_resolver = ImportResolver(self.root_path) if enable_cross_file else None
        self.function_defs: dict[str, ast.FunctionDef] = {}  # Cache of function definitions

    def _find_function_definitions(self, tree: ast.AST) -> dict[str, ast.FunctionDef]:
        """Find all function definitions in the AST.

        Args:
            tree: The AST to search

        Returns:
            Dictionary mapping function names to their FunctionDef nodes
        """
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = node
        return functions

    def slice(
        self,
        file_path: str,
        line: int,
        variable: str,
        direction: SliceDirection = SliceDirection.BOTH,
    ) -> SliceResult:
        """Perform slicing on a variable.

        Args:
            file_path: Path to the Python file to analyze.
            line: Line number where the variable appears.
            variable: Name of the variable to slice.
            direction: Direction of slicing (BACKWARD, FORWARD, or BOTH).

        Returns:
            SliceResult containing the backward and/or forward slices.
        """
        # Resolve file path
        full_path = self.root_path / file_path
        if not full_path.exists():
            full_path = Path(file_path)

        with open(full_path) as f:
            source = f.read()

        source_lines = source.split("\n")
        tree = ast.parse(source, filename=str(full_path))

        # Find all function definitions in the file for inter-procedural analysis
        self.function_defs = self._find_function_definitions(tree)

        # Parse imports if cross-file analysis is enabled
        imports = {}
        if self.import_resolver:
            imports = self.import_resolver.parse_imports(tree, full_path)

        result = SliceResult(
            target_file=Path(file_path).name,
            target_line=line,
            target_variable=variable,
        )

        if direction in (SliceDirection.BACKWARD, SliceDirection.BOTH):
            # Multi-pass backward slicing to find transitive dependencies
            # This is necessary because dependencies may be defined before they're discovered
            all_nodes = []
            seen_keys = set()
            relevant_vars = {variable}

            max_passes = 10  # Safety limit to prevent infinite loops
            for pass_num in range(max_passes):
                backward_visitor = SlicerVisitor(
                    variable,
                    line,
                    SliceDirection.BACKWARD,
                    source_lines,
                    current_file=Path(file_path).name,
                    imports=imports,
                    import_resolver=self.import_resolver,
                    function_defs=self.function_defs,
                )
                # Start with accumulated relevant vars from previous passes
                backward_visitor.relevant_vars = relevant_vars.copy()
                backward_visitor.visit(tree)

                # Add new nodes (avoiding duplicates)
                for node in backward_visitor.nodes:
                    key = (node.file, node.line, node.variable, node.operation)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_nodes.append(node)

                # Check if we found any new variables
                new_vars = backward_visitor.relevant_vars - relevant_vars
                if not new_vars and pass_num > 0:
                    # No new variables discovered after first pass, we're done
                    break

                # Update relevant vars for next pass
                relevant_vars = backward_visitor.relevant_vars.copy()

            # Don't overwrite file names - preserve cross-file information
            result.backward_slice = sorted(all_nodes, key=lambda n: (n.file, n.line))

        if direction in (SliceDirection.FORWARD, SliceDirection.BOTH):
            forward_visitor = SlicerVisitor(
                variable,
                line,
                SliceDirection.FORWARD,
                source_lines,
                current_file=Path(file_path).name,
                imports=imports,
                import_resolver=self.import_resolver,
                function_defs=self.function_defs,
            )
            forward_visitor.visit(tree)
            # For forward slicing, sort by (current_file first, then line, then other files)
            # This ensures cross-file nodes appear after their call sites
            target_file = Path(file_path).name

            def sort_key(node: SliceNode) -> tuple[int, int, int]:
                # Nodes from target file come first (sorted by line)
                # Nodes from other files come after (in insertion order)
                if node.file == target_file:
                    return (0, node.line, 0)
                else:
                    # Use original index for cross-file nodes to preserve insertion order
                    return (1, forward_visitor.nodes.index(node), 0)
            result.forward_slice = sorted(forward_visitor.nodes, key=sort_key)

        return result
