"""Graph-based formatter showing convergence/divergence in dataflow."""

from flowslice.core.models import SliceDirection, SliceNode, SliceResult
from flowslice.formatters.colors import Colors, colorize


class GraphFormatter:
    """Format slices as grouped dependency graphs."""

    @staticmethod
    def _format_code_line(code: str, max_length: int = 100) -> str:
        """Format a code line for display, handling incomplete multi-line statements.

        Args:
            code: The code line to format
            max_length: Maximum length before truncating (default: 100)

        Returns:
            Formatted code with ellipsis for incomplete/long statements
        """
        code = code.strip()

        # Check if line ends with opening bracket/paren without closing
        has_unmatched_paren = code and code[-1] in "([{" and code.count("(") > code.count(")")
        has_unmatched_bracket = code and code[-1] in "([{" and code.count("[") > code.count("]")
        has_unmatched_brace = code and code[-1] in "([{" and code.count("{") > code.count("}")

        if has_unmatched_paren or has_unmatched_bracket or has_unmatched_brace:
            # Add continuation indicator
            code = code + "...)"

        # Truncate if too long
        if len(code) > max_length:
            code = code[:max_length - 3] + "..."

        return code

    @staticmethod
    def format(
        result: SliceResult,
        direction: SliceDirection = SliceDirection.BOTH,
    ) -> str:
        """Format a SliceResult showing graph structure with grouping.

        Args:
            result: The SliceResult to format.
            direction: Which slices to show (BACKWARD, FORWARD, or BOTH).

        Returns:
            Formatted string with grouped dependencies/uses.
        """
        output = []

        # Header
        output.append(colorize("╔" + "═" * 70 + "╗", Colors.CYAN))
        header_text = (
            f"  GRAPH VIEW: {result.target_variable} @ "
            f"{result.target_file}:{result.target_line}"
        )
        header_line = f"║{header_text}{' ' * (70 - len(header_text))}║"
        output.append(colorize(header_line, Colors.YELLOW, bold=True))
        output.append(colorize("╚" + "═" * 70 + "╝", Colors.CYAN))
        output.append("")

        if direction in (SliceDirection.BACKWARD, SliceDirection.BOTH):
            if result.backward_slice:
                output.append(GraphFormatter._format_backward_graph(result))
            else:
                output.append("⬅️  BACKWARD SLICE: No dependencies found")
                output.append("")

        if direction in (SliceDirection.FORWARD, SliceDirection.BOTH):
            if result.forward_slice:
                output.append(GraphFormatter._format_forward_graph(result))
            else:
                output.append("➡️  FORWARD SLICE: No uses found")
                output.append("")

        # Statistics
        output.append(colorize("📊 STATISTICS:", Colors.CYAN, bold=True))
        total_nodes = len(result.backward_slice) + len(result.forward_slice)
        output.append(
            colorize("   - Total nodes: ", Colors.WHITE)
            + colorize(str(total_nodes), Colors.YELLOW, bold=True)
        )

        backward_lines = len(set(n.line for n in result.backward_slice))
        forward_lines = len(set(n.line for n in result.forward_slice))
        stats_line = (
            colorize("   - Backward: ", Colors.WHITE)
            + colorize(f"{backward_lines}", Colors.GREEN, bold=True)
            + colorize(" lines, Forward: ", Colors.WHITE)
            + colorize(f"{forward_lines}", Colors.BLUE, bold=True)
            + colorize(" lines", Colors.WHITE)
        )
        output.append(stats_line)

        return "\n".join(output)

    @staticmethod
    def _format_backward_graph(result: SliceResult) -> str:
        """Format backward slice showing convergence."""
        output = []
        title = "⬅️  BACKWARD SLICE (How did we get here?)"
        output.append(colorize(title, Colors.GREEN, bold=True))
        output.append(colorize("─" * 72, Colors.BRIGHT_BLACK))
        output.append("")

        # Find the target node
        target_nodes = [n for n in result.backward_slice if n.line == result.target_line]

        if target_nodes:
            target = target_nodes[0]
            target_text = f"  🎯 TARGET: {result.target_variable} (Line {result.target_line})"
            output.append(colorize(target_text, Colors.YELLOW, bold=True))
            formatted_code = GraphFormatter._format_code_line(target.code)
            output.append(colorize(f"     └─ {formatted_code}", Colors.WHITE))
            output.append("")

            # Group dependencies
            if target.dependencies:
                deps_header = f"  📥 DIRECT DEPENDENCIES ({len(target.dependencies)}):"
                output.append(colorize(deps_header, Colors.CYAN, bold=True))
                output.append("")

                # Find nodes for each dependency
                dep_nodes: dict[str, list[SliceNode]] = {}
                for dep in target.dependencies:
                    # Find the node that defines this dependency
                    for node in result.backward_slice:
                        if node.variable == dep and node.line != result.target_line:
                            if dep not in dep_nodes:
                                dep_nodes[dep] = []
                            dep_nodes[dep].append(node)

                # Display each dependency
                for i, dep in enumerate(target.dependencies):
                    is_last = i == len(target.dependencies) - 1
                    prefix = "     └─" if is_last else "     ├─"

                    if dep in dep_nodes and dep_nodes[dep]:
                        node = dep_nodes[dep][0]
                        # Indicate if cross-file
                        is_cross_file = node.file != result.target_file
                        file_indicator = " 🔗" if is_cross_file else ""
                        dep_color = Colors.MAGENTA if is_cross_file else Colors.GREEN

                        dep_line = f"{prefix} {dep} (Line {node.line}){file_indicator}"
                        output.append(colorize(dep_line, dep_color, bold=is_cross_file))
                        indent = "  " if is_last else "│ "
                        formatted_code = GraphFormatter._format_code_line(node.code)
                        code_line = f"     {indent}   {formatted_code}"
                        output.append(colorize(code_line, Colors.BRIGHT_BLACK))
                        if node.dependencies:
                            deps_str = ", ".join(node.dependencies)
                            deps_line = f"     {indent}   └─ depends on: {deps_str}"
                            output.append(colorize(deps_line, Colors.BRIGHT_BLACK))
                    else:
                        # External or not found
                        ext_line = f"{prefix} {dep} (external or parameter)"
                        output.append(colorize(ext_line, Colors.BRIGHT_BLACK))

                    if not is_last:
                        output.append(colorize("     │", Colors.BRIGHT_BLACK))

        output.append("")
        return "\n".join(output)

    @staticmethod
    def _format_forward_graph(result: SliceResult) -> str:
        """Format forward slice showing divergence."""
        output = []
        title = "➡️  FORWARD SLICE (Where does it go?)"
        output.append(colorize(title, Colors.BLUE, bold=True))
        output.append(colorize("─" * 72, Colors.BRIGHT_BLACK))
        output.append("")

        # Group nodes by type
        assignments = []
        function_calls = []
        other_uses = []

        for node in result.forward_slice:
            if node.line == result.target_line:
                continue  # Skip the target itself

            if node.operation == "assignment":
                assignments.append(node)
            elif "passed to" in node.operation:
                function_calls.append(node)
            else:
                other_uses.append(node)

        source_text = f"  🎯 SOURCE: {result.target_variable} (Line {result.target_line})"
        output.append(colorize(source_text, Colors.YELLOW, bold=True))
        output.append("")

        # Show divergence to derived variables
        if assignments:
            header = f"  🌿 DERIVED VARIABLES ({len(assignments)}):"
            output.append(colorize(header, Colors.CYAN, bold=True))
            desc = "     Variables that receive data from the source"
            output.append(colorize(desc, Colors.BRIGHT_BLACK))
            output.append("")

            for i, node in enumerate(assignments):
                is_last = i == len(assignments) - 1
                prefix = "     └─" if is_last else "     ├─"

                # Indicate if cross-file
                is_cross_file = node.file != result.target_file
                file_indicator = " 🔗" if is_cross_file else ""
                var_color = Colors.MAGENTA if is_cross_file else Colors.BLUE

                var_line = f"{prefix} {node.variable} (Line {node.line}){file_indicator}"
                output.append(colorize(var_line, var_color, bold=is_cross_file))
                indent = "  " if is_last else "│ "
                code_line = f"     {indent}   {node.code.strip()}"
                output.append(colorize(code_line, Colors.BRIGHT_BLACK))
                if node.dependencies:
                    deps_str = ", ".join(node.dependencies)
                    deps_line = f"     {indent}   └─ uses: {deps_str}"
                    output.append(colorize(deps_line, Colors.BRIGHT_BLACK))
                if not is_last:
                    output.append(colorize("     │", Colors.BRIGHT_BLACK))
            output.append("")

        # Show function calls
        if function_calls:
            # Group by unique calls (de-duplicate)
            unique_calls = {}
            for node in function_calls:
                key = (node.line, node.operation)
                if key not in unique_calls:
                    unique_calls[key] = node

            header = f"  📤 PASSED TO FUNCTIONS ({len(unique_calls)}):"
            output.append(colorize(header, Colors.CYAN, bold=True))
            output.append("")

            for i, (_, node) in enumerate(sorted(unique_calls.items())):
                is_last = i == len(unique_calls) - 1
                prefix = "     └─" if is_last else "     ├─"

                # Indicate if cross-file
                is_cross_file = node.file != result.target_file
                file_indicator = " 🔗" if is_cross_file else ""
                func_color = Colors.MAGENTA if is_cross_file else Colors.BLUE

                # Extract function name from operation
                func_name = node.operation.replace("passed to ", "")
                func_line = f"{prefix} {func_name} (Line {node.line}){file_indicator}"
                output.append(colorize(func_line, func_color, bold=is_cross_file))
                indent = "  " if is_last else "│ "
                code_line = f"     {indent}   {node.code.strip()}"
                output.append(colorize(code_line, Colors.BRIGHT_BLACK))
                if not is_last:
                    output.append(colorize("     │", Colors.BRIGHT_BLACK))

            output.append("")

        # Show other uses
        if other_uses:
            header = f"  🔧 OTHER USES ({len(other_uses)}):"
            output.append(colorize(header, Colors.CYAN, bold=True))
            output.append("")

            for i, node in enumerate(other_uses):
                is_last = i == len(other_uses) - 1
                prefix = "     └─" if is_last else "     ├─"

                # Indicate if cross-file
                is_cross_file = node.file != result.target_file
                file_indicator = " 🔗" if is_cross_file else ""
                use_color = Colors.MAGENTA if is_cross_file else Colors.BLUE

                use_line = f"{prefix} Line {node.line}: {node.operation}{file_indicator}"
                output.append(colorize(use_line, use_color, bold=is_cross_file))
                indent = "  " if is_last else "│ "
                code_line = f"     {indent}   {node.code.strip()}"
                output.append(colorize(code_line, Colors.BRIGHT_BLACK))
                if not is_last:
                    output.append(colorize("     │", Colors.BRIGHT_BLACK))

            output.append("")

        return "\n".join(output)
