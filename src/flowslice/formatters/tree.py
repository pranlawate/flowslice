"""Tree formatter for flowslice results."""


from flowslice.core.models import SliceDirection, SliceNode, SliceResult
from flowslice.formatters.colors import Colors, colorize


class TreeFormatter:
    """Format slice results as a tree structure."""

    @staticmethod
    def _merge_nodes_by_line(nodes: list[SliceNode]) -> list[SliceNode]:
        """Merge multiple nodes from the same line into one.

        When the same line appears multiple times (e.g., assignment + function call),
        merge them into a single node with combined dependencies and operations.
        Preserves original order of first occurrence.

        Args:
            nodes: List of SliceNodes to merge.

        Returns:
            List of merged SliceNodes in original order.
        """
        seen_lines: dict[tuple[str, int], int] = {}  # (file, line) -> index
        merged: list[SliceNode] = []

        for node in nodes:
            key = (node.file, node.line)
            if key not in seen_lines:
                seen_lines[key] = len(merged)
                merged.append(node)
            else:
                # Merge dependencies
                idx = seen_lines[key]
                existing = merged[idx]
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
        header_text = f"BIDIRECTIONAL SLICE: {result.target_variable} @ "
        header_text += f"{result.target_file}:{result.target_line}"
        output.append(colorize("╔" + "═" * 70 + "╗", Colors.CYAN))
        output.append(
            colorize("║  ", Colors.CYAN)
            + colorize(header_text.ljust(68), Colors.YELLOW, bold=True)
            + colorize("  ║", Colors.CYAN)
        )
        output.append(colorize("╚" + "═" * 70 + "╝", Colors.CYAN))
        output.append("")

        if direction in (SliceDirection.BACKWARD, SliceDirection.BOTH) and result.backward_slice:
            title = "⬅️  BACKWARD SLICE (How did we get here?)"
            output.append(colorize(title, Colors.GREEN, bold=True))
            output.append(colorize("─" * 72, Colors.BRIGHT_BLACK))
            output.append("")

            # Merge duplicate lines and sort chronologically
            merged_nodes = TreeFormatter._merge_nodes_by_line(result.backward_slice)
            sorted_nodes = sorted(merged_nodes, key=lambda n: (n.file, n.line))

            # Track current file for cross-file indicators
            current_file = None
            current_function = None

            for node in sorted_nodes:
                # Show file/function header when it changes
                if node.file != current_file or node.function != current_function:
                    if current_file is not None:
                        output.append("")  # Blank line between functions

                    # Indicate if this is cross-file
                    is_cross_file = node.file != result.target_file
                    file_indicator = "🔗" if is_cross_file else "📁"
                    file_color = Colors.MAGENTA if is_cross_file else Colors.BLUE

                    func_line = f"  {file_indicator} {node.file} → {node.function}()"
                    output.append(colorize(func_line, file_color, bold=is_cross_file))
                    current_file = node.file
                    current_function = node.function

                # Show the node
                is_target = node.line == result.target_line
                marker = colorize(" ⭐ TARGET", Colors.YELLOW, bold=True) if is_target else ""

                line_color = Colors.YELLOW if is_target else Colors.WHITE
                line_text = f"    ├─ Line {node.line}: {node.code.strip()}"
                output.append(colorize(line_text, line_color) + marker)

                if node.dependencies:
                    deps_text = f"    │  └─ depends on: {', '.join(node.dependencies)}"
                    output.append(colorize(deps_text, Colors.BRIGHT_BLACK))

                if node.context and "Also:" not in node.context:
                    context_text = f"    │  └─ {node.context}"
                    output.append(colorize(context_text, Colors.BRIGHT_BLACK))

            output.append("")

        if direction in (SliceDirection.FORWARD, SliceDirection.BOTH) and result.forward_slice:
            title = "➡️  FORWARD SLICE (Where does it go?)"
            output.append(colorize(title, Colors.BLUE, bold=True))
            output.append(colorize("─" * 72, Colors.BRIGHT_BLACK))
            output.append("")

            # Forward slice is already sorted chronologically by the slicer
            # Merge nodes from same line to avoid duplication (preserves order)
            merged_nodes = TreeFormatter._merge_nodes_by_line(result.forward_slice)

            # Track current file for cross-file indicators
            current_file = None
            current_function = None

            for node in merged_nodes:
                # Show file/function header when it changes
                if node.file != current_file or node.function != current_function:
                    if current_file is not None:
                        output.append("")  # Blank line between functions

                    # Indicate if this is cross-file
                    is_cross_file = node.file != result.target_file
                    file_indicator = "🔗" if is_cross_file else "📁"
                    file_color = Colors.MAGENTA if is_cross_file else Colors.BLUE

                    func_line = f"  {file_indicator} {node.file} → {node.function}()"
                    output.append(colorize(func_line, file_color, bold=is_cross_file))
                    current_file = node.file
                    current_function = node.function

                # Show the node
                is_target = node.line == result.target_line
                marker = colorize(" ⭐ TARGET", Colors.YELLOW, bold=True) if is_target else ""

                line_color = Colors.YELLOW if is_target else Colors.WHITE
                line_text = f"    ├─ Line {node.line}: {node.code.strip()}"
                output.append(colorize(line_text, line_color) + marker)

                if node.dependencies:
                    deps_text = f"    │  └─ affects: {', '.join(node.dependencies)}"
                    output.append(colorize(deps_text, Colors.BRIGHT_BLACK))

                if node.operation and "passed to" not in node.operation:
                    op_text = f"    │  └─ operation: {node.operation}"
                    output.append(colorize(op_text, Colors.BRIGHT_BLACK))

                if node.context and "Also:" not in node.context:
                    context_text = f"    │  └─ {node.context}"
                    output.append(colorize(context_text, Colors.BRIGHT_BLACK))

            output.append("")

        # Statistics
        all_files = set(n.file for n in result.backward_slice + result.forward_slice)
        all_functions = set(
            n.function for n in result.backward_slice + result.forward_slice
        )
        output.append(colorize("📊 STATISTICS:", Colors.CYAN, bold=True))
        total_lines = len(result.backward_slice) + len(result.forward_slice)
        output.append(
            colorize("   - Total lines in slice: ", Colors.WHITE)
            + colorize(str(total_lines), Colors.YELLOW, bold=True)
        )
        output.append(
            colorize("   - Files involved: ", Colors.WHITE)
            + colorize(str(len(all_files)), Colors.YELLOW, bold=True)
            + colorize(f" ({', '.join(sorted(all_files))})", Colors.BRIGHT_BLACK)
        )
        output.append(
            colorize("   - Functions involved: ", Colors.WHITE)
            + colorize(str(len(all_functions)), Colors.YELLOW, bold=True)
            + colorize(f" ({', '.join(sorted(all_functions))})", Colors.BRIGHT_BLACK)
        )

        return "\n".join(output)
