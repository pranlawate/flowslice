#!/usr/bin/env python3
"""
flowslice - Dataflow Slicing for Python (Proof of Concept)

Given a variable at a specific line, trace:
- Where it came from (backward slice)
- Where it goes (forward slice)

Shows function names, not just line numbers.
"""

import ast
import sys
from pathlib import Path
from typing import Set, List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class SliceNode:
    """Represents a single node in the slice."""
    file: str
    line: int
    function: str
    code: str
    variable: str
    operation: str
    dependencies: List[str] = field(default_factory=list)
    context: Optional[str] = None


@dataclass
class SliceResult:
    """Result of slicing operation."""
    target_file: str
    target_line: int
    target_variable: str
    backward_slice: List[SliceNode] = field(default_factory=list)
    forward_slice: List[SliceNode] = field(default_factory=list)

    def as_tree(self, direction='both') -> str:
        """Format as a tree structure."""
        output = []
        output.append("╔" + "═" * 70 + "╗")
        output.append(f"║  BIDIRECTIONAL SLICE: {self.target_variable} @ {self.target_file}:{self.target_line}".ljust(71) + "║")
        output.append("╚" + "═" * 70 + "╝")
        output.append("")

        if direction in ('backward', 'both') and self.backward_slice:
            output.append("⬅️  BACKWARD SLICE (How did we get here?)")
            output.append("─" * 72)
            output.append("")

            # Group by function
            by_function = defaultdict(list)
            for node in self.backward_slice:
                by_function[f"{node.file}:{node.function}"].append(node)

            for func_key, nodes in by_function.items():
                file, func = func_key.split(':', 1)
                output.append(f"  📁 {file} → {func}()")
                for node in sorted(nodes, key=lambda n: n.line):
                    output.append(f"    ├─ Line {node.line}: {node.code.strip()}")
                    if node.dependencies:
                        output.append(f"    │  └─ depends on: {', '.join(node.dependencies)}")
                    if node.context:
                        output.append(f"    │  └─ context: {node.context}")
                output.append("")

        if direction in ('forward', 'both') and self.forward_slice:
            output.append("➡️  FORWARD SLICE (Where does it go?)")
            output.append("─" * 72)
            output.append("")

            # Group by function
            by_function = defaultdict(list)
            for node in self.forward_slice:
                by_function[f"{node.file}:{node.function}"].append(node)

            for func_key, nodes in by_function.items():
                file, func = func_key.split(':', 1)
                output.append(f"  📁 {file} → {func}()")
                for node in sorted(nodes, key=lambda n: n.line):
                    marker = " ⭐ TARGET" if node.line == self.target_line else ""
                    output.append(f"    ├─ Line {node.line}: {node.code.strip()}{marker}")
                    if node.dependencies:
                        output.append(f"    │  └─ affects: {', '.join(node.dependencies)}")
                    if node.operation:
                        output.append(f"    │  └─ operation: {node.operation}")
                output.append("")

        # Statistics
        all_files = set(n.file for n in self.backward_slice + self.forward_slice)
        all_functions = set(n.function for n in self.backward_slice + self.forward_slice)
        output.append("📊 STATISTICS:")
        output.append(f"   - Total lines in slice: {len(self.backward_slice) + len(self.forward_slice)}")
        output.append(f"   - Files involved: {len(all_files)} ({', '.join(sorted(all_files))})")
        output.append(f"   - Functions involved: {len(all_functions)} ({', '.join(sorted(all_functions))})")

        return "\n".join(output)


