"""Graph-based formatter showing convergence/divergence in dataflow."""

from flowslice.core.models import SliceDirection, SliceNode, SliceResult


class GraphFormatter:
    """Format slices as grouped dependency graphs."""

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
        output.append("╔" + "═" * 70 + "╗")
        header_text = (
            f"  GRAPH VIEW: {result.target_variable} @ "
            f"{result.target_file}:{result.target_line}"
        )
        output.append(f"║{header_text}{' ' * (70 - len(header_text))}║")
        output.append("╚" + "═" * 70 + "╝")
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
        output.append("📊 STATISTICS:")
        total_nodes = len(result.backward_slice) + len(result.forward_slice)
        output.append(f"   - Total nodes: {total_nodes}")

        backward_lines = len(set(n.line for n in result.backward_slice))
        forward_lines = len(set(n.line for n in result.forward_slice))
        output.append(f"   - Backward: {backward_lines} lines, Forward: {forward_lines} lines")

        return "\n".join(output)

    @staticmethod
    def _format_backward_graph(result: SliceResult) -> str:
        """Format backward slice showing convergence."""
        output = []
        output.append("⬅️  BACKWARD SLICE (How did we get here?)")
        output.append("─" * 72)
        output.append("")

        # Find the target node
        target_nodes = [n for n in result.backward_slice if n.line == result.target_line]

        if target_nodes:
            target = target_nodes[0]
            output.append(f"  🎯 TARGET: {result.target_variable} (Line {result.target_line})")
            output.append(f"     └─ {target.code.strip()}")
            output.append("")

            # Group dependencies
            if target.dependencies:
                output.append(f"  📥 DIRECT DEPENDENCIES ({len(target.dependencies)}):")
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
                        output.append(f"{prefix} {dep} (Line {node.line})")
                        output.append(f"     {'  ' if is_last else '│ '}   {node.code.strip()}")
                        if node.dependencies:
                            deps_str = ", ".join(node.dependencies)
                            indent = "  " if is_last else "│ "
                            output.append(f"     {indent}   └─ depends on: {deps_str}")
                    else:
                        # External or not found
                        output.append(f"{prefix} {dep} (external or parameter)")

                    if not is_last:
                        output.append("     │")

        output.append("")
        return "\n".join(output)

    @staticmethod
    def _format_forward_graph(result: SliceResult) -> str:
        """Format forward slice showing divergence."""
        output = []
        output.append("➡️  FORWARD SLICE (Where does it go?)")
        output.append("─" * 72)
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

        output.append(f"  🎯 SOURCE: {result.target_variable} (Line {result.target_line})")
        output.append("")

        # Show divergence to derived variables
        if assignments:
            output.append(f"  🌿 DERIVED VARIABLES ({len(assignments)}):")
            output.append("     Variables that receive data from the source")
            output.append("")

            for i, node in enumerate(assignments):
                is_last = i == len(assignments) - 1
                prefix = "     └─" if is_last else "     ├─"
                output.append(f"{prefix} {node.variable} (Line {node.line})")
                output.append(f"     {'  ' if is_last else '│ '}   {node.code.strip()}")
                if node.dependencies:
                    deps_str = ", ".join(node.dependencies)
                    output.append(f"     {'  ' if is_last else '│ '}   └─ uses: {deps_str}")
                if not is_last:
                    output.append("     │")
            output.append("")

        # Show function calls
        if function_calls:
            # Group by unique calls (de-duplicate)
            unique_calls = {}
            for node in function_calls:
                key = (node.line, node.operation)
                if key not in unique_calls:
                    unique_calls[key] = node

            output.append(f"  📤 PASSED TO FUNCTIONS ({len(unique_calls)}):")
            output.append("")

            for i, (_, node) in enumerate(sorted(unique_calls.items())):
                is_last = i == len(unique_calls) - 1
                prefix = "     └─" if is_last else "     ├─"

                # Extract function name from operation
                func_name = node.operation.replace("passed to ", "")
                output.append(f"{prefix} {func_name} (Line {node.line})")
                output.append(f"     {'  ' if is_last else '│ '}   {node.code.strip()}")
                if not is_last:
                    output.append("     │")

            output.append("")

        # Show other uses
        if other_uses:
            output.append(f"  🔧 OTHER USES ({len(other_uses)}):")
            output.append("")

            for i, node in enumerate(other_uses):
                is_last = i == len(other_uses) - 1
                prefix = "     └─" if is_last else "     ├─"
                output.append(f"{prefix} Line {node.line}: {node.operation}")
                output.append(f"     {'  ' if is_last else '│ '}   {node.code.strip()}")
                if not is_last:
                    output.append("     │")

            output.append("")

        return "\n".join(output)
