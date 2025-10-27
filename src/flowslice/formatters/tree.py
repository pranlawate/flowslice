"""Tree formatter for flowslice results."""

from collections import defaultdict

from flowslice.core.models import SliceDirection, SliceNode, SliceResult


class TreeFormatter:
    """Format slice results as a tree structure."""

    @staticmethod
    def _merge_nodes_by_line(nodes: list[SliceNode]) -> dict[int, SliceNode]:
        """Merge multiple nodes from the same line into one.

        When the same line appears multiple times (e.g., assignment + function call),
        merge them into a single node with combined dependencies and operations.

        Args:
            nodes: List of SliceNodes to merge.

        Returns:
            Dictionary mapping line number to merged SliceNode.
        """
        merged: dict[int, SliceNode] = {}

        for node in nodes:
            if node.line not in merged:
                merged[node.line] = node
            else:
                # Merge dependencies
                existing = merged[node.line]
                all_deps = set(existing.dependencies) | set(node.dependencies)
                existing.dependencies = sorted(list(all_deps))

                # Merge operations (keep first operation, note if there are more)
                if node.operation and node.operation != existing.operation:
                    if not existing.context:
                        existing.context = f"Also: {node.operation}"
                    else:
                        existing.context += f", {node.operation}"

        return merged

    @staticmethod
    def format(result: SliceResult, direction: SliceDirection = SliceDirection.BOTH) -> str:
        """Format a SliceResult as a tree structure.

        Args:
            result: The SliceResult to format.
            direction: Which direction(s) to display.

        Returns:
            Formatted tree as a string.
        """
        output = []
        output.append("╔" + "═" * 70 + "╗")
        output.append(
            f"║  BIDIRECTIONAL SLICE: {result.target_variable} @ "
            f"{result.target_file}:{result.target_line}".ljust(71) + "║"
        )
        output.append("╚" + "═" * 70 + "╝")
        output.append("")

        if direction in (SliceDirection.BACKWARD, SliceDirection.BOTH) and result.backward_slice:
            output.append("⬅️  BACKWARD SLICE (How did we get here?)")
            output.append("─" * 72)
            output.append("")

            # Group by function
            by_function: dict[str, list[SliceNode]] = defaultdict(list)
            for node in result.backward_slice:
                by_function[f"{node.file}:{node.function}"].append(node)

            for func_key, nodes in by_function.items():
                file, func = func_key.split(":", 1)
                output.append(f"  📁 {file} → {func}()")

                # Merge nodes from same line to avoid duplication
                merged_nodes = TreeFormatter._merge_nodes_by_line(nodes)

                for line_num in sorted(merged_nodes.keys()):
                    node = merged_nodes[line_num]
                    marker = " ⭐ TARGET" if node.line == result.target_line else ""
                    output.append(f"    ├─ Line {node.line}: {node.code.strip()}{marker}")
                    if node.dependencies:
                        output.append(
                            f"    │  └─ depends on: {', '.join(node.dependencies)}"
                        )
                    if node.context:
                        output.append(f"    │  └─ {node.context}")
                output.append("")

        if direction in (SliceDirection.FORWARD, SliceDirection.BOTH) and result.forward_slice:
            output.append("➡️  FORWARD SLICE (Where does it go?)")
            output.append("─" * 72)
            output.append("")

            # Group by function
            by_function = defaultdict(list)
            for node in result.forward_slice:
                by_function[f"{node.file}:{node.function}"].append(node)

            for func_key, nodes in by_function.items():
                file, func = func_key.split(":", 1)
                output.append(f"  📁 {file} → {func}()")

                # Merge nodes from same line to avoid duplication
                merged_nodes = TreeFormatter._merge_nodes_by_line(nodes)

                for line_num in sorted(merged_nodes.keys()):
                    node = merged_nodes[line_num]
                    marker = " ⭐ TARGET" if node.line == result.target_line else ""
                    output.append(f"    ├─ Line {node.line}: {node.code.strip()}{marker}")
                    if node.dependencies:
                        output.append(
                            f"    │  └─ affects: {', '.join(node.dependencies)}"
                        )
                    if node.operation:
                        output.append(f"    │  └─ operation: {node.operation}")
                    if node.context:
                        output.append(f"    │  └─ {node.context}")
                output.append("")

        # Statistics
        all_files = set(n.file for n in result.backward_slice + result.forward_slice)
        all_functions = set(
            n.function for n in result.backward_slice + result.forward_slice
        )
        output.append("📊 STATISTICS:")
        output.append(
            f"   - Total lines in slice: {len(result.backward_slice) + len(result.forward_slice)}"
        )
        output.append(
            f"   - Files involved: {len(all_files)} ({', '.join(sorted(all_files))})"
        )
        output.append(
            f"   - Functions involved: {len(all_functions)} ({', '.join(sorted(all_functions))})"
        )

        return "\n".join(output)