class EnhancedSlicer(ast.NodeVisitor):
    """Enhanced slicer with function tracking."""

    def __init__(self, target_var: str, target_line: int, direction: str, source_lines: List[str]):
        self.target_var = target_var
        self.target_line = target_line
        self.direction = direction
        self.source_lines = source_lines

        self.nodes: List[SliceNode] = []
        self.current_function = "<module>"
        self.function_stack = ["<module>"]
        self.started = False

        if direction == 'backward':
            self.relevant_vars: Set[str] = {target_var}
        else:  # forward
            self.affected_vars: Set[str] = {target_var}

    def visit_FunctionDef(self, node):
        """Track function context."""
        self.function_stack.append(node.name)
        self.current_function = node.name

        # Check parameters
        if self.direction == 'backward':
            for arg in node.args.args:
                if arg.arg in self.relevant_vars:
                    self.nodes.append(SliceNode(
                        file="<current>",
                        line=node.lineno,
                        function=self.current_function,
                        code=f"def {node.name}(..., {arg.arg}, ...)",
                        variable=arg.arg,
                        operation="parameter",
                        dependencies=[]
                    ))

        self.generic_visit(node)
        self.function_stack.pop()
        self.current_function = self.function_stack[-1] if self.function_stack else "<module>"

    def visit_Assign(self, node):
        """Track assignments."""
        if self.direction == 'backward':
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in self.relevant_vars:
                    rhs_vars = self._get_names_from_expr(node.value)
                    code = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""

                    self.nodes.append(SliceNode(
                        file="<current>",
                        line=node.lineno,
                        function=self.current_function,
                        code=code,
                        variable=target.id,
                        operation="assignment",
                        dependencies=list(rhs_vars)
                    ))

                    # Add RHS vars to relevant set
                    self.relevant_vars.update(rhs_vars)

        else:  # forward
            if not self.started and node.lineno >= self.target_line:
                self.started = True

            if self.started:
                rhs_vars = self._get_names_from_expr(node.value)
                if rhs_vars & self.affected_vars:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            code = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
                            self.nodes.append(SliceNode(
                                file="<current>",
                                line=node.lineno,
                                function=self.current_function,
                                code=code,
                                variable=target.id,
                                operation="assignment",
                                dependencies=list(rhs_vars & self.affected_vars)
                            ))
                            self.affected_vars.add(target.id)

        self.generic_visit(node)

    def visit_Expr(self, node):
        """Track method calls like list.append()."""
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            obj = self._get_base_name(node.value.func.value)
            method = node.value.func.attr

            if self.direction == 'backward':
                if obj in self.relevant_vars:
                    args = [self._get_names_from_expr(arg) for arg in node.value.args]
                    all_args = set()
                    for arg_set in args:
                        all_args.update(arg_set)

                    code = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
                    self.nodes.append(SliceNode(
                        file="<current>",
                        line=node.lineno,
                        function=self.current_function,
                        code=code,
                        variable=obj,
                        operation=f".{method}()",
                        dependencies=list(all_args)
                    ))
                    self.relevant_vars.update(all_args)

            else:  # forward
                if self.started and obj in self.affected_vars:
                    code = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
                    self.nodes.append(SliceNode(
                        file="<current>",
                        line=node.lineno,
                        function=self.current_function,
                        code=code,
                        variable=obj,
                        operation=f".{method}()",
                        dependencies=[]
                    ))

        self.generic_visit(node)

    def visit_For(self, node):
        """Track for loops."""
        if self.direction == 'backward':
            if isinstance(node.target, ast.Name) and node.target.id in self.relevant_vars:
                iter_vars = self._get_names_from_expr(node.iter)
                code = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""

                self.nodes.append(SliceNode(
                    file="<current>",
                    line=node.lineno,
                    function=self.current_function,
                    code=code,
                    variable=node.target.id,
                    operation="for loop",
                    dependencies=list(iter_vars),
                    context=f"iterates over {iter_vars}"
                ))
                self.relevant_vars.update(iter_vars)

        else:  # forward
            if self.started:
                iter_vars = self._get_names_from_expr(node.iter)
                if iter_vars & self.affected_vars:
                    code = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
                    if isinstance(node.target, ast.Name):
                        self.nodes.append(SliceNode(
                            file="<current>",
                            line=node.lineno,
                            function=self.current_function,
                            code=code,
                            variable=node.target.id,
                            operation="for loop",
                            dependencies=list(iter_vars & self.affected_vars),
                            context=f"iterates over {iter_vars & self.affected_vars}"
                        ))
                        self.affected_vars.add(node.target.id)

        self.generic_visit(node)

    def visit_Call(self, node):
        """Track function calls."""
        if self.started or self.direction == 'backward':
            # Check arguments
            for arg in node.args:
                arg_vars = self._get_names_from_expr(arg)
                if self.direction == 'backward':
                    check_set = self.relevant_vars
                else:
                    check_set = self.affected_vars if self.started else set()

                if arg_vars & check_set and hasattr(node, 'lineno'):
                    code = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
                    func_name = self._get_func_name(node.func)
                    self.nodes.append(SliceNode(
                        file="<current>",
                        line=node.lineno,
                        function=self.current_function,
                        code=code,
                        variable=list(arg_vars & check_set)[0],
                        operation=f"passed to {func_name}()",
                        dependencies=list(arg_vars & check_set)
                    ))

        self.generic_visit(node)

    def _get_func_name(self, node) -> str:
        """Get function name from call."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        return "<unknown>"

    def _get_names_from_expr(self, expr) -> Set[str]:
        """Extract all variable names from an expression."""
        names = set()

        class NameCollector(ast.NodeVisitor):
            def visit_Name(self, node):
                names.add(node.id)

        NameCollector().visit(expr)
        return names

    def _get_base_name(self, node) -> str:
        """Get the base variable name from an attribute chain."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_base_name(node.value)
        return ""


def slice_variable(file_path: str, variable: str, line: int, direction: str = 'both') -> SliceResult:
    """Perform slicing on a variable."""

    with open(file_path, 'r') as f:
        source = f.read()

    source_lines = source.split('\n')
    tree = ast.parse(source, filename=file_path)

    result = SliceResult(
        target_file=Path(file_path).name,
        target_line=line,
        target_variable=variable
    )

    if direction in ('backward', 'both'):
        backward_slicer = EnhancedSlicer(variable, line, 'backward', source_lines)
        backward_slicer.visit(tree)
        for node in backward_slicer.nodes:
            node.file = result.target_file
        result.backward_slice = sorted(backward_slicer.nodes, key=lambda n: n.line)

    if direction in ('forward', 'both'):
        forward_slicer = EnhancedSlicer(variable, line, 'forward', source_lines)
        forward_slicer.visit(tree)
        for node in forward_slicer.nodes:
            node.file = result.target_file
        result.forward_slice = sorted(forward_slicer.nodes, key=lambda n: n.line)

    return result


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("flowslice - Dataflow Slicing for Python")
        print("\nUsage:")
        print("  flowslice <file>:<line>:<variable> [direction]")
        print("\nExample:")
        print("  flowslice main.py:1251:skipped both")
        print("  flowslice main.py:1251:skipped backward")
        print("  flowslice main.py:1251:skipped forward")
        sys.exit(1)

    # Parse input
    criterion = sys.argv[1]
    direction = sys.argv[2] if len(sys.argv) > 2 else 'both'

    try:
        file_path, line_str, variable = criterion.split(':')
        line = int(line_str)
    except ValueError:
        print("Error: Invalid format. Use <file>:<line>:<variable>")
        sys.exit(1)

    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)

    # Perform slicing
    result = slice_variable(file_path, variable, line, direction)

    # Print result
    print(result.as_tree(direction))


if __name__ == "__main__":
    main()
