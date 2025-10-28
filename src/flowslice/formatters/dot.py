"""DOT/Graphviz formatter for graph visualization."""

from flowslice.core.models import SliceDirection, SliceResult


class DotFormatter:
    """Format slice results as DOT graph for Graphviz visualization."""

    def format(self, result: SliceResult, direction: SliceDirection) -> str:
        """Format the slice result as a DOT graph.

        Args:
            result: The slice result to format
            direction: The slicing direction (used for labeling)

        Returns:
            DOT format string that can be rendered with Graphviz
        """
        lines = []
        lines.append("digraph dataflow {")
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box, style=filled, fillcolor=lightblue];")
        lines.append("")

        # Add target node
        target_id = f"{result.target_file}:{result.target_line}"
        target_label = f"{result.target_variable}\\n{result.target_file}:{result.target_line}"
        lines.append(f'  "{target_id}" [label="{target_label}", fillcolor=yellow, penwidth=3];')
        lines.append("")

        # Process backward slice (dependencies flow TO target)
        if result.backward_slice:
            lines.append("  // Backward dependencies")
            seen_nodes = {target_id}
            for node in result.backward_slice:
                node_id = f"{node.file}:{node.line}"
                if node_id not in seen_nodes:
                    label = self._escape_label(node.code[:50] if node.code else node.variable)
                    color = "lightgreen" if node.file != result.target_file else "lightblue"
                    node_label = f"{label}\\n{node.file}:{node.line}"
                    lines.append(f'  "{node_id}" [label="{node_label}", fillcolor={color}];')
                    seen_nodes.add(node_id)

                # Add edge from this node to target (or dependent nodes)
                if node.dependencies:
                    # This node depends on its dependencies
                    for dep in node.dependencies:
                        # Find nodes that define this dependency
                        for other in result.backward_slice:
                            if other.variable == dep and other.line < node.line:
                                dep_id = f"{other.file}:{other.line}"
                                lines.append(f'  "{dep_id}" -> "{node_id}";')
                                break

                # Connect to target if it's a direct dependency
                if node_id != target_id:
                    lines.append(f'  "{node_id}" -> "{target_id}" [style=dashed];')
            lines.append("")

        # Process forward slice (target flows TO these nodes)
        if result.forward_slice:
            lines.append("  // Forward dataflow")
            seen_nodes = {target_id}
            for node in result.forward_slice:
                node_id = f"{node.file}:{node.line}"
                if node_id not in seen_nodes:
                    label = self._escape_label(node.code[:50] if node.code else node.variable)
                    color = "lightcoral" if node.file != result.target_file else "lightblue"
                    node_label = f"{label}\\n{node.file}:{node.line}"
                    lines.append(f'  "{node_id}" [label="{node_label}", fillcolor={color}];')
                    seen_nodes.add(node_id)

                # Add edge from target to this node
                if node_id != target_id:
                    lines.append(f'  "{target_id}" -> "{node_id}";')
            lines.append("")

        lines.append("}")
        return "\n".join(lines)

    def _escape_label(self, text: str) -> str:
        """Escape special characters for DOT labels."""
        return text.replace('"', '\\"').replace('\n', '\\n').strip()
